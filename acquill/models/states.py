"""
State definitions for LangGraph workflows
"""

from typing import TypedDict, Optional, List, Dict


class LearningState(TypedDict):
    """State for the main chat processing graph"""
    user_message: Optional[str]
    diff: Optional[str]
    filepath: Optional[str]
    topic: Optional[str]
    event_type: Optional[str]
    detail: Optional[str]
    confidence: Optional[float]
    skip_storage: Optional[bool]
    topic_id: Optional[str]
    weak_prerequisites: Optional[List[Dict]]
    retrieved_docs: Optional[List[Dict]]
    reply: Optional[str]
    error: Optional[str]


class ReminderState(TypedDict):
    """State for the reminder checking graph"""
    overdue_topics: Optional[List[Dict]]
    reminder_message: Optional[str]
    quiz_questions: Optional[List[Dict]]
    error: Optional[str]


class DigestState(TypedDict):
    """State for weekly digest generation"""
    start_date: Optional[str]
    end_date: Optional[str]
    topics_touched: Optional[int]
    confidence_changes: Optional[Dict[str, float]]
    recurring_struggles: Optional[List[Dict]]
    digest: Optional[str]
    error: Optional[str]


class PatternState(TypedDict):
    """State for pattern analysis"""
    patterns: Optional[List[Dict]]
    insights: Optional[str]
    error: Optional[str]
