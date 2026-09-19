from pydantic import BaseModel


class TopicOut(BaseModel):
    id: int
    name: str
    current_level: int | None = None

    class Config:
        from_attributes = True
