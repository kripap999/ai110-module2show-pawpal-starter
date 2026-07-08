"""CLI demo for PawPal+.

A temporary testing ground: builds an owner with two pets and several tasks,
then prints today's schedule to the terminal. Run with: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def build_demo_owner() -> Owner:
    """Create a sample owner with two pets and a handful of tasks.

    Tasks are deliberately added *out of time order* so sort_by_time() has
    something to reorder, and one task is pre-completed to exercise the
    status filter.
    """
    owner = Owner("Jordan", available_minutes=90)

    biscuit = Pet("Biscuit", "dog", breed="Golden Retriever", age=4)
    biscuit.add_task(Task("Morning walk", 30, time="08:00", priority="high", category="walk"))
    biscuit.add_task(Task("Feeding", 10, time="07:30", priority="high", category="feeding"))
    biscuit.add_task(Task("Fetch / play", 25, priority="low", category="enrichment"))
    biscuit.tasks[1].mark_complete()  # Biscuit already had breakfast

    mochi = Pet("Mochi", "cat", breed="Tabby", age=2)
    mochi.add_task(Task("Medication", 5, time="09:00", priority="medium", category="meds"))
    # Deliberately at 08:00 too — same slot as Biscuit's walk, to trigger a conflict.
    mochi.add_task(Task("Feeding", 10, time="08:00", priority="high", category="feeding"))
    mochi.add_task(Task("Litter cleanup", 15, priority="medium", category="grooming"))

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner


def print_tasks(label: str, tasks: list) -> None:
    """Print a labeled list of tasks as 'time  title (status)'."""
    print(f"\n{label}")
    print("-" * 55)
    if not tasks:
        print("  (none)")
        return
    for task in tasks:
        status = "done" if task.completed else "to do"
        print(f"  {task.time or '--:--'}  {task.title:<16} [{status}]")


def demo_sort_and_filter(scheduler: Scheduler) -> None:
    """Show the sorting and filtering methods working in the terminal."""
    print("\nSorting & filtering demo")
    print("=" * 55)

    # Sorting: tasks were added out of order; sort_by_time() lines them up.
    print_tasks("All tasks, sorted by time (blank times last):", scheduler.sort_by_time())

    # Filtering by completion status.
    print_tasks("Still to do:", scheduler.filter_by_status(completed=False))
    print_tasks("Already done:", scheduler.filter_by_status(completed=True))

    # Filtering by pet name.
    print_tasks("Only Mochi's tasks:", scheduler.filter_by_pet("Mochi"))


def demo_conflicts(scheduler: Scheduler) -> None:
    """Print any scheduling conflicts, or a clear all-clear message."""
    print("\nConflict check")
    print("=" * 55)
    conflicts = scheduler.find_conflicts()
    if not conflicts:
        print("  No conflicts — every scheduled time is free.")
        return
    for warning in conflicts:
        print(f"  ⚠️  {warning}")


def print_schedule(owner: Owner, scheduler: Scheduler) -> None:
    """Print today's plan as a readable, time-stamped list."""
    scheduler.generate_plan()  # populates the plan that build_timeline() lays out

    print(f"Today's schedule for {owner.name} "
          f"({len(owner.pets)} pets, {owner.available_minutes} min available)")
    print("=" * 55)

    # Fixed-time tasks anchor at their time; the rest flow from 8:00 AM.
    for time_str, task in scheduler.build_timeline():
        print(f"  {time_str}  {task.title:<16} "
              f"({task.duration_minutes} min) [priority: {task.priority}]")

    print("=" * 55)
    print(scheduler.explain())


def main() -> None:
    owner = build_demo_owner()
    scheduler = Scheduler.for_owner(owner)
    print_schedule(owner, scheduler)
    demo_sort_and_filter(scheduler)
    demo_conflicts(scheduler)


if __name__ == "__main__":
    main()
