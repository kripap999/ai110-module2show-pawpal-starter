"""CLI demo for PawPal+.

A temporary testing ground: builds an owner with two pets and several tasks,
then prints today's schedule to the terminal. Run with: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def build_demo_owner() -> Owner:
    """Create a sample owner with two pets and a handful of tasks."""
    owner = Owner("Jordan", available_minutes=90)

    biscuit = Pet("Biscuit", "dog", breed="Golden Retriever", age=4)
    biscuit.add_task(Task("Morning walk", 30, priority="high", category="walk"))
    biscuit.add_task(Task("Feeding", 10, priority="high", category="feeding"))
    biscuit.add_task(Task("Fetch / play", 25, priority="low", category="enrichment"))

    mochi = Pet("Mochi", "cat", breed="Tabby", age=2)
    mochi.add_task(Task("Feeding", 10, priority="high", category="feeding"))
    mochi.add_task(Task("Medication", 5, priority="medium", category="meds"))
    mochi.add_task(Task("Litter cleanup", 15, priority="medium", category="grooming"))

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner


def print_schedule(owner: Owner, scheduler: Scheduler) -> None:
    """Print today's plan as a readable, time-stamped list."""
    plan = scheduler.generate_plan()

    print(f"Today's schedule for {owner.name} "
          f"({len(owner.pets)} pets, {owner.available_minutes} min available)")
    print("=" * 55)

    # Lay tasks out sequentially starting at 8:00 AM.
    minutes = 8 * 60
    for task in plan:
        hh, mm = divmod(minutes, 60)
        print(f"  {hh:02d}:{mm:02d}  {task.title:<16} "
              f"({task.duration_minutes} min) [priority: {task.priority}]")
        minutes += task.duration_minutes

    print("=" * 55)
    print(scheduler.explain())


def main() -> None:
    owner = build_demo_owner()
    scheduler = Scheduler.for_owner(owner)
    print_schedule(owner, scheduler)


if __name__ == "__main__":
    main()
