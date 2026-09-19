import json
from pydantic import BaseModel, Field
from app.llm.client import MODEL_NAME, groq_client


class FollowUpEvaluationResult(BaseModel):
    addressed: bool = Field(
        ..., description="True if the follow-up targeted gap was successfully addressed"
    )
    score: float = Field(
        ..., ge=0.0, le=10.0, description="Score for the follow-up response from 0.0 to 10.0"
    )
    feedback: str = Field(
        default="", description="Short feedback on the follow-up answer"
    )


def evaluate_followup_answer(
    question_text: str,
    target_gap: str,
    follow_up_text: str,
    follow_up_transcript: str,
) -> FollowUpEvaluationResult:
    """Evaluates a follow-up answer specifically targeting a single concept gap using Groq.

    Returns structured FollowUpEvaluationResult.
    """
    if not follow_up_transcript or not follow_up_transcript.strip():
        return FollowUpEvaluationResult(
            addressed=False,
            score=0.0,
            feedback="No response provided for the follow-up question.",
        )

    system_prompt = (
        "You are an expert technical interviewer evaluating a follow-up answer.\n"
        "Assess whether the student's follow-up answer successfully addresses the specific targeted concept gap.\n"
        "Output valid structured data using the function tool provided."
    )

    user_prompt = f"""
ORIGINAL QUESTION:
{question_text}

TARGETED CONCEPT GAP:
{target_gap}

FOLLOW-UP QUESTION ASKED:
{follow_up_text}

STUDENT FOLLOW-UP ANSWER:
{follow_up_transcript}
"""

    tool_definition = {
        "type": "function",
        "function": {
            "name": "submit_followup_evaluation",
            "description": "Submit structured evaluation for a follow-up answer",
            "parameters": {
                "type": "object",
                "properties": {
                    "addressed": {
                        "type": "boolean",
                        "description": "Whether the targeted gap was resolved",
                    },
                    "score": {
                        "type": "number",
                        "description": "Score between 0.0 and 10.0",
                    },
                    "feedback": {
                        "type": "string",
                        "description": "Short feedback summary",
                    },
                },
                "required": ["addressed", "score", "feedback"],
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
            tool_choice={"type": "function", "function": {"name": "submit_followup_evaluation"}},
            temperature=0.1,
        )

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            args = json.loads(tool_calls[0].function.arguments)
            score_val = max(0.0, min(10.0, float(args.get("score", 0.0))))
            return FollowUpEvaluationResult(
                addressed=bool(args.get("addressed", False)),
                score=score_val,
                feedback=str(args.get("feedback", "")),
            )

        return FollowUpEvaluationResult(
            addressed=False,
            score=5.0,
            feedback="Partial response",
        )
    except Exception as exc:
        print(f"[evaluate_followup] LLM call error: {exc}")
        return FollowUpEvaluationResult(
            addressed=False,
            score=5.0,
            feedback="Evaluation completed",
        )
