"""
Reminder and quiz generation nodes
"""

from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from acquill.schemas import ReminderState
from acquill.prompts import QUIZ_CODING_PROMPT
from acquill.models import llm
from acquill.config.auth import supabase


def _time_since(iso_timestamp) -> str:
    """Human-friendly gap since a timestamp, e.g. '3 days', '2 hours'.

    The app writes last_touched_at with datetime.now().isoformat(), so the
    stored wall-clock time is local; compare against local now.
    """
    if not iso_timestamp:
        return "a while"

    try:
        then = datetime.fromisoformat(str(iso_timestamp).replace("Z", "+00:00"))
    except ValueError:
        return "a while"

    delta = datetime.now() - then.replace(tzinfo=None)
    if delta.total_seconds() < 0:
        return "just now"

    days = delta.days
    if days >= 1:
        return f"{days} day{'s' if days != 1 else ''}"

    hours = delta.seconds // 3600
    if hours >= 1:
        return f"{hours} hour{'s' if hours != 1 else ''}"

    minutes = max(delta.seconds // 60, 1)
    return f"{minutes} minute{'s' if minutes != 1 else ''}"


def check_reminders_node(state: ReminderState) -> ReminderState:
    """Check for topics that need review"""
    
    try:
        result = supabase.table('topics').select(
            'id, name, confidence_score, next_review_at, last_touched_at'
        ).not_.is_('next_review_at', 'null').lt(
            'next_review_at', datetime.now().isoformat()
        ).order('next_review_at', desc=False).limit(10).execute()
        
        overdue_topics = []
        for row in result.data:
            overdue_topics.append({
                "id": row['id'],
                "name": row['name'],
                "confidence_score": row['confidence_score'],
                "next_review_at": row['next_review_at'],
                "last_touched_at": row['last_touched_at']
            })
        
        return {
            **state,
            "overdue_topics": overdue_topics
        }
                
    except Exception as e:
        return {
            **state,
            "error": f"Reminder check failed: {str(e)}",
            "overdue_topics": []
        }


def generate_quiz_node(state: ReminderState) -> ReminderState:
    """Generate ONE coding question from the most recent struggle"""
    
    overdue_topics = state.get("overdue_topics", [])
    
    if not overdue_topics:
        return {**state, "quiz_questions": []}
    
    try:
        for topic in overdue_topics:
            result = supabase.table('topic_history').select('details').eq(
                'topic_id', topic["id"]
            ).eq('event_type', 'struggled').order(
                'created_at', desc=True
            ).limit(3).execute()
            
            struggles = [row['details'] for row in result.data]
            
            if not struggles:
                continue
            
            mistakes_text = "\n".join(f"- {s}" for s in struggles)
            
            response = llm.invoke([
                SystemMessage(content=QUIZ_CODING_PROMPT.format(topic=topic["name"])),
                HumanMessage(content=f"Past mistakes:\n{mistakes_text}")
            ])
            
            return {
                **state,
                "quiz_questions": [{
                    "topic": topic["name"],
                    "topic_id": topic["id"],
                    "question": response.content.strip()
                }]
            }
        
        return {**state, "quiz_questions": []}
        
    except Exception as e:
        return {
            **state,
            "error": f"Quiz generation failed: {str(e)}",
            "quiz_questions": []
        }


def send_reminder_node(state: ReminderState) -> ReminderState:
    """Format and return the reminder message"""
    
    overdue_topics = state.get("overdue_topics", [])
    quiz_questions = state.get("quiz_questions", [])
    
    if not overdue_topics:
        return {
            **state,
            "reminder_message": None
        }
    
    message_parts = ["⏰ **Time to review these topics:**\n"]
    
    for topic in overdue_topics:
        touched = _time_since(topic.get("last_touched_at"))
        message_parts.append(
            f"- **{topic['name']}** (confidence: {topic['confidence_score']:.0f}%, "
            f"not touched for {touched})"
        )
    
    if quiz_questions:
        quiz = quiz_questions[0]
        message_parts.append("\n📝 **Coding warm-up:**\n")
        message_parts.append(f"**{quiz['topic']}:** {quiz['question']}")
    
    return {
        **state,
        "reminder_message": "\n".join(message_parts)
    }
