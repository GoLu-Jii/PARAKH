# Tech Stack & Implementation Decisions — V1

Final technical decisions for the platform, given the locked constraints: solo build, zero budget, free-tier infrastructure only, voice-based interview (full STT + TTS).

---

## Final Stack at a Glance

| Component | Choice |
|---|---|
| Frontend | React + Vite + Tailwind |
| Frontend hosting | Vercel |
| Backend | FastAPI (Python) |
| Backend hosting | Hugging Face Spaces (Docker) |
| Auth | Supabase Auth (Google OAuth provider) |
| Database | Supabase Postgres |
| Speech-to-Text | Groq API — Whisper Large v3 Turbo |
| Text-to-Speech | Browser Web Speech API (SpeechSynthesis) |
| LLM (evaluation + question flow + reports) | Groq API — Llama 3.3 70B (or current best available Groq-hosted model) |

---

## 1. Authentication + Database — Supabase

Free Postgres bundled with built-in Auth and one-click Google sign-in — handles the OAuth redirect flow, session/token management, and user table without building that subsystem yourself.

**Caveat:** Supabase pauses a project after ~7 days of zero activity. A non-issue for an actively used pilot, but the first request after a pause will be noticeably slower — worth knowing so it doesn't look like a bug.

---

## 2. Speech-to-Text — Groq Whisper API (Large v3 Turbo)

Free tier: 2,000 requests/day, 7,200 audio-seconds/hour (~8 hours of audio/day), 25 MB max file size per request, no credit card required. Dramatically more accurate on technical interview content than browser STT, and consistent regardless of the student's browser or OS.

**Flow:** browser records the student's answer via `MediaRecorder` → sent to the FastAPI backend → forwarded to Groq's Whisper endpoint → text transcript returned.

---

## 3. Text-to-Speech — Browser Web Speech API (`SpeechSynthesis`)

Free, unlimited, zero backend round-trip, built into every modern browser. Reading a question aloud only needs clarity, not emotional realism, so the free option and the correct engineering option are the same choice here. It also means "speak the question" never depends on the server being awake or Groq quota having room left — it happens instantly, client-side.

**Future upgrade path (V2):** swapping in Groq's Orpheus TTS or ElevenLabs for a more natural voice is a contained change if this is isolated behind a single function/module now (e.g. `speakQuestion(text)`).

---

## 4. LLM — Question Flow, Answer Evaluation, Follow-ups, Reports — Groq API (Llama 3.3 70B)

Free tier: 30 requests/minute, 6,000 tokens/minute, 14,400 requests/day at the organization level. Same provider and pattern already proven in Chasr, including forcing structured/tool-use output rather than trusting freeform text.

**Design pattern:** one LLM call per answer, forced structured output shaped around the actual V1 follow-up-selection design:

```json
{
  "addressed_concepts": ["..."],
  "score": 0,
  "gaps": ["..."],
  "ask_follow_up": true,
  "follow_up_id": "..."
}
```

The LLM is **not** asked to freely generate a live follow-up question. It receives the pre-written follow-up options for the current question and selects a `follow_up_id` from those options when a follow-up is warranted. The backend validates that the returned `follow_up_id` actually belongs to the current question before using it. If the id is invalid, no follow-up is asked.

**Known limitation:** 30 requests/minute shared across every active session is fine for a small pilot but will need attention (or a paid tier) once usage scales past a few dozen concurrent students.

---

## 5. Backend Hosting — Hugging Face Spaces (Docker)

Free, supports a Dockerized FastAPI app directly. No uptime guarantee — same cold-start tradeoff as any comparable free host. Reuses the exact deployment setup already proven on Code Sherpa, so there's zero new learning curve. Render remains a fallback if HF Spaces free compute ever proves insufficient.

**Cold-start caveat:** the first interview request after a period of no traffic may take longer than expected while the backend wakes up. This is a free-tier-hosting characteristic, not a bug — worth naming upfront so it doesn't look like a reliability problem during a demo.

---

## 6. Frontend Hosting — Vercel

Already used for Code Sherpa's frontend, has a genuinely permanent free tier for static/React deployments.

---

## 7. Question Bank, Content Model & Leveling Engine

The V1 question bank is a curated content model built around **topics → concepts → questions → follow-ups**, plus lightweight per-student state. The database is responsible for storing interview knowledge and student state; the LLM does not own the interview flow.

### `topics`

```text
id, name
```

Fixed set for V1: **DSA, Operating Systems, DBMS, Computer Networks, System Design.**

### `concepts`

```text
id, topic_id, name, cognitive_level
```

The fundamental unit of content — not the question. A topic decomposes into many concepts, each carrying its own cognitive level from 1-10. There is deliberately **no separate `level` field on `questions`** — a question's level is inherited entirely from its parent concept. If the same idea needs testing at multiple difficulties (e.g. "Hash Tables" at both a definitional level and a trade-offs level), that's two separate concept rows, not one concept with a variable level.

### `questions`

```text
id, concept_id, question_text, expected_concepts, is_llm_generated
```

`expected_concepts` is the single most important field in the schema — it's the whitelist every downstream LLM call is grounded against, both for grading the main answer and for deciding whether a follow-up is warranted.

### `follow_ups`

```text
id, question_id, follow_up_text, targets_gap
```

2-4 rows per question, authored (or generated-then-reviewed) at the same time as the question itself. This table is what turns "the LLM invents a follow-up" into "the LLM selects a follow-up" — a foundational hallucination-safety decision for this project.

### `students`

```text
id, email, username, avatar, created_at
```

### `student_topic_progress`

```text
student_id, topic_id, current_level
```

Current level is the authoritative per-topic progression state. The V1 product does not expose a level-history timeline.

### `student_concept_state`

```text
student_id, concept_id, status (not_seen / weak / cleared), last_attempt_date
```

The deliberately simple stand-in for a full mastery-scoring model. Three discrete states, not a continuous 0.0–1.0 score — chosen because a real confidence-weighted mastery model needs usage data to calibrate that doesn't exist yet at V1.

### `interview_sessions`

```text
id, student_id, topic_id, target_level, started_at, ended_at,
question_ids_asked (ordered list), outcome (level_up / same / dismissed)
```

A `dismissed` outcome (connection drop, tab close) is excluded from the daily attempt count entirely — this row still exists for internal bookkeeping but is treated as if it never happened for every product-facing purpose.

### `attempts`

```text
id, session_id, student_id, question_id, transcript,
addressed_concepts (json), gaps (json), score,
follow_up_id_used (nullable), follow_up_transcript (nullable),
follow_up_addressed (nullable), follow_up_score (nullable),
timestamp
```

One row per question per session (not per follow-up) — a follow-up updates the same row rather than creating a second one, keeping "one row = one question" clean for report generation.

The global daily interview limit is enforced from `interview_sessions`: a student may start at most **two non-dismissed interview sessions during the current interview day**, where the interview day resets at **4:00 AM in the student's own timezone**.

---

## 8. Level-Skip Mechanic

Level skip is an alternate entry point into the same evaluation logic — a student can request a higher target level directly before starting an interview; if they pass it, `current_level` jumps to that level instead of incrementing by one. No separate system is needed.

---

## 9. Gamification / Badges

A `badges` table (badge definitions) and a `student_badges` join table (which student earned which badge and when). Badge-earning conditions are checked as simple queries after each interview session ends — no separate engine is needed for V1's lightweight badge set.

---

## 10. What's Deliberately Deferred (Not Researched for V1)

- **Project-repo interview deepening** — the basic project-interview add-on remains a lower-priority V1 feature; deeper repository parsing/understanding is a separate technical problem, closer to what Code Sherpa already solves.
- **Facial expression analysis** — excluded from V1 by design; no infrastructure research needed until/unless it is revisited.
- **Paid TTS upgrade (Groq Orpheus / ElevenLabs)** — revisit once free-tier limits are actually being hit in practice, not before.
