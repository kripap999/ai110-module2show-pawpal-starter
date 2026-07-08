import streamlit as st

# Step 1: import the logic layer so the UI can create real objects.
from pawpal_system import Owner, Pet, Task, Scheduler


def fmt_time(value) -> str:
    """Format a st.time_input value as 'HH:MM', or '' when left blank."""
    return value.strftime("%H:%M") if value else ""

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant. Add pets and tasks, then generate a daily plan.")

# Step 2: keep one Owner alive across reruns.
# Streamlit re-runs this script top-to-bottom on every interaction, so we only
# create the Owner the first time and reuse the stored instance after that.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=90)

owner = st.session_state.owner

# --- Owner settings ---------------------------------------------------------
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes = st.number_input(
    "Minutes available today", min_value=5, max_value=600, value=owner.available_minutes, step=5
)

st.divider()

# --- Step 3a: add a pet -----------------------------------------------------
st.subheader("Add a pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name", value="")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed (optional)", value="")
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    if pet_name.strip():
        owner.add_pet(Pet(pet_name.strip(), species, breed=breed.strip()))
        st.success(f"Added {pet_name.strip()} to {owner.name}'s pets.")
    else:
        st.warning("Please enter a pet name.")

st.divider()

# --- Step 3b: add a task to a pet -------------------------------------------
st.subheader("Add a task")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_names = [pet.name for pet in owner.pets]
        target = st.selectbox("Which pet?", pet_names)
        task_title = st.text_input("Task title", value="")
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        col3, col4 = st.columns(2)
        with col3:
            scheduled = st.time_input("Scheduled time (optional)", value=None)
        with col4:
            frequency = st.selectbox("Repeats", ["none", "daily", "weekly"])
        add_task = st.form_submit_button("Add task")

    if add_task:
        if task_title.strip():
            pet = owner.pets[pet_names.index(target)]
            pet.add_task(
                Task(
                    task_title.strip(),
                    int(duration),
                    time=fmt_time(scheduled),
                    priority=priority,
                    frequency=frequency,
                )
            )
            st.success(f"Added '{task_title.strip()}' to {target}.")
        else:
            st.warning("Please enter a task title.")

st.divider()

# --- Current pets & tasks ---------------------------------------------------
st.subheader("Current pets & tasks")
if not owner.pets:
    st.info("No pets yet.")
else:
    scheduler = Scheduler.for_owner(owner)

    # View controls: filter by pet/status and choose the ordering.
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_filter = st.selectbox("Pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.selectbox("Status", ["All", "To do", "Done"])
    with col3:
        order_by = st.radio("Order by", ["priority", "time"], horizontal=True)

    # Start from the whole task list, then narrow it with the logic-layer filters.
    tasks = scheduler.filter_by_pet(pet_filter) if pet_filter != "All pets" else owner.all_tasks()
    if status_filter != "All":
        tasks = [t for t in tasks if t.completed == (status_filter == "Done")]

    # Reuse the scheduler's sorters on whatever the filters produced.
    view = Scheduler(tasks, owner.available_minutes, owner=owner)
    ordered = view.sort_by_time() if order_by == "time" else view.sort_tasks()

    if not ordered:
        st.info("No tasks match this view.")
    else:
        st.table(
            [
                {
                    "time": t.time or "—",
                    "title": t.title,
                    "duration (min)": t.duration_minutes,
                    "priority": t.priority,
                    "repeats": t.frequency,
                    "status": "done" if t.completed else "to do",
                }
                for t in ordered
            ]
        )

    # Conflict detection: warn when two tasks share a scheduled time.
    conflicts = scheduler.find_conflicts()
    if conflicts:
        for message in conflicts:
            st.warning(f"⚠️ {message}")

    # Mark-complete buttons. Completing a recurring task spawns its next occurrence.
    st.caption("Mark a task done — recurring tasks reappear on their next date.")
    for pet in owner.pets:
        for i, task in enumerate(pet.tasks):
            if task.completed:
                continue
            label = f"✓ {pet.name}: {task.title}"
            if st.button(label, key=f"done-{pet.name}-{i}-{task.title}"):
                nxt = pet.complete_task(task)
                if nxt is not None:
                    st.success(f"Completed '{task.title}'. Next {task.frequency} on {nxt.due_date}.")
                else:
                    st.success(f"Completed '{task.title}'.")
                st.rerun()

st.divider()

# --- Generate schedule ------------------------------------------------------
st.subheader("Today's schedule")
if st.button("Generate schedule"):
    scheduler = Scheduler.for_owner(owner)
    plan = scheduler.generate_plan()

    if not plan:
        st.warning("No tasks could be scheduled. Add some tasks (or more time) first.")
    else:
        # Fixed-time tasks anchor at their time; the rest flow around them.
        rows = [
            {
                "time": time_str,
                "task": t.title,
                "duration (min)": t.duration_minutes,
                "priority": t.priority,
            }
            for time_str, t in scheduler.build_timeline()
        ]
        st.table(rows)
        st.info(scheduler.explain())
