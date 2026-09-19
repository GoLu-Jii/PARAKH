import json
from app.llm.client import MODEL_NAME, groq_client


def generate_interview_report(
    topic_name: str,
    target_level: int,
    outcome: str,
    attempt_summaries: list[dict],
) -> str:
    """Generates a narrative interview report using Groq Llama 3.3 70B.

    Inputs ONLY validated structured attempt data (scores, addressed_concepts, gaps) —
    NEVER raw transcripts. Lowest-risk LLM call.
    """
    system_prompt = (
        "You are an expert technical evaluator generating an executive interview feedback report for a student.\n"
        "State performance plainly and clearly without softening or overly flattering failures.\n"
        "The report MUST include:\n"
        "1. Overall Performance Summary\n"
        "2. Demonstrated Strengths\n"
        "3. Weak Areas / Gaps Identified\n"
        "4. Suggested Study Areas\n"
        "5. Final Level Outcome Status (whether level increased or remains unchanged)"
    )

    user_prompt = f"""
TOPIC: {topic_name}
TARGET LEVEL: {target_level}
FINAL LEVEL OUTCOME: {outcome}

SESSION ATTEMPTS DATA:
{json.dumps(attempt_summaries, indent=2)}
"""

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or "Report generation completed."
    except Exception as exc:
        print(f"[generate_report] LLM call error: {exc}")
        # Deterministic fallback text if Groq call fails
        avg_score = (
            sum(a.get("score", 0) for a in attempt_summaries) / len(attempt_summaries)
            if attempt_summaries
            else 0
        )
        all_strengths = [c for a in attempt_summaries for c in a.get("addressed_concepts", [])]
        all_gaps = [g for a in attempt_summaries for g in a.get("gaps", [])]

        return f"""# Interview Performance Report — {topic_name} (Level {target_level})

## Overall Performance Summary
You completed a {target_level}-level session in {topic_name} with an average score of {avg_score:.1f}/10.

## Demonstrated Strengths
{chr(10).join('- ' + s for s in set(all_strengths)) if all_strengths else '- No key concepts were fully cleared.'}

## Weak Areas / Gaps Identified
{chr(10).join('- ' + g for g in set(all_gaps)) if all_gaps else '- No major gaps recorded.'}

## Level Outcome
Outcome: **{outcome.upper()}** (Current level {"increases" if outcome == "level_up" else "remains unchanged"}).
"""
