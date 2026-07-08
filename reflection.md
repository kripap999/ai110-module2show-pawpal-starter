# PawPal+ Project Reflection

## 1. System Design

The three core actions a user should be able to perform are:

    1. Enter basic owner and pet information like the owner’s name, the pet’s name, and basic pet details.
    2. Add or edit pet care tasks, including the task name, duration, and priority.
    3. Generate and view a daily care plan that organizes the pet’s tasks based on time available, task priority, and owner preferences.

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
    For my first UML design, I will use four main classes: Owner, Pet, Task, and Scheduler. The Owner class stores information about the pet owner. The Pet class stores information about the pet. The Task class stores care tasks, like feeding, walking, or giving medicine. The Scheduler class chooses the tasks and puts them into a daily plan.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. AI review pointed out my `Scheduler` was disconnected: it took a raw task list and `available_minutes` separately, even though that data already lived on `Pet` and `Owner`. I added an alternate constructor `Scheduler.for_pet(owner, pet)` that builds the scheduler directly from an owner and pet, and updated the UML to show these relationships. I also noticed `priority` is a plain string, which will complicate sorting later, but kept it simple for now.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers three constraints: the owner's **time budget** (`available_minutes`), each task's **priority** (high / medium / low), and each task's optional **scheduled time** (`"HH:MM"`). The time budget is the hard limit — `generate_plan()` stops adding tasks once the minutes run out. Priority is the main ordering signal: I sort high-priority tasks first so the essentials (feeding, medication) get scheduled even on a busy day, and I use shorter duration as a tiebreaker so more small tasks can fit. Scheduled time drives the timeline layout and conflict detection rather than selection. I decided priority mattered most because for a pet owner the cost of *missing* a critical task is far higher than the cost of skipping a nice-to-have like extra playtime, so the algorithm should protect high-priority work first.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

My `Scheduler.find_conflicts()` only flags tasks that share the **exact same start time** (the same `"HH:MM"` string). It does *not* detect **overlapping durations** — a 30-minute walk at 08:00 and a feeding at 08:15 both run at once, but my code stays silent because their start strings differ. I chose the exact-match approach because it is lightweight: it buckets tasks by time in a single O(n) pass, needs no interval math, and returns plain warning strings instead of raising an error. Detecting true overlaps would mean computing each task's end time (`start + duration_minutes`), sorting the intervals, and comparing neighbors — noticeably more code and more ways to get an off-by-one wrong.

This tradeoff is reasonable for a personal daily pet-care planner: the tasks are short and few, an owner is likely to enter clean, on-the-hour or half-hour times, and a missed near-overlap is a minor annoyance rather than a real failure. The exact-match check catches the most common and most obvious mistake — two things booked for the very same moment — while keeping the code simple enough to trust and easy to read. If the app ever grew to manage many pets or back-to-back appointments, upgrading to interval-based overlap detection would be the natural next step.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used my AI coding assistant across the whole build: turning the UML into class stubs, implementing each algorithm (sorting, filtering, conflict detection, recurrence, the timeline layout), wiring those methods into the Streamlit UI, generating the test suite, and doing "evaluate and refine" reviews. The most helpful prompts were **specific and file-referenced** — e.g. "implement `sort_by_time()` to sort `"HH:MM"` strings with blanks last," or "how could `find_conflicts()` be simplified for readability?" Vague prompts produced generic code; concrete ones that named the method and the expected behavior produced code I could drop in and test immediately.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When I asked how to simplify `find_conflicts()`, the assistant offered an `itertools.groupby` version that was shorter and more "Pythonic." I rejected it: it required pre-sorting, forced me to materialize each group with `list(grp)` just to check its length, and buried a walrus assignment inside a comprehension — clever but hard to read. I kept my plain `setdefault` loop instead. More generally I verified AI suggestions two ways: by running `python -m pytest` (21 tests) after every change, and by running `python main.py` to eyeball real output. That caught a real bug too — the original `generate_plan()` counted already-completed tasks against the time budget, which the "skip completed" fix and a new test resolved.

**c. AI strategy**

- Which assistant features were most effective, and how did separate sessions help?

The most effective features were **file-referenced chat** (attaching `pawpal_system.py` so the model reasoned about my actual code, not a guess), **multi-file edits** (the recurrence feature touched both `Task` and `Pet`, and the assistant edited them together consistently), and **inline diffs** I could review before accepting. Using a **separate chat session per phase** kept each conversation's context focused — the testing session wasn't cluttered with UI-wiring history, so its suggestions stayed on-topic and its prompts stayed sharp. The biggest lesson about being the **lead architect** is that the AI is fast at *producing* code but does not own the *decisions*: it will happily generate a clever-but-unreadable refactor or pick a debatable default (like anchoring recurrence to today vs. the due date). My job was to set the direction, judge each suggestion against readability and correctness, verify with tests, and keep the design coherent. The AI accelerated the typing; I owned the architecture.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested the core logic and its edge cases (21 tests in `tests/test_pawpal.py`): sorting order (chronological, blanks last), filtering by pet and status, conflict detection (flagged on shared times, silent otherwise), recurrence (daily → +1 day, weekly → +1 week, one-off → nothing), and planning (respects the budget, skips completed tasks, lays out fixed times without overlap). I also added edge cases — a pet with no tasks, an owner with no pets, and a zero-minute budget — to confirm the scheduler returns empty results instead of crashing. These mattered because they are exactly the behaviors a user depends on and the ones most likely to break silently when I refactor.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**★★★★☆ (4/5).** All 21 tests pass and cover the main algorithms plus the obvious edge cases, so I trust the core logic. I held back the last star because two areas are untested: conflict detection only catches *exact* time matches (not overlapping durations — see §2b), and I haven't tested malformed input such as a bad `"HH:MM"` string, a negative duration, or an unknown priority label. Those would be my next tests.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the clean separation between the logic layer (`pawpal_system.py`) and the UI (`app.py`). Because all the scheduling logic lives in testable methods on `Scheduler`, `Task`, and `Pet`, the Streamlit UI just calls them and displays results — and the same methods power the CLI demo. The `build_timeline()` algorithm, which anchors fixed-time tasks and flows flexible ones around them without overlapping, is the piece I'm proudest of because it took real thought to get the interval-skipping right.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd upgrade conflict detection from exact-time matches to true **overlap detection** using each task's start + duration. I'd also make the planner smarter: rank by priority *density* (value per minute) so a long high-priority task doesn't crowd out several important short ones, and factor in `due_date` so overdue tasks bubble up. Finally I'd add input validation so a malformed time or negative duration fails gracefully instead of surprising the scheduler.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The biggest thing I learned is that **I stay the lead architect even when the AI writes most of the code**. The assistant is excellent at producing implementations quickly, but it doesn't own the tradeoffs — it will offer a clever refactor that hurts readability, or a subtly wrong default, and it's my job to catch that. Keeping the logic layer separate, writing tests, and reviewing every diff let me move fast *and* keep control of the design.
