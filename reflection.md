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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
