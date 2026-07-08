# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Sample output from running `python main.py`:

```
Today's schedule for Jordan (2 pets, 90 min available)
=======================================================
  08:00  Feeding          (10 min) [priority: high]
  08:00  Morning walk     (30 min) [priority: high]
  08:30  Litter cleanup   (15 min) [priority: medium]
  09:00  Medication       (5 min) [priority: medium]
  09:05  Fetch / play     (25 min) [priority: low]
=======================================================
Planned 5 task(s) using 85 of 90 available minutes, highest priority first.

...(sorting & filtering demo)...

Conflict check
=======================================================
  ⚠️  Conflict at 08:00: Morning walk, Feeding
```

(The demo also prints a sorting & filtering section and a conflict check;
see `main.py` for the full output.)

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
tests/test_pawpal.py .................                                   [100%]

============================== 17 passed in 0.02s ==============================
```

## 📐 Smarter Scheduling

Beyond the basic "fit tasks into a time budget" plan, PawPal+ adds four smarter-scheduling
features. Each is implemented in the logic layer (`pawpal_system.py`) and exercised by both
the CLI demo (`main.py`) and the Streamlit UI (`app.py`).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_tasks()` | `sort_by_time()` orders tasks by `"HH:MM"` (unscheduled tasks last); `sort_tasks()` orders by priority, then shorter tasks first. |
| Filtering | `Scheduler.filter_by_pet()`, `Scheduler.filter_by_status()` | Narrow the task list to a single pet, or to done vs. outstanding tasks. |
| Conflict detection | `Scheduler.find_conflicts()` | Lightweight O(n) check: buckets tasks by exact start time and returns a warning string for any slot booked more than once (across all pets). Returns messages instead of crashing. |
| Recurring tasks | `Task.next_occurrence()`, `Pet.complete_task()` | Completing a `"daily"` or `"weekly"` task auto-creates the next instance (`due_date + timedelta`); one-off tasks don't repeat. |
| Timeline layout | `Scheduler.build_timeline()` | Assigns real clock times to the plan: fixed-time tasks anchor at their time, flexible tasks flow around them without overlapping. |

### Sorting behavior
`Scheduler.sort_by_time()` sorts on the zero-padded `"HH:MM"` string, which compares
chronologically; blank times fall back to `"99:99"` so unscheduled tasks sort to the end.

### Filtering behavior
`Scheduler.filter_by_pet(name)` returns only the named pet's tasks (using the owner reference);
`Scheduler.filter_by_status(completed)` splits done vs. outstanding tasks.

### Conflict detection logic
`Scheduler.find_conflicts()` returns a list of human-readable warnings (empty when the day is
clear). It flags tasks sharing an **exact** start time; overlapping durations are intentionally
out of scope (see `reflection.md` §2b).

### Recurring task logic
`Task.next_occurrence()` uses `datetime.timedelta` to compute the next due date (+1 day for
`"daily"`, +1 week for `"weekly"`). `Pet.complete_task()` marks a task done and, when it recurs,
appends the fresh next instance to the pet's task list.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
