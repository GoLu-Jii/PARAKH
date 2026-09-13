# V1 Product Decisions — The Story of How This Platform Actually Works

This document walks through the platform the way a student would actually experience it — from the moment they sign up to the moment they close their tenth interview report — and captures every product decision made along the way. It's meant to be read start to finish, not looked up like a reference table (that version exists separately, in the technical document).

---

## Joining the Platform

A student arrives, signs in with their Gmail account — nothing more elaborate than that, no roll number, no separate password to remember — and the system quietly generates a username and an avatar for them. They're free to rename the username once, if they want, but otherwise they're in.

Before their first interview, they go through a short onboarding: they pick at least three broad topics they care about (from a fixed list this platform launches with — Data Structures & Algorithms, Operating Systems, DBMS, Computer Networks, and System Design), they give a rough self-assessment of where they stand in each (beginner, intermediate, advanced), and they share a bit of academic context. None of this self-assessment is blindly trusted, though — every student starts at Level 1 in every topic they pick, regardless of what they claimed. If someone genuinely is advanced, they don't have to grind through levels that don't reflect their real ability — before starting any interview, they can choose to attempt a harder level directly instead of the one they're currently sitting at. If they clear it, they jump straight there. If they don't, they simply stay where they were. That one mechanism does double duty: it's both the "skip levels you've outgrown" feature and, quietly, the answer to the cold-start problem — there's no separate placement test to build, because the level-skip option already lets someone prove their claim on day one.

Once onboarding is done, the topics they picked are locked in for now. There's no changing your mind mid-way through V1 — that's a deliberate simplification, not an oversight.

## Starting an Interview

From the home screen, a student either continues with a topic they've already chosen or, at that moment, decides which of their topics to practice today. What they don't see, deliberately, is any preview of what's inside — the specific concepts a topic will test are kept opaque. They walk in not knowing exactly what's coming, the same way a real interview works.

There's a hard cap on how much of this someone can do in a day: **two interviews total, across all topics combined**, resetting each day at 4:00 AM in the student's own timezone. It's not "one per topic" — it's a shared daily budget, which gives a student the freedom to go deep on one topic they're struggling with instead of being forced to rotate evenly across all three.

Every interview is a fixed **four questions**, regardless of level. What changes as the level climbs isn't how many questions there are — it's how demanding each one becomes, and how much follow-up probing happens around each answer. At the lower levels, a follow-up only shows up if the system genuinely detects a gap in what was said. At higher levels, every single question comes with at least one follow-up as a matter of course. That's also, quietly, how a Level 8 interview ends up taking noticeably longer than a Level 2 one, without ever needing to be a different length by design — it just naturally stretches as the probing gets heavier. The whole thing is capped loosely by time too — no student is left in an interview forever, give or take a few minutes around the expected length for that level.

## Living Through the Interview

The system speaks each question aloud, and the student answers by speaking back — nothing is typed. If a follow-up comes, it never announces itself as one. It just sounds like the next natural thing an interviewer would ask, the same way a real person doesn't pause to say "now for my follow-up question" — they just ask it.

There's no scorekeeping shown mid-interview. A student doesn't see "correct" or "incorrect" flash after each answer, and they don't see their level ticking up in real time. All of that is held back until the very end, in one report — the interview itself is meant to feel like being interviewed, not like taking a quiz with a running scoreboard.

If the system genuinely can't make out what was said — silence, background noise, a garbled recording — it doesn't just guess or fail silently. It surfaces something simple like "I couldn't quite hear that — want to try again?" and gives one retry. If the second attempt is still unintelligible, that question is marked as attempted anyway, for better or worse — the system doesn't quietly discard a bad recording and pretend the question never happened.

For V1, there are no hints available mid-interview if a student is stuck — they either know it or they don't, and the interview moves on. A hint system, spending down to maybe one hint per session, is explicitly something being saved for a later version, not this one.

## What Happens When It's Over

Right after the fourth question, a report is generated — not the raw scoring, but a written summary: what the student's overall performance looked like this time, which areas they showed real strength in, and which areas showed real gaps. For V1, this is a summary-level report — a full question-by-question transcript breakdown, with every answer laid out individually, is something planned for a later, more detailed version, not this one.

Whether the student's level moves depends on one clear rule: their average score across all four main questions needs to clear a real bar, **and** no single question is allowed to have gone badly enough to slip beneath a minimum floor. In other words, three great answers can't paper over one genuinely bad one — every question has to at least clear a basic threshold on its own, on top of the average being strong overall.

If a student doesn't level up, the report doesn't try to cushion that. There's a deliberate decision here that this platform is not going to be gentle about failure — it isn't in the business of telling a student they did great when they didn't. The report is meant to state plainly, and without softening, exactly where the answer fell short, so there's nothing ambiguous for the student to explain away to themselves. The intent isn't encouragement — it's an evaluator that refuses to lie to make someone feel better, which is treated as one of this platform's actual differentiators rather than a rough edge to smooth out later.

Each report stands entirely on its own for V1 — it doesn't look back and compare this session to the last one, or track a visible trend line yet. That kind of longitudinal view is left for later, once there's enough real usage to make comparisons meaningful.

## Growing Over Time

Outside of any single interview, a student can see their level for each topic sitting plainly in their profile — an actual number, not a disguised badge or tier name. Ten levels exist per topic in V1, and climbing them is the entire long-term arc of using the platform.

Alongside levels, there's a small set of lightweight badges to mark real milestones — completing a first interview ever, reaching a meaningfully high level across multiple different topics (rewarding breadth, not just depth in one area), showing up consistently across several different days rather than in one binge, and having at least one session where every single question was answered strongly with no follow-ups even needed. None of these are meant to carry much weight — they're a small, low-cost layer of recognition sitting on top of the real signal, which is the level itself.

## The Edges of V1, On Purpose

A few things are deliberately left rough or entirely unbuilt for this version, not because they were missed, but because they're not worth solving before the platform has real users to learn from.

If a student's connection drops or they close the tab mid-interview, that entire session is simply thrown away — it doesn't count as one of their two daily attempts, and it isn't scored or saved in any partial form. It's as if it never happened.

There's no self-serve way for a student to delete their account or their data in V1. If someone wants that, it's handled by hand — they reach out directly, and their data is removed manually. It's not a polished flow, but it's a real, honest answer rather than silence on the question, and it's enough for a small pilot without needing to build infrastructure around something that will rarely come up this early.

Taken together, this is a platform that is intentionally narrow in scope but not careless about it — every corner that's been cut has been cut on purpose, with a clear line drawn to a later version where it gets revisited, rather than quietly ignored.
