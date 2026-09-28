"""
Pydantic models for structured LLM outputs
"""

from pydantic import BaseModel


class ExtractedEvent(BaseModel):
    """Structured event extracted from user message"""
    topic: str
    event_type: str
    detail: str


class DiffAnalysis(BaseModel):
    """Analysis of a git diff"""
    topic: str
    event_type: str
    detail: str
    confidence: float


class QuizQuestion(BaseModel):
    """Quiz question generated from past struggles"""
    question: str
    hint: str
    learning_point: str
