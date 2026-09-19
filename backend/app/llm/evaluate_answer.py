import json
from pydantic import BaseModel, Field
from app.llm.client import MODEL_NAME, groq_client


class AnswerEvaluationResult(BaseModel):
    addressed_concepts: list[str] = Field(
        default_factory=list,
        description="List of expected concepts correctly addressed by the student",
    )
    score: float = Field(
        ..., ge=0.0, le=10.0, description="Overall score for the answer from 0.0 to 10.0"
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="List of expected concepts missed or insufficiently explained",
    )
    ask_follow_up: bool = Field(
        ..., description="True if a follow-up question should be asked to probe a gap"
    )
    follow_up_id: int | None = Field(
        default=None,
        description="ID of the selected follow-up from candidate_follow_ups, if ask_follow_up is true",
    )


def evaluate_main_answer(
    question_text: str,
    expected_concepts: list[str],
    candidate_follow_ups: list[dict],  # list of {"id": int, "text": str, "targets_gap": str}
    transcript: str,
) -> AnswerEvaluationResult:
    """Evaluates a student's text answer using Groq Llama 3.3 70B with structured output.

    Grounded strictly against expected_concepts.
    If a follow-up is recommended, follow_up_id must be chosen from candidate_follow_ups.
    """
    if not transcript or not transcript.strip():
        # Empty transcript fallback
        return AnswerEvaluationResult(
            addressed_concepts=[],
            score=0.0,
            gaps=expected_concepts,
            ask_follow_up=False,
            follow_up_id=None,
        )

    system_prompt = (
        "You are an expert technical interviewer evaluating a student's answer.\n"
        "Evaluate the student's answer STRICTLY against the provided list of expected concepts.\n"
        "Rules:\n"
        "1. Identify which expected concepts were addressed correctly and which were missed/gaps.\n"
        "2. Score the answer from 0.0 to 10.0 based on accuracy and completeness.\n"
        "3. If there are clear gaps and a candidate follow-up matches a missed concept, set ask_follow_up to true and provide its follow_up_id.\n"
        "4. Output valid JSON matching the specified schema."
    )

    user_prompt = f"""
QUESTION:
{question_text}

EXPECTED CONCEPTS:
{json.dumps(expected_concepts, indent=2)}

CANDIDATE FOLLOW-UPS:
{json.dumps(candidate_follow_ups, indent=2)}

STUDENT ANSWER:
{transcript}
"""

    tool_definition = {
        "type": "function",
        "function": {
            "name": "submit_answer_evaluation",
            "description": "Submit structured evaluation for a student's interview answer",
            "parameters": {
                "type": "object",
                "properties": {
                    "addressed_concepts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Expected concepts addressed in the answer",
                    },
                    "score": {
                        "type": "number",
                        "description": "Score between 0.0 and 10.0",
                    },
                    "gaps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Expected concepts missed or incomplete",
                    },
                    "ask_follow_up": {
                        "type": "boolean",
                        "description": "Whether to ask a follow-up question",
                    },
                    "follow_up_id": {
                        "type": ["integer", "null"],
                        "description": "ID of selected candidate follow-up",
                    },
                },
                "required": [
                    "addressed_concepts",
                    "score",
                    "gaps",
                    "ask_follow_up",
                    "follow_up_id",
                ],
            },
        },
    }

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tools=[tool_definition],
            tool_choice={"type": "function", "function": {"name": "submit_answer_evaluation"}},
            temperature=0.1,
        )

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            args = json.loads(tool_calls[0].function.arguments)
            # Clamp score 0-10
            score_val = max(0.0, min(10.0, float(args.get("score", 0.0))))
            return AnswerEvaluationResult(
                addressed_concepts=args.get("addressed_concepts", []),
                score=score_val,
                gaps=args.get("gaps", []),
                ask_follow_up=bool(args.get("ask_follow_up", False)),
                follow_up_id=args.get("follow_up_id"),
            )

        # Fallback if no tool call
        return AnswerEvaluationResult(
            addressed_concepts=[],
            score=5.0,
            gaps=expected_concepts,
            ask_follow_up=False,
            follow_up_id=None,
        )
    except Exception as exc:
        print(f"[evaluate_answer] LLM call error: {exc}")
        # Safe fallback on error
        return AnswerEvaluationResult(
            addressed_concepts=[],
            score=5.0,
            gaps=expected_concepts,
            ask_follow_up=False,
            follow_up_id=None,
        )
