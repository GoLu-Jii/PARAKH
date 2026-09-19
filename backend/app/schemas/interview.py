from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    topic_id: int
    target_level: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Optional target level. If omitted, uses student's current topic level.",
    )


class QuestionOut(BaseModel):
    id: int
    question_text: str
    concept_id: int
    cognitive_level: int

    class Config:
        from_attributes = True


class FollowUpOut(BaseModel):
    id: int
    follow_up_text: str

    class Config:
        from_attributes = True


class StartInterviewResponse(BaseModel):
    session_id: str
    topic_id: int
    target_level: int
    current_question_index: int = 1
    total_questions: int = 4
    first_question: QuestionOut


class SubmitAnswerRequest(BaseModel):
    question_id: int
    transcript: str = Field(..., min_length=1, description="Student text answer")


class SubmitFollowUpRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description="Student text follow-up answer")


class AnswerEvaluationOut(BaseModel):
    attempt_id: str
    question_id: int
    addressed_concepts: list[str]
    score: float
    gaps: list[str]
    ask_follow_up: bool
    follow_up_id: int | None = None
    follow_up_prompt: FollowUpOut | None = None
    next_question: QuestionOut | None = None
    is_session_complete: bool = False
    session_outcome: str | None = None


class FollowUpEvaluationOut(BaseModel):
    attempt_id: str
    follow_up_addressed: bool
    follow_up_score: float
    next_question: QuestionOut | None = None
    is_session_complete: bool = False
    session_outcome: str | None = None


class ReportResponse(BaseModel):
    session_id: str
    topic_name: str
    target_level: int
    outcome: str
    report_markdown: str
