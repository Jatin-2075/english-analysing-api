from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)

from ..database.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class WordFeedback(Base):
    __tablename__ = "word_feedback"

    id = Column(Integer, primary_key=True, index=True)
    original_word = Column(String(255), nullable=False)
    suggested_word = Column(String(255), nullable=True)
    confirmed_word = Column(String(255), nullable=True)
    accepted = Column(Boolean, nullable=True)
    context = Column(Text, nullable=True)
    is_name = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class AssessmentFeedback(Base):
    __tablename__ = "assessment_feedback"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(String(100), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    original_score = Column(Float, nullable=True)
    suggested_score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class DictionaryWord(Base):
    __tablename__ = "dictionary_words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(255), nullable=False)
    normalized_word = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
