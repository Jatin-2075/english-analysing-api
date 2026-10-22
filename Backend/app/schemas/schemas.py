from pydantic import BaseModel, Field


class WordFeedbackCreate(BaseModel):
    original_word: str = Field(min_length=1, max_length=255)
    suggested_word: str | None = None
    confirmed_word: str | None = None
    accepted: bool | None = None
    context: str | None = None
    is_name: bool = False


class AssessmentFeedbackCreate(BaseModel):
    assessment_id: str = Field(min_length=1, max_length=100)
    rating: int = Field(ge=1, le=5)
    original_score: float | None = Field(default=None, ge=0, le=100)
    suggested_score: float | None = Field(default=None, ge=0, le=100)
    reason: str | None = None


class DictionaryWordCreate(BaseModel):
    word: str = Field(min_length=1, max_length=255)
