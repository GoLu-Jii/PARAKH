# Parakh — Implementation Reference

This is the single reference document for actually building Parakh — the database schema, the folder/file structure with what each piece is responsible for, the API surface, the LLM integration points, and the deterministic logic underneath them. `V1_Product_Decisions.md` explains what the product does and why; this document exists to answer "where does this go and what does it do" while writing code.

---

## 1. Tech Stack

| Component | Choice |
|---|---|
| Frontend | React + Vite + Tailwind |
| Frontend hosting | Vercel |
| Backend | FastAPI (Python) |
| Backend hosting | Hugging Face Spaces (Docker) |
| Auth | Supabase Auth (Google OAuth provider) |
| Database | Supabase Postgres |
| Speech-to-Text | Groq API — Whisper Large v3 Turbo |
| Text-to-Speech | Browser Web Speech API (`SpeechSynthesis`) |
| LLM | Groq API — Llama 3.3 70B (or current best available Groq-hosted model) |

---

## 2. Environment Variables

| Variable | Used by | Purpose |
|---|---|---|
| `SUPABASE_URL` | backend, frontend | Project endpoint |
| `SUPABASE_ANON_KEY` | frontend | Client-side auth/session calls |
| `SUPABASE_SERVICE_ROLE_KEY` | backend only | Server-side privileged DB access — never exposed to the frontend |
| `GROQ_API_KEY` | backend only | Whisper (STT) and Llama (LLM) calls |
| `VITE_API_BASE_URL` | frontend | Where the FastAPI backend is deployed (points at HF Spaces) |

The service role key and the Groq key must never reach the frontend bundle — both STT and LLM calls happen backend-side, per the folder structure below, specifically so these secrets stay server-only.

---

## 3. Database Schema

### `topics`
```
id, name
```
Fixed set for V1: DSA, Operating Systems, DBMS, Computer Networks, System Design.

### `concepts`
```
id, topic_id, name, cognitive_level (1-10)
```
The fundamental content unit — not the question. A question's level is inherited entirely from its parent concept; there is no separate level field on `questions`. Testing the same idea at multiple difficulties means multiple concept rows (e.g. "Hash Tables — definition" at level 2, "Hash Tables — trade-offs" at level 6), not one concept with a variable level.

### `questions`
```
id, concept_id, question_text, expected_concepts (json list, 2-4 short strings), is_llm_generated (bool)
```
`expected_concepts` is the whitelist every LLM evaluation call is grounded against — it's what a complete answer should touch, written by a human (or generated then human-reviewed) at authoring time, never invented live.

### `follow_ups`
```
id, question_id, follow_up_text, targets_gap
```
2-4 rows per question, authored alongside the question. `targets_gap` names which `expected_concepts` entry this follow-up is designed to probe if missing. This table is what makes live follow-up handling a **selection**, not a generation — the core hallucination-safety decision in the system.

### `students`
```
id, email, username, avatar, created_at
```

### `student_topic_progress`
```
student_id, topic_id, current_level, last_interview_date
```
`last_interview_date` backs the daily-limit check (2 interviews/day total, shared across topics, resetting at 4 AM local).

### `student_concept_state`
```
student_id, concept_id, status (not_seen / weak / cleared), last_attempt_date
```
Deliberately three discrete states rather than a continuous mastery score — a real confidence-weighted model needs usage data to calibrate that doesn't exist yet.

### `interview_sessions`
```
id, student_id, topic_id, target_level, started_at, ended_at, question_ids_asked (ordered list), outcome (level_up / same / dismissed)
```
`dismissed` (connection drop, tab close) is excluded from the daily attempt count entirely.

### `attempts`
```
id, session_id, student_id, question_id, transcript,
addressed_concepts (json), gaps (json), score,
follow_up_id_used (nullable), follow_up_transcript (nullable),
follow_up_addressed (nullable), follow_up_score (nullable),
timestamp
```
One row per **question** per session — a follow-up updates this same row rather than creating a second one.

### `badges` / `student_badges`
```
badges: id, name, description
student_badges: student_id, badge_id, earned_at
```
Checked via simple queries after each session ends — no separate engine.

---

## 4. Folder & File Structure

```
parakh/
│
├── README.md
├── docs/
│   ├── project_scope.md
│   ├── tech_stack_decisions.md
│   ├── V1_Product_Decisions.md
│   ├── V1_Technical_Architecture.md
│   └── Parakh_Implementation_Reference.md   (this file)
│
├── frontend/
│   └── src/
│       ├── main.tsx                 — app entry point, mounts React to the DOM
│       ├── App.tsx                  — top-level routing between pages
│       ├── api/
│       │   ├── client.ts            — the one place base URL, headers, and error handling live
│       │   ├── auth.ts              — login/logout calls to Supabase Auth
│       │   ├── interview.ts         — start session, submit answer, fetch report
│       │   └── types.ts             — shared TypeScript types matching backend response shapes
│       ├── pages/
│       │   ├── Onboarding.tsx       — topic selection, self-assessment, academic info form
│       │   ├── Home.tsx             — topic picker, "attempt a harder level" option
│       │   ├── Interview.tsx        — the live question/answer loop UI
│       │   ├── Report.tsx           — end-of-session report display
│       │   └── Profile.tsx          — current level per topic, badges
│       ├── components/
│       │   ├── VoiceRecorder.tsx    — wraps MediaRecorder, handles the retry-on-silence prompt
│       │   ├── QuestionPlayer.tsx   — wraps browser TTS to speak question_text aloud
│       │   └── LevelBadge.tsx       — small display component for level/badges
│       ├── hooks/
│       │   ├── useAuth.ts           — current user/session state
│       │   ├── useSpeechSynthesis.ts — thin wrapper around SpeechSynthesis
│       │   └── useMediaRecorder.ts  — thin wrapper around MediaRecorder + audio blob handling
│       └── store/                   — shared auth/session state (Context or a small store)
│
├── backend/
│   └── app/
│       ├── main.py                  — FastAPI app instance, router registration, CORS config
│       ├── config.py                — loads env vars (Supabase keys, Groq key)
│       ├── routers/                 — see Section 5 for the actual endpoint list
│       │   ├── auth.py
│       │   ├── onboarding.py
│       │   ├── interview.py
│       │   ├── report.py
│       │   └── profile.py
│       ├── engine/                  — deterministic logic only — NO LLM calls anywhere in this folder
│       │   ├── selection.py         — Section 6.1: picks the next question
│       │   ├── leveling.py          — Section 6.2: computes level_up/same
│       │   └── session_flow.py      — orchestrates the 4-question loop, calls engine + llm modules in order
│       ├── llm/                     — every Groq LLM call, isolated from engine/ on purpose
│       │   ├── client.py            — Groq client wrapper, structured-output helper
│       │   ├── evaluate_answer.py   — Section 7.1
│       │   ├── evaluate_followup.py — Section 7.2
│       │   ├── generate_report.py   — Section 7.3
│       │   └── generate_question.py — Section 7.4 (offline batch + rare runtime fallback)
│       ├── speech/
│       │   └── transcribe.py        — wraps the Groq Whisper call
│       ├── db/
│       │   ├── client.py            — Supabase client init (service role key)
│       │   └── queries/             — one file per table, plain read/write functions
│       │       ├── students.py
│       │       ├── progress.py
│       │       ├── concept_state.py
│       │       ├── sessions.py
│       │       ├── attempts.py
│       │       ├── questions.py
│       │       └── badges.py
│       └── schemas/                 — pydantic request/response models, one file per router's shapes
│           ├── interview.py
│           ├── report.py
│           └── common.py
│
├── content/                          — Phase 7's world, separate from the live app
│   ├── generation_scripts/
│   │   └── generate_batch.py         — calls the same generate_question logic offline, in bulk
│   ├── staging/                      — generated, not yet reviewed
│   ├── approved/                     — reviewed, ready to seed
│   └── seed_to_db.py                 — loads approved/ content into Supabase
│
└── supabase/
    ├── config.toml
    └── migrations/
        └── 0001_init.sql             — full DDL for every table in Section 3
```

---

## 5. API Endpoints (`backend/routers/`)

| Method & Path | Router file | Purpose |
|---|---|---|
| `POST /onboarding` | `onboarding.py` | Saves topic selections, self-assessment, academic info; creates `student_topic_progress` rows at Level 1 |
| `GET /topics` | `onboarding.py` or `profile.py` | Returns the fixed topic list plus this student's current level in each, for the home screen |
| `POST /interview/start` | `interview.py` | Body: `{topic_id, target_level}`. Creates an `interview_sessions` row, runs selection (6.1), returns the first question |
| `POST /interview/{session_id}/answer` | `interview.py` | Body: audio blob. Runs transcription (Section 8) → evaluation (7.1) → writes `attempts` row → returns either a follow-up prompt, the next question, or a session-complete signal |
| `POST /interview/{session_id}/followup-answer` | `interview.py` | Same shape, scoped to follow-up evaluation (7.2), updates the existing `attempts` row |
| `GET /interview/{session_id}/report` | `report.py` | Triggers report generation (7.3) once the session is complete, returns the report |
| `GET /profile` | `profile.py` | Current level per topic, badges earned |

Auth itself is handled client-side by Supabase Auth directly (Google OAuth redirect flow) — the backend only ever receives an already-authenticated request with a Supabase session token to verify, it doesn't run its own login flow.

---

## 6. Deterministic Engine Logic (`backend/app/engine/`) — no LLM involved

### 6.1 Selection (`selection.py`)
Given a student, topic, and target level:
1. Pull `questions` whose parent `concept.cognitive_level` matches the target level, for that topic.
2. Rank by `student_concept_state.status`: `weak` first, then `not_seen`, then everything else.
3. Exclude any `question_id` already in this session's `question_ids_asked`.
4. Return the top candidate. If none remain, trigger the runtime fallback (Section 7.4).

### 6.2 Leveling (`leveling.py`)
```
average(score across 4 main-question attempts) >= 7
AND
min(score across 4 main-question attempts) >= 4
→ level_up
otherwise → same
```
On `level_up`: increment `student_topic_progress.current_level`. Always: update `last_interview_date`, and update `student_concept_state` per concept touched this session (`weak` if gaps were recorded, `cleared` if addressed cleanly with a strong score).

---

## 7. LLM Integration Points (`backend/app/llm/`)

### 7.1 `evaluate_answer.py`
**In:** `question_text`, `expected_concepts`, this question's `follow_ups` (text + `targets_gap`), raw verbatim transcript.
**Out:**
```json
{ "addressed_concepts": [], "score": 0, "gaps": [], "ask_follow_up": true, "follow_up_id": "..." }
```
Backend validates `follow_up_id` belongs to this question before trusting it.

### 7.2 `evaluate_followup.py`
Same shape, scoped to whether the targeted gap was addressed in the follow-up answer.

### 7.3 `generate_report.py`
**In:** the four `attempts` rows (scores, gaps, addressed_concepts) — never raw transcripts.
**Out:** narrative report text. Lowest-risk call — narrates already-validated data, generates no new technical claims.

### 7.4 `generate_question.py`
**In:** concept, level, a type/depth template (recognition → explain → apply → trade-offs → deep reasoning), 2-3 sibling questions as style examples.
**Out:** `question_text`, `expected_concepts`, 3 candidate `follow_ups`.
Primary use: offline batch authoring (`content/generation_scripts/`), always human-reviewed before entering `questions`. Secondary use: rare runtime fallback when Section 6.1 finds an empty pool — enters rotation immediately out of necessity, but should still be logged for later review.

---

## 8. Speech (`backend/app/speech/transcribe.py`)

Wraps the Groq Whisper call: receives an audio blob from the frontend, forwards it to Groq's Whisper Large v3 Turbo endpoint, returns the transcript string. If Whisper returns empty/unclear, the router returns a "couldn't hear that, try again" response rather than passing an empty transcript into evaluation.

---

## 9. End-to-End Session Flow

```
POST /interview/start
        │
        ▼
┌─────────────────────────────────────────────┐
│  FOUR TIMES:                                  │
│  selection.py → question                      │
│  frontend: QuestionPlayer speaks it            │
│  frontend: VoiceRecorder captures answer       │
│  POST /interview/{id}/answer                   │
│    → transcribe.py → evaluate_answer.py        │
│    → write attempts row                        │
│  if ask_follow_up:                             │
│    frontend speaks follow_ups.text (DB read)   │
│    POST /interview/{id}/followup-answer        │
│    → transcribe.py → evaluate_followup.py      │
│    → update same attempts row                  │
└─────────────────────────────────────────────┘
        │
        ▼
leveling.py computes outcome
        │
        ▼
update student_topic_progress, student_concept_state,
interview_sessions
        │
        ▼
GET /interview/{id}/report → generate_report.py
```

---

## 10. Hallucination Guardrails

| Guardrail | Where it lives |
|---|---|
| Grounded evaluation against `expected_concepts` | `evaluate_answer.py` |
| Follow-up selection, not generation | `follow_ups` table + `evaluate_answer.py` |
| Structured output only | `llm/client.py` |
| Server-side validation of `follow_up_id` | `interview.py` router |
| Bounded follow-up depth (max 1) | `session_flow.py` |
| Verbatim transcript, never paraphrased | `transcribe.py` → `evaluate_answer.py` |
| Human review before bank entry | `content/staging/` → `content/approved/` workflow |
| No LLM memory — state lives in Postgres | `db/queries/` (`concept_state.py`, `attempts.py`) |

---

## 11. Content Authoring Workflow (`content/`)

Not part of the live request path. `generate_batch.py` calls the same logic as `generate_question.py` offline, in bulk, per `(concept, level)` pair. Output lands in `staging/` for manual review; only what's approved moves to `approved/`; `seed_to_db.py` loads approved content into the live `questions`/`follow_ups` tables via Supabase.

---

## 12. Explicitly Deferred to V2+

Continuous mastery scoring · weighted multi-factor selection · prerequisite knowledge graph · licensed multi-source ingestion · separate Interviewer/Judge LLM roles · per-question transcript breakdown in reports · cross-session trend references · in-session hints · self-serve account deletion.
