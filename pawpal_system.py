"""PawPal+ logic layer.

Backend classes for the pet care planner: Task, Pet, Owner, and the Scheduler
that sorts, filters, detects conflicts, and builds a daily plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

# How each priority label ranks when sorting (higher = more important).
PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}


def _parse_hhmm(value: str) -> "int | None":
    """Convert an 'HH:MM' string to minutes past midnight, or None if blank/invalid."""
    if not value:
        return None
    try:
        hh, mm = value.split(":")
        return int(hh) * 60 + int(mm)
    except (ValueError, AttributeError):
        return None


def _to_hhmm(minutes: int) -> str:
    """Convert minutes past midnight to an 'HH:MM' string (wraps past 24h)."""
    hh, mm = divmod(minutes % (24 * 60), 60)
    return f"{hh:02d}:{mm:02d}"


@dataclass
class Task:
    """A single pet care task, e.g. a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    time: str = ""  # scheduled start time, "HH:MM" (blank = unscheduled)
    priority: str = "medium"  # "low" | "medium" | "high"
    category: str = "general"  # e.g. walk, feeding, meds, grooming
    frequency: str = "none"  # "none" | "daily" | "weekly"
    completed: bool = False
    due_date: date | None = None

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    @property
    def priority_rank(self) -> int:
        """Numeric rank for the task's priority (unknown labels rank lowest)."""
        return PRIORITY_RANK.get(self.priority, 0)

    def next_occurrence(self) -> "Task | None":
        """Return the next instance of a recurring task, or None if it doesn't repeat."""
        if self.frequency not in ("daily", "weekly"):
            return None
        base = self.due_date or date.today()
        step = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            time=self.time,
            priority=self.priority,
            category=self.category,
            frequency=self.frequency,
            completed=False,
            due_date=base + step,
        )


@dataclass
class Pet:
    """A pet that care tasks belong to."""

    name: str
    species: str
    breed: str = ""
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self.tasks.append(task)

    def complete_task(self, task: Task) -> "Task | None":
        """Mark a task complete; if it recurs, add and return the next occurrence."""
        task.mark_complete()
        nxt = task.next_occurrence()
        if nxt is not None:
            self.tasks.append(nxt)
        return nxt


@dataclass
class Owner:
    """The pet owner: manages pets and their daily time budget."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    available_minutes: int = 120
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The 'brain': sorts, filters, detects conflicts, and builds a daily plan."""

    def __init__(
        self, tasks: list[Task], available_minutes: int, owner: "Owner | None" = None
    ) -> None:
        self.tasks = tasks
        self.available_minutes = available_minutes
        self.owner = owner  # kept so we can filter by pet when available
        self.plan: list[Task] = []
        self.skipped: list[Task] = []

    @classmethod
    def for_owner(cls, owner: Owner) -> "Scheduler":
        """Build a scheduler from all of an owner's pets' tasks and time budget."""
        return cls(owner.all_tasks(), owner.available_minutes, owner=owner)

    @classmethod
    def for_pet(cls, owner: Owner, pet: Pet) -> "Scheduler":
        """Build a scheduler for a single pet, using the owner's time budget."""
        return cls(pet.tasks, owner.available_minutes, owner=owner)

    # --- sorting ------------------------------------------------------------
    def sort_tasks(self) -> list[Task]:
        """Order tasks by priority (high first), then shorter tasks first."""
        return sorted(self.tasks, key=lambda t: (-t.priority_rank, t.duration_minutes))

    def sort_by_time(self) -> list[Task]:
        """Order tasks by scheduled 'HH:MM' time; unscheduled tasks go last."""
        return sorted(self.tasks, key=lambda t: t.time or "99:99")

    # --- filtering ----------------------------------------------------------
    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return tasks matching the given completion status."""
        return [t for t in self.tasks if t.completed == completed]

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return tasks belonging to the named pet (needs an owner reference)."""
        if self.owner is None:
            return []
        return [t for pet in self.owner.pets if pet.name == pet_name for t in pet.tasks]

    # --- conflict detection -------------------------------------------------
    def find_conflicts(self) -> list[str]:
        """Return warnings for tasks that share the same scheduled time."""
        by_time: dict[str, list[str]] = {}
        for task in self.tasks:
            if task.time:
                by_time.setdefault(task.time, []).append(task.title)
        return [
            f"Conflict at {time}: {', '.join(titles)}"
            for time, titles in sorted(by_time.items())
            if len(titles) > 1
        ]

    # --- planning -----------------------------------------------------------
    def generate_plan(self) -> list[Task]:
        """Greedily pick the highest-priority *outstanding* tasks that fit the budget."""
        remaining = self.available_minutes
        self.plan = []
        self.skipped = []
        for task in self.sort_tasks():
            if task.completed:
                continue  # already done — don't spend today's budget on it
            if task.duration_minutes <= remaining:
                self.plan.append(task)
                remaining -= task.duration_minutes
            else:
                self.skipped.append(task)
        return self.plan

    def build_timeline(self, start: str = "08:00") -> "list[tuple[str, Task]]":
        """Assign clock times to the current plan.

        Tasks with a fixed ``time`` anchor at that time; the rest flow
        sequentially from ``start``, jumping past any fixed block so nothing
        overlaps. Returns (start_time, task) pairs sorted by start time.
        Call ``generate_plan()`` first to populate the plan.
        """
        fixed: list[tuple[int, Task]] = []
        flexible: list[Task] = []
        for task in self.plan:
            start_min = _parse_hhmm(task.time)
            if start_min is None:
                flexible.append(task)
            else:
                fixed.append((start_min, task))

        # Blocks the flexible tasks must not overlap.
        intervals = sorted((s, s + t.duration_minutes) for s, t in fixed)

        def next_free(cursor: int, duration: int) -> int:
            """Advance cursor past any fixed block that [cursor, cursor+duration) hits."""
            moved = True
            while moved:
                moved = False
                for lo, hi in intervals:
                    if cursor < hi and cursor + duration > lo:
                        cursor, moved = hi, True
            return cursor

        placed = list(fixed)
        cursor = _parse_hhmm(start) or 8 * 60
        for task in flexible:
            cursor = next_free(cursor, task.duration_minutes)
            placed.append((cursor, task))
            cursor += task.duration_minutes

        placed.sort(key=lambda pair: pair[0])
        return [(_to_hhmm(start_min), task) for start_min, task in placed]

    def explain(self) -> str:
        """Describe why the current plan looks the way it does."""
        if not self.plan and not self.skipped:
            return "No plan generated yet. Call generate_plan() first."
        used = sum(t.duration_minutes for t in self.plan)
        lines = [
            f"Planned {len(self.plan)} task(s) using {used} of "
            f"{self.available_minutes} available minutes, highest priority first."
        ]
        if self.skipped:
            names = ", ".join(t.title for t in self.skipped)
            lines.append(f"Skipped (not enough time): {names}.")
        return "\n".join(lines)
