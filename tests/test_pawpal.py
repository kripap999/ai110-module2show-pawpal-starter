"""Basic tests for the PawPal+ logic layer."""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Task, Scheduler


def _owner_with_two_pets() -> Owner:
    """Owner with two pets and a few scheduled tasks, for filter/sort tests."""
    owner = Owner("Jordan", available_minutes=90)

    biscuit = Pet("Biscuit", "dog")
    biscuit.add_task(Task("Morning walk", 30, time="08:00", priority="high"))
    biscuit.add_task(Task("Fetch", 25, time="", priority="low"))

    mochi = Pet("Mochi", "cat")
    mochi.add_task(Task("Feeding", 10, time="07:30", priority="high"))

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner


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


# --- sorting by time --------------------------------------------------------
def test_sort_by_time_orders_scheduled_and_puts_unscheduled_last():
    """Tasks sort by 'HH:MM'; blank-time tasks fall to the end."""
    scheduler = Scheduler.for_owner(_owner_with_two_pets())

    ordered = [t.title for t in scheduler.sort_by_time()]

    assert ordered == ["Feeding", "Morning walk", "Fetch"]


# --- filtering --------------------------------------------------------------
def test_filter_by_pet_returns_only_that_pets_tasks():
    """filter_by_pet returns tasks for the named pet only."""
    scheduler = Scheduler.for_owner(_owner_with_two_pets())

    titles = [t.title for t in scheduler.filter_by_pet("Biscuit")]

    assert titles == ["Morning walk", "Fetch"]


def test_filter_by_pet_unknown_name_returns_empty():
    """An unknown pet name yields no tasks."""
    scheduler = Scheduler.for_owner(_owner_with_two_pets())

    assert scheduler.filter_by_pet("Nobody") == []


def test_filter_by_status_splits_done_and_todo():
    """filter_by_status separates completed tasks from outstanding ones."""
    owner = _owner_with_two_pets()
    owner.pets[0].tasks[0].mark_complete()  # complete "Morning walk"
    scheduler = Scheduler.for_owner(owner)

    done = [t.title for t in scheduler.filter_by_status(completed=True)]
    todo = [t.title for t in scheduler.filter_by_status(completed=False)]

    assert done == ["Morning walk"]
    assert "Morning walk" not in todo
    assert set(todo) == {"Fetch", "Feeding"}


# --- conflict detection -----------------------------------------------------
def test_find_conflicts_flags_shared_time():
    """Two tasks at the same time produce one conflict warning naming both."""
    owner = Owner("Jordan")
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("Feeding", 10, time="08:00"))
    pet.add_task(Task("Medication", 5, time="08:00"))
    owner.add_pet(pet)

    conflicts = Scheduler.for_owner(owner).find_conflicts()

    assert len(conflicts) == 1
    assert "08:00" in conflicts[0]
    assert "Feeding" in conflicts[0] and "Medication" in conflicts[0]


def test_find_conflicts_none_when_times_differ_or_blank():
    """No conflict when times are distinct, and blank times never conflict."""
    owner = Owner("Jordan")
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("Feeding", 10, time="08:00"))
    pet.add_task(Task("Walk", 30, time="09:00"))
    pet.add_task(Task("Play", 15, time=""))
    pet.add_task(Task("Nap", 15, time=""))
    owner.add_pet(pet)

    assert Scheduler.for_owner(owner).find_conflicts() == []


# --- recurring tasks --------------------------------------------------------
def test_next_occurrence_none_for_non_recurring():
    """A one-off task has no next occurrence."""
    assert Task("Feeding", 10, frequency="none").next_occurrence() is None


def test_next_occurrence_daily_advances_one_day():
    """A daily task's next occurrence is due one day after its due date."""
    task = Task("Meds", 5, frequency="daily", due_date=date(2026, 7, 6))

    nxt = task.next_occurrence()

    assert nxt is not None
    assert nxt.due_date == date(2026, 7, 7)
    assert nxt.completed is False


def test_next_occurrence_weekly_advances_one_week():
    """A weekly task's next occurrence is due seven days later."""
    task = Task("Grooming", 20, frequency="weekly", due_date=date(2026, 7, 6))

    nxt = task.next_occurrence()

    assert nxt.due_date == date(2026, 7, 6) + timedelta(weeks=1)


def test_complete_task_spawns_and_appends_next_occurrence():
    """Completing a recurring task marks it done and queues the next one."""
    pet = Pet("Mochi", "cat")
    task = Task("Meds", 5, frequency="daily", due_date=date(2026, 7, 6))
    pet.add_task(task)

    nxt = pet.complete_task(task)

    assert task.completed is True
    assert nxt is not None and nxt in pet.tasks
    assert len(pet.tasks) == 2


def test_complete_task_non_recurring_adds_nothing():
    """Completing a one-off task returns None and adds no new task."""
    pet = Pet("Mochi", "cat")
    task = Task("Bath", 30, frequency="none")
    pet.add_task(task)

    nxt = pet.complete_task(task)

    assert nxt is None
    assert len(pet.tasks) == 1


# --- planning: completed tasks & timeline -----------------------------------
def test_generate_plan_skips_completed_tasks():
    """A completed task is not scheduled and does not consume the budget."""
    owner = Owner("Jordan", available_minutes=40)
    pet = Pet("Mochi", "cat")
    done = Task("Feeding", 10, priority="high")
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(Task("Walk", 30, priority="high"))
    owner.add_pet(pet)

    plan = Scheduler.for_owner(owner).generate_plan()

    titles = [t.title for t in plan]
    assert "Feeding" not in titles
    assert "Walk" in titles


def test_build_timeline_flows_flexible_tasks_from_start():
    """Untimed tasks flow back-to-back starting at the given start time."""
    owner = Owner("Jordan", available_minutes=100)
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("Long", 30, priority="high"))
    pet.add_task(Task("Short", 15, priority="high"))
    owner.add_pet(pet)
    scheduler = Scheduler.for_owner(owner)
    scheduler.generate_plan()

    timeline = scheduler.build_timeline(start="08:00")

    # Equal priority sorts shorter-first, so "Short" leads at 08:00.
    assert [(ts, t.title) for ts, t in timeline] == [
        ("08:00", "Short"),
        ("08:15", "Long"),
    ]


def test_build_timeline_anchors_fixed_time_and_avoids_overlap():
    """A fixed-time task stays put; a flexible task is pushed past its block."""
    owner = Owner("Jordan", available_minutes=100)
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("Meds", 15, time="08:00", priority="high"))
    pet.add_task(Task("Walk", 30, priority="high"))
    owner.add_pet(pet)
    scheduler = Scheduler.for_owner(owner)
    scheduler.generate_plan()

    at = {t.title: ts for ts, t in scheduler.build_timeline(start="08:00")}

    assert at["Meds"] == "08:00"
    assert at["Walk"] == "08:15"  # jumped past the fixed 08:00–08:15 block


# --- edge cases: empty / no-task inputs -------------------------------------
def test_pet_with_no_tasks_produces_empty_plan():
    """A pet with no tasks yields empty results everywhere, not an error."""
    owner = Owner("Jordan", available_minutes=60)
    owner.add_pet(Pet("Mochi", "cat"))
    scheduler = Scheduler.for_owner(owner)

    assert scheduler.generate_plan() == []
    assert scheduler.build_timeline() == []
    assert scheduler.find_conflicts() == []
    assert scheduler.sort_by_time() == []


def test_owner_with_no_pets_produces_empty_plan():
    """An owner with no pets at all schedules nothing without crashing."""
    scheduler = Scheduler.for_owner(Owner("Jordan", available_minutes=60))

    assert scheduler.generate_plan() == []


def test_explain_before_generate_plan_prompts_to_run_it():
    """explain() gives a clear message when no plan has been built yet."""
    owner = Owner("Jordan")
    owner.add_pet(Pet("Mochi", "cat"))

    message = Scheduler.for_owner(owner).explain()

    assert "generate_plan()" in message


def test_zero_available_minutes_skips_everything():
    """With no time budget, every task is skipped and the plan is empty."""
    owner = Owner("Jordan", available_minutes=0)
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("Feeding", 10, priority="high"))
    owner.add_pet(pet)
    scheduler = Scheduler.for_owner(owner)

    assert scheduler.generate_plan() == []
    assert len(scheduler.skipped) == 1
