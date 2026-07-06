"""Basic tests for the PawPal+ logic layer."""

from pawpal_system import Owner, Pet, Task, Scheduler


def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task from incomplete to complete."""
    task = Task("Morning walk", 30, priority="high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a pet increases that pet's task count by one."""
    pet = Pet("Biscuit", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", 10, priority="high"))

    assert len(pet.tasks) == 1


def test_scheduler_skips_tasks_that_dont_fit():
    """The scheduler leaves out tasks once the time budget runs out."""
    owner = Owner("Jordan", available_minutes=20)
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("Feeding", 10, priority="high"))
    pet.add_task(Task("Long grooming", 60, priority="low"))
    owner.add_pet(pet)

    plan = Scheduler.for_owner(owner).generate_plan()

    titles = [t.title for t in plan]
    assert "Feeding" in titles
    assert "Long grooming" not in titles
