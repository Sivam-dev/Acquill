"""
Public API for LearningTrack/Acquill
Convenience functions for external use
"""

from typing import Dict, Optional
from datetime import datetime, timedelta

from acquill.models import LearningState, ReminderState, DigestState, PatternState
from acquill.graphs.workflows import (
    build_chat_graph,
    build_diff_graph,
    build_reminder_graph,
    build_digest_graph,
    build_pattern_graph,
)


def process_message(user_message: str) -> Dict:
    """Process a user message through the main chat graph"""
    
    chat_graph = build_chat_graph()
    
    initial_state = LearningState(
        user_message=user_message,
        diff=None,
        filepath=None,
        topic=None,
        event_type=None,
        detail=None,
        confidence=None,
        skip_storage=False,
        topic_id=None,
        weak_prerequisites=None,
        retrieved_docs=None,
        reply=None,
        error=None
    )
    
    result = chat_graph.invoke(initial_state)
    
    return {
        "reply": result.get("reply"),
        "topic": result.get("topic"),
        "event_type": result.get("event_type"),
        "error": result.get("error")
    }


def process_diff(diff: str, filepath: str) -> Dict:
    """Process a git diff through the diff analysis path"""
    
    diff_graph = build_diff_graph()
    
    initial_state = LearningState(
        user_message=None,
        diff=diff,
        filepath=filepath,
        topic=None,
        event_type=None,
        detail=None,
        confidence=None,
        skip_storage=False,
        topic_id=None,
        weak_prerequisites=None,
        retrieved_docs=None,
        reply=None,
        error=None
    )
    
    result = diff_graph.invoke(initial_state)
    
    return {
        "reply": result.get("reply"),
        "topic": result.get("topic"),
        "event_type": result.get("event_type"),
        "confidence": result.get("confidence", 0.0),
        "filepath": filepath,
        "error": result.get("error")
    }


def check_and_send_reminders() -> Optional[str]:
    """Check for overdue topics and generate reminder with quizzes"""
    
    reminder_graph = build_reminder_graph()
    
    initial_state = ReminderState(
        overdue_topics=None,
        reminder_message=None,
        quiz_questions=None,
        error=None
    )
    
    result = reminder_graph.invoke(initial_state)
    return result.get("reminder_message")


def generate_weekly_digest(days=7) -> Optional[str]:
    """Generate a progress digest for the last N days"""
    
    digest_graph = build_digest_graph()
    
    initial_state = DigestState(
        start_date=(datetime.now() - timedelta(days=days)).isoformat(),
        end_date=datetime.now().isoformat(),
        topics_touched=None,
        confidence_changes=None,
        recurring_struggles=None,
        digest=None,
        error=None
    )
    
    result = digest_graph.invoke(initial_state)
    return result.get("digest")


def analyze_learning_patterns() -> Optional[str]:
    """Analyze recurring mistake patterns across all topics"""
    
    pattern_graph = build_pattern_graph()
    
    initial_state = PatternState(
        patterns=None,
        insights=None,
        error=None
    )
    
    result = pattern_graph.invoke(initial_state)
    return result.get("insights")
