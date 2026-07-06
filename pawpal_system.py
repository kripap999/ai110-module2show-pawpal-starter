"""PawPal+ logic layer.

Backend classes for the pet care planner. These implement the Phase 1 UML:
Task, Pet, Owner, and the Scheduler that builds a daily plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# How each priority label ranks when sorting (higher = more important).
PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Task:
    """A single pet care task, e.g. a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    category: str = "general"  # e.g. walk, feeding, meds, grooming
    recurring: bool = False
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    @property
    def priority_rank(self) -> int:
        """Numeric rank for the task's priority (unknown labels rank lowest)."""
        return PRIORITY_RANK.get(self.priority, 0)


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
    """The 'brain': orders tasks and builds a daily plan within a time budget."""

    def __init__(self, tasks: list[Task], available_minutes: int) -> None:
        self.tasks = tasks
        self.available_minutes = available_minutes
        self.plan: list[Task] = []
        self.skipped: list[Task] = []

    @classmethod
    def for_owner(cls, owner: Owner) -> "Scheduler":
        """Build a scheduler from all of an owner's pets' tasks and time budget."""
        return cls(tasks=owner.all_tasks(), available_minutes=owner.available_minutes)

    @classmethod
    def for_pet(cls, owner: Owner, pet: Pet) -> "Scheduler":
        """Build a scheduler for a single pet, using the owner's time budget."""
        return cls(tasks=pet.tasks, available_minutes=owner.available_minutes)

    def sort_tasks(self) -> list[Task]:
        """Order tasks by priority (high first), then shorter tasks first."""
        return sorted(
            self.tasks,
            key=lambda t: (-t.priority_rank, t.duration_minutes),
        )

    def generate_plan(self) -> list[Task]:
        """Greedily pick the highest-priority tasks that fit the time budget."""
        remaining = self.available_minutes
        self.plan = []
        self.skipped = []
        for task in self.sort_tasks():
            if task.duration_minutes <= remaining:
                self.plan.append(task)
                remaining -= task.duration_minutes
            else:
                self.skipped.append(task)
        return self.plan

    def explain(self) -> str:
        """Describe why the current plan looks the way it does."""
        if not self.plan and not self.skipped:
            return "No plan generated yet. Call generate_plan() first."
        used = sum(t.duration_minutes for t in self.plan)
        lines = [
            f"Planned {len(self.plan)} task(s) using {used} of "
            f"{self.available_minutes} available minutes, "
            f"highest priority first."
        ]
        if self.skipped:
            names = ", ".join(t.title for t in self.skipped)
            lines.append(f"Skipped (not enough time): {names}.")
        return "\n".join(lines)
