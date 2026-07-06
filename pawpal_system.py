"""PawPal+ logic layer.

Backend classes for the pet care planner. This is the "skeleton" generated
from the Phase 1 UML: class names, attributes, and empty method stubs.
Scheduling logic gets filled in during a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care task, e.g. a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    category: str = "general"  # e.g. walk, feeding, meds, grooming
    recurring: bool = False


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
        ...


@dataclass
class Owner:
    """The pet owner and their daily constraints/preferences."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    available_minutes: int = 120
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        ...


class Scheduler:
    """Builds a daily plan from a pet's tasks under time/priority constraints."""

    def __init__(self, tasks: list[Task], available_minutes: int) -> None:
        self.tasks = tasks
        self.available_minutes = available_minutes

    def sort_tasks(self) -> list[Task]:
        """Order tasks by priority (and duration as a tiebreaker)."""
        ...

    def generate_plan(self) -> list[Task]:
        """Pick and order tasks that fit within available_minutes."""
        ...

    def explain(self) -> str:
        """Return a human-readable reason for why the plan looks the way it does."""
        ...
