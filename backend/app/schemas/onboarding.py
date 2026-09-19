from typing import Literal
from pydantic import BaseModel, Field, field_validator


class TopicSelectionSchema(BaseModel):
    topic_id: int
    self_assessment: Literal["beginner", "intermediate", "advanced"]


class AcademicInfoSchema(BaseModel):
    college_year: str = Field(..., min_length=1, max_length=50)
    stream: str = Field(..., min_length=1, max_length=100)


class OnboardingRequestSchema(BaseModel):
    topic_selections: list[TopicSelectionSchema]
    academic_info: AcademicInfoSchema
    goal: str | None = None
    timezone: str = Field(default="UTC", min_length=1, max_length=50)

    @field_validator("topic_selections")
    @classmethod
    def validate_topics_length_and_uniqueness(
        cls, value: list[TopicSelectionSchema]
    ) -> list[TopicSelectionSchema]:
        if len(value) < 3:
            raise ValueError("You must select at least 3 topics.")
        topic_ids = [t.topic_id for t in value]
        if len(topic_ids) != len(set(topic_ids)):
            raise ValueError("Duplicate topic selections are not allowed.")
        return value


class OnboardingResponseSchema(BaseModel):
    success: bool
    message: str
    student_id: str
    topics_count: int
