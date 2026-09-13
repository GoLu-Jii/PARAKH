# AI Mock Interview Platform — Project Scope

## 1. Problem Statement

Students need a structured, repeatable way to practice technical interviews and understand where they genuinely stand — not just whether they "feel ready," but concrete, measured areas of strength and weakness across the topics that matter for their goals (placements, skill-building, or general practice).

## 2. Core Idea

A voice-based AI interview platform where a student logs in, picks a topic, and is interviewed by an AI interviewer. Questions get progressively harder as the student proves competence, gated behind a level system. After each interview, the student receives an immediate report on their performance and their level is adjusted accordingly. Over time, the platform tracks growth per topic, not just a single score.

The platform is not built exclusively for one college. It is meant to be usable by any student, anywhere. The first real users will come from the founder's own college, but the college is a starting audience, not a constraint baked into the product.

## 3. Guiding Principles for V1

- **Free-tier only.** V1 is built entirely on free infrastructure and free-tier APIs. Nothing about the product should require payment to run at pilot scale. If the pilot proves the idea works, a move to paid infrastructure (to support real scale) is a separate, later decision — not something V1 needs to solve.
- **Pilot, not launch.** V1 is meant to validate the idea with a small, real group of users (starting with one college) before expanding further. It is not meant to handle "entire university" scale on day one.
- **Solo build.** The project is being built by one person. Scope for V1 is deliberately kept to what one person can realistically build, maintain, and support.
- **Student-only.** V1 has no admin, faculty, or institution-facing view. It is entirely for the student using the product themselves.
- **Privacy-conscious by default.** Voice is used only to conduct the interview. Nothing about the student's spoken voice itself is kept after the interview — only the resulting text and evaluation are stored.

---

## 4. V1 Scope

### 4.1 Login & Identity

- Students log in using their Gmail account. No separate roll number, college ID, or custom password system.
- Any Gmail account can be used — the platform is not restricted to a specific college's email domain. This keeps it open to anyone, anywhere, consistent with the platform not being college-locked.
- On first login, the system automatically generates a username and avatar for the student. The student can edit the auto-generated username once afterward if they choose.
- Every new student starts at **Level 1** across all topics by default.

### 4.2 Onboarding — Basic Info

After first login, the student fills in some basic information:

- **Topic/domain preferences** — the student selects at least 3 broad areas of interest from the fixed V1 topic list: **Data Structures & Algorithms, Operating Systems, DBMS, Computer Networks, and System Design**. These are intentionally broad categories for V1, not narrow or highly specific subtopics — narrow topics can be introduced later once there's real usage data on what students actually want.
- **Self-assessed skill level** per selected topic (e.g., beginner / intermediate / advanced) — this is a starting signal the system can use to guide the student toward a more appropriate entry point, rather than assuming every student is a complete beginner.
- **Academic info** — college year/stream and similar basic details that help contextualize the student's progress.
- **Goal/intent (optional)** — e.g., preparing for placements, general practice, specific company prep. This isn't used for anything functional in V1, but it's useful context to capture early for future personalization.

### 4.3 Home Page

The home page offers two main actions:

**A. Take an Interview**

The student can either:
- Start an interview based on the topics/preferences chosen during onboarding, or
- Choose a specific topic fresh, regardless of what was selected earlier.

**B. Take an Interview for Your Project** *(V1, but positioned as a lower-priority add-on, not core to initial scope)*

The student can submit a link to one of their own project repositories, and the system conducts an interview specifically about that project — testing whether the student actually understands the code they claim to have built, rather than testing general topic knowledge. This is a strong differentiator for the platform but is explicitly scoped as something to build **after** the core topic-based interview flow is solid, not before.

### 4.4 The Interview Flow

1. The student either has a topic pre-selected or picks one at the start.
2. The interview is fully voice-based: the system speaks each question aloud, and the student responds by speaking their answer aloud (not typing).
3. Questions start at the student's current level for that topic and get progressively harder as the student proves they've cleared the current level.
4. **Level-skip option:** a student can choose, **before starting an interview**, to attempt a harder-level question/challenge directly. If they pass it, they jump straight to that level instead of climbing one level at a time. This respects students who already know the material and don't want to grind through levels they've clearly outgrown.
5. A student must "clear" their current level before being allowed to progress normally to the next one (outside of the level-skip path).
6. **Daily limit:** a student can take **at most two interview sessions per day, across all topics combined**. The daily interview day resets at **4:00 AM in the student's own timezone**. This sets a deliberate cap on interview volume while allowing the student to spend both sessions on the same topic if they choose.

### 4.5 Evaluating the Student

The core signal for evaluation is the **quality and correctness of the student's spoken answers** — how well they explain concepts, how complete and accurate their answers are, and how they handle follow-up or probing questions asked during the interview (handling a "why" or "what if" follow-up well is a much stronger signal of real understanding than just answering the first question correctly).

Two additional signals are tracked for the student's own awareness, but are **not** used to determine level progression, since they can unfairly penalize students who are simply less fluent speakers or more naturally deliberate thinkers:
- **Response time** — how long the student takes to start answering. Shown back to the student as a reflection point (e.g., "you took notably longer on X questions"), not scored.
- **Pauses during answers** — tracked and shown for self-awareness, not scored, since pausing correlates with nervousness or non-native fluency as much as it does with not knowing an answer.

**Facial expression analysis** was considered as a potential evaluation signal but is explicitly **excluded from V1** and pushed to a future research phase (see V2), due to privacy/consent concerns around biometric data and the current unreliability of expression-based competence signals.

### 4.6 The Report

Immediately after the interview ends, the student receives a report covering:
- Overall performance summary for that session
- Specific strengths shown
- Specific weak areas / gaps identified
- Suggested areas to revisit or study further
- Whether their level for that topic increased, stayed the same, or needs another attempt

### 4.7 Progress Tracking

Students can view their **current level per topic** in their profile, so they can see where they currently stand rather than only seeing a single overall score. V1 does not expose a historical level timeline; longitudinal history can be introduced later once the product has real usage data to justify it.

### 4.8 Gamification — Badges

Students can earn badges for milestones and achievements, for example:
- Completing their first interview ever
- Clearing a certain level across multiple topics (breadth)
- Completing interviews across several different days (consistency)
- Having a session where every main question was answered strongly

These are meant to be lightweight, low-cost additions that increase engagement without adding much complexity.

### 4.9 Data & Privacy Approach for V1

- The student's spoken answers are converted to text for evaluation purposes.
- Only the resulting **text transcript and evaluation results** are stored. The raw voice recording itself is **not** kept after the interview is processed.
- Because login is open to any Gmail account (not verified against a specific institution), V1 does not attempt to formally verify that a user is a genuine student of any particular college — it is open by design.

---

## 5. V2 and Future Scope

Everything below is explicitly **not** part of V1. These are ideas to revisit once the core platform is built, working, and validated with real users.

### 5.1 Facial Expression Analysis

Explored as a possible additional evaluation signal (e.g., confidence, engagement) but deferred due to privacy/consent complexity and the current unreliability of mapping expressions to actual competence. Treated as a future research spike, not a committed feature.

### 5.2 Project Repository Interview (Full Version)

While a basic version of "interview me about my project" is planned even for V1 as a lower-priority add-on, a deeper version of this — where the system meaningfully understands a student's actual codebase structure and asks genuinely code-aware questions — is a significant undertaking on its own and is expected to mature well beyond V1.

### 5.3 Daily Engagement Features

- **Daily questions** — a lightweight, low-commitment daily question unrelated to a full interview session.
- **Daily streaks** — rewarding consistent day-to-day usage, similar to habit-building apps.

### 5.4 Social / Comparative Features

- **Leaderboards** — opt-in, likely scoped per college/branch/year, to drive organic engagement.
- **Peer comparison in reports** — e.g., showing a student how they compare to others in the same topic, once there's enough real usage data to make this meaningful.

### 5.5 Institutional / Paid Upgrade Path

If V1 proves successful on free infrastructure, the plan is to move to paid infrastructure and services (for LLM usage, voice processing, hosting, etc.) to support real scale, and only then pursue formal adoption by the university (or other institutions) as paying or sanctioned users. This is a deliberate "prove it free, then scale it paid" approach.

### 5.6 Admin / Faculty View

Not part of V1 by design. If the platform is adopted more formally by an institution later, a faculty or admin-facing view (e.g., seeing aggregate student performance, managing question banks) may become relevant, but this is entirely a future consideration.

### 5.7 Multi-Institution Growth

Since the platform is not built to be college-specific, future growth could extend usage to other colleges/universities beyond the founding pilot group, without requiring structural changes to the product's core idea.

---

## 6. What's Deliberately Out of Scope (Not Just "Later" — Currently Not Planned)

- Anti-cheating or proctoring measures
- Mobile app
- Multi-language support
- Formal identity verification of "real" students (beyond requiring a Gmail login)

These are noted here so they are consciously excluded, not accidentally forgotten.
