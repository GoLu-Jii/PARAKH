# V1 Technical Architecture — Data Model, LLM Integration, and System Flow

Companion document to `V1_Product_Decisions.md`. That document explains what the platform does and why; this one explains how it's actually built — the data model, exactly where and how the LLM gets involved, and the end-to-end flow of a single interview session.

---

## 1. Confirmed Tech Stack

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
| LLM (evaluation, follow-up selection, reports, offline question generation) | Groq API — Llama 3.3 70B (or current best available Groq-hosted model) |

---

## 2. Data Model

### `topics`
```
id, name
```
Fixed set for V1: DSA, Operating Systems, DBMS, Computer Networks, System Design.

### `concepts`
```
id, topic_id, name, cognitive_level (1-10)
```
The fundamental unit of content — not the question. A topic decomposes into many concepts, each carrying its own level. There is deliberately **no** separate `level` field on `questions` — a question's level is inherited entirely from its parent concept. If the same idea needs testing at multiple difficulties (e.g. "Hash Tables" at both a definitional level and a trade-offs level), that's two separate concept rows, not one concept with a variable level.

### `questions`
```
id, concept_id, question_text, expected_concepts (json list, 2-4 short strings), is_llm_generated (bool)
```
`expected_concepts` is the single most important field in the schema — it's the whitelist every downstream LLM call is grounded against, both for grading the main answer and for deciding whether a follow-up is warranted.

### `follow_ups`
```
id, question_id, follow_up_text, targets_gap (which expected_concept this follow-up is designed to probe)
```
2-4 rows per question, authored (or generated-then-reviewed) at the same time as the question itself. This table is what turns "the LLM invents a follow-up" into "the LLM selects a follow-up" — a foundational hallucination-safety decision for this project.

### `students`
```
id, email, username, avatar, created_at
```

### `student_topic_progress`
```
student_id, topic_id, current_level, last_interview_date
```

### `student_concept_state`
```
student_id, concept_id, status (not_seen / weak / cleared), last_attempt_date
```
The deliberately simple stand-in for a full mastery-scoring model. Three discrete states, not a continuous 0.0–1.0 score — chosen because a real confidence-weighted mastery model needs usage data to calibrate that doesn't exist yet at V1.

### `interview_sessions`
```
id, student_id, topic_id, target_level, started_at, ended_at, question_ids_asked (ordered list), outcome (level_up / same / dismissed)
```
A `dismissed` outcome (connection drop, tab close) is excluded from the daily attempt count entirely — this row still exists for internal bookkeeping but is treated as if it never happened for every product-facing purpose.

### `attempts`
```
id, session_id, student_id, question_id, transcript, addressed_concepts (json), gaps (json), score,
follow_up_id_used (nullable), follow_up_transcript (nullable), follow_up_addressed (nullable), follow_up_score (nullable),
timestamp
```
One row per question per session (not per follow-up) — a follow-up updates the same row rather than creating a second one, keeping "one row = one question" clean for report generation.

---

## 3. The Deterministic Selection Rule (No LLM)

Given a student, a topic, and a target level (either their `current_level`, or a higher one they explicitly chose to attempt):

1. Pull all `questions` whose parent `concept.cognitive_level` matches the target level, for that topic.
2. Cross-reference against `student_concept_state`: prioritize concepts marked `weak`, then `not_seen`, then everything else.
3. Exclude any `question_id` already present in this session's `question_ids_asked`.
4. Take the top-ranked remaining candidate.
5. If no candidates remain at this level (bank exhausted): trigger offline-style generation on demand (see Section 5), insert the result into `questions`/`follow_ups` after passing a basic sanity check, and select it.

Repeat four times per session. This entire process is backend logic — no LLM call is involved in deciding *what* to ask.

---

## 4. Level Advancement Rule

```
average(score across 4 main-question attempts) >= 7
AND
min(score across 4 main-question attempts) >= 4
→ level_up

otherwise → same
```

Both conditions are required — the floor prevents one badly-handled question from being averaged away by three strong ones. On level-up: `student_topic_progress.current_level` increments, `student_topic_progress.last_interview_date` updates, and every concept touched in the session gets its `student_concept_state.status` updated (gaps recorded → `weak`; addressed cleanly with a strong score → `cleared`).

---

## 5. LLM Integration Points

There are exactly four places the LLM is called in this system — never more, and never as a freeform "generate an interview" call.

### 5.1 Answer Evaluation (live, per question)
**Input:** `question_text`, `expected_concepts`, all `follow_ups` rows for this question (text + `targets_gap`), the raw verbatim transcript.
**Output (structured):**
```json
{
  "addressed_concepts": ["..."],
  "score": 0,
  "gaps": ["..."],
  "ask_follow_up": true,
  "follow_up_id": "..."
}
```
Critically, `follow_up_id` is a **selection** from the pre-authored options passed in, never freely generated text. The backend validates the returned id actually belongs to this question before trusting it — if it doesn't, no follow-up is asked, rather than falling back to trusting unvalidated model output.

### 5.2 Follow-up Evaluation (live, conditional)
Same call shape as 5.1, scoped specifically to whether the targeted gap (`follow_ups.targets_gap`) was addressed in the follow-up answer. Result is written into the same `attempts` row (`follow_up_transcript`, `follow_up_addressed`, `follow_up_score`), not a new row.

### 5.3 Report Generation (live, end of session)
**Input:** the four `attempts` rows for the session — scores, gaps, addressed_concepts — **not** the raw transcripts.
**Output:** narrative report text (summary, strong areas, areas for improvement), per the V1 report format.
This is the lowest-risk LLM call in the system: it narrates already-validated structured data into prose rather than generating or evaluating any new technical claim, so there's no new surface area for hallucination.

### 5.4 Question Generation (offline-first, human-reviewed)
**Not a live/runtime-only call.** Primary use is batch authoring: for a given `(concept, level)` pair, using a type/depth template —

| Level band | Question type | Expected answer depth |
|---|---|---|
| Low (recognition) | "What is X?" | One or two sentences, core definition |
| Low-mid (explain) | "How does X work?" | A few sentences, 2-3 key steps |
| Mid (apply) | "Given [scenario], how would you use X?" | Correct application with brief reasoning |
| Mid-high (trade-offs) | "When would X fail / when would you avoid it?" | Compares against an alternative, names a real limitation |
| High (deep/unfamiliar) | Multi-step reasoning under a novel constraint | Reasoning touching several concepts, justifies a decision |

**Input:** concept, level, the type/depth row above, 2-3 sibling questions at the same level as style examples, optionally a short grounding excerpt from a trusted source for concepts the author isn't fully confident about.
**Output:** `question_text`, `expected_concepts`, 3 candidate `follow_ups` (each tagged with a `targets_gap`).
**Every batch-generated output goes through human review before entering the live `questions` table** — this is what makes generation-assisted authoring safe where live, unreviewed generation would not be.

**Runtime fallback** (Section 3, step 5) reuses this exact same call shape when a level's bank is empty — it is the rare exception, not the default path, and its output should still be logged for later review even though it enters rotation immediately out of necessity.

---

## 6. End-to-End Flow of One Session

```
Student picks topic (+ optionally: attempt a higher level)
        │
        ▼
Create interview_sessions row (target_level, started_at)
        │
        ▼
┌───────────────────────────────────────────────┐
│  FOUR TIMES:                                    │
│                                                  │
│  1. Deterministic selection (Section 3)         │
│         → question chosen, no LLM               │
│  2. Browser TTS speaks question_text            │
│         → no backend involvement                │
│  3. Student speaks → MediaRecorder → Groq       │
│     Whisper → transcript                        │
│  4. LLM call 5.1 (Answer Evaluation)            │
│         → write attempts row                     │
│  5. If ask_follow_up: speak follow_ups.text      │
│     (DB read, not LLM-generated) → student       │
│     answers → Whisper → LLM call 5.2             │
│         → update same attempts row               │
└───────────────────────────────────────────────┘
        │
        ▼
Compute level_up / same (Section 4) — deterministic
        │
        ▼
Update student_topic_progress, student_concept_state,
interview_sessions (ended_at, outcome)
        │
        ▼
LLM call 5.3 (Report Generation) — from structured
attempts data only
        │
        ▼
Report shown to student
```

---

## 7. Hallucination Guardrails Summary

| Guardrail | Mechanism |
|---|---|
| Grounded evaluation | LLM only checks answers against `expected_concepts`, never freely judges "correctness" in the abstract |
| Follow-up selection, not generation | Live follow-ups are always chosen from `follow_ups` rows written/reviewed in advance |
| Structured output | Every LLM call returns a fixed JSON shape, never freeform prose to parse |
| Server-side validation | Backend confirms any `follow_up_id` returned actually belongs to the current question before using it |
| Bounded follow-up depth | Maximum one follow-up per question — no open-ended multi-turn chains that compound drift |
| Verbatim transcript only | The raw transcript is always passed as-is into evaluation calls, never paraphrased or summarized first |
| Human review before bank entry | All offline-generated content is reviewed before reaching students; only the rare runtime fallback skips this, and even then is logged for later review |
| No LLM memory | Cross-session and cross-question state lives entirely in Postgres (`student_concept_state`, `attempts`) — the LLM is never asked to "remember" a conversation |

---

## 8. Explicitly Deferred to V2+

- Continuous per-concept mastery scoring (replacing the discrete `not_seen`/`weak`/`cleared` state)
- Weighted multi-factor question selection (replacing the simple weak-first ranking rule)
- Full prerequisite knowledge graph between concepts
- Licensed multi-source content ingestion pipeline (Stack Exchange, curated repositories, documentation)
- Separate Interviewer/Judge LLM roles as distinct calls
- Per-question transcript breakdown in reports
- Cross-session trend references in reports
- In-session hints
- Self-serve account/data deletion
