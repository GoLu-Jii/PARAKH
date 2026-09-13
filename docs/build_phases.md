# Build Phases


Phase 1 — Schema + minimal seed data

Create every table from the technical doc (topics, concepts, questions, follow_ups, students, student_topic_progress, student_concept_state, interview_sessions, attempts) in Supabase. Insert the five fixed topic rows. Then — deliberately — hand-write just enough content for one topic only (a couple of concepts across two or three levels, a handful of questions with real expected_concepts and follow_ups) to have something to actually build and test against. Full content across all five topics is Phase 7, run separately, not a blocker here.

Exit test: the schema is stable and repeatable, and one topic has enough real data to exercise every table at least once.

Phase 2 — Auth + onboarding

Google sign-in via Supabase Auth, backend creates a students row plus auto-generated username/avatar on first login, then the onboarding flow: topic selection from the fixed five, self-assessment per topic, academic info, optional goal/intent. On completion, student_topic_progress rows get created at Level 1 for every chosen topic, regardless of self-assessment.

Exit test: a real Gmail account can sign in, complete onboarding, and the resulting DB state is exactly Level 1 across their chosen topics — nothing more, nothing less.

Phase 3 — The core interview loop, text-only (this is the phase that matters most)

Build the actual interview engine — but with typed text standing in for spoken voice, on purpose. This isolates two completely different risk categories that are easy to conflate if built together: "is the interview logic correct" versus "does the voice pipeline work." Debugging both at once means every bug is ambiguous — is the LLM evaluation wrong, or did Whisper mishear something? Solve one before introducing the other.

Build, in this phase: the deterministic selection rule, session creation and question_ids_asked tracking, the Answer Evaluation LLM call (grounded against expected_concepts, returning structured JSON), the follow-up selection-and-evaluation call, the level-advancement computation, student_concept_state updates, and the report-generation call.

Exit test: a complete 4-question interview can run start to finish through typed input — via a bare API client or the ugliest possible placeholder page — producing a real report and a real level-up/same outcome. It doesn't need to be usable yet. It needs to be correct.

Phase 4 — Voice pipeline

Only now do you add MediaRecorder capture, Groq Whisper transcription, browser TTS for reading questions aloud, and the "I couldn't hear that, want to try again?" retry flow. Every piece of logic underneath is already proven from Phase 3 — this phase is purely about the audio layer working correctly, with no interview-logic uncertainty muddying the debugging.

Exit test: the exact same interview flow from Phase 3 now runs via real spoken voice, in an actual browser, start to finish.

Phase 5 — Real frontend UI

Build the interview screen, the report screen (matching your locked tone and format), the home screen (topic pick, "attempt a harder level" option), and the profile screen (level as a plain number, badges). Everything here is presentation on top of logic that already works — which is exactly why it comes this late, not first. Building UI before the underlying logic is proven means redesigning screens around bugs you haven't found yet.

Exit test: the full student experience is navigable through a real interface, with no direct API calls needed to use the product.

Phase 6 — Edge cases, limits, gamification

Implement the 2-per-day global cap with the 4 AM local reset, session dismissal on disconnect (not counted against the cap), and the four badges. These are exactly the decisions that are easy to design on paper and then forget to actually enforce in code — this phase exists specifically to make sure every "decided" behavior is a real, tested rule, not just a line in a document.

Exit test: every edge-case decision from the product doc is verifiably enforced, not just described.

Phase 7 — Content authoring at scale (runs partly in parallel with 3–6)

This is where the offline generation-then-review workflow happens for real: batch-generate question_text + expected_concepts + candidate follow_ups per concept per level, across all five topics, review and approve every single one before it enters the live tables. This can genuinely start as soon as Phase 1's schema exists — it doesn't need to wait for the interview engine to be built, since it's populating tables the engine will later read from.

Exit test: enough approved content exists across all five topics that a student running several sessions in a row won't hit an empty bank or repeat a question too soon.

Phase 8 — Dogfooding

Run the entire flow yourself, repeatedly, and ideally get one or two trusted friends to do the same before any real student sees it. Watch specifically for: does the LLM's scoring feel sane against your own judgment of the answer, does follow-up selection pick something sensible rather than something odd, how does Whisper handle real accents/background noise/hesitation, what happens if two people hit the API at the same moment given your tight rate limit, and — importantly — does the level-advancement rule feel fair in practice, not just on paper.

Exit test: you personally trust this enough to put it in front of real students, not "it technically works."

Phase 9 — Launch to the pilot

Roll out to your actual college audience. Manual monitoring, the manual account-deletion process ready to go if anyone asks. This is also the point where real usage data starts existing — which matters, because several of your V2 deferred items (real mastery scoring, weighted selection) specifically need real behavioral data to design well, not more upfront guessing.

