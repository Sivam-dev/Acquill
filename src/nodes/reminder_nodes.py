"""
Reminder and quiz generation nodes
"""

from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from src.models import ReminderState, QuizQuestion
from src.prompts import QUIZ_SYSTEM_PROMPT_STRUCTURED
from src.core import chat_llm
from config.auth import supabase


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
    """Generate quiz questions based on past struggles"""
    
    overdue_topics = state.get("overdue_topics", [])
    
    if not overdue_topics:
        return {**state, "quiz_questions": []}
    
    quiz_questions = []
    
    try:
        for topic in overdue_topics[:3]:
            result = supabase.table('topic_history').select('details').eq(
                'topic_id', topic["id"]
            ).eq('event_type', 'struggled').order(
                'created_at', desc=True
            ).limit(3).execute()
            
            struggles = [row['details'] for row in result.data]
            
            if struggles:
                structured_llm = chat_llm.with_structured_output(QuizQuestion)
                system_prompt = QUIZ_SYSTEM_PROMPT_STRUCTURED.format(topic=topic["name"])
                mistakes_text = "\n".join(f"- {s}" for s in struggles)
                
                response = structured_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Past mistakes:\n{mistakes_text}")
                ])
                
                quiz_questions.append({
                    "topic": topic["name"],
                    "topic_id": topic["id"],
                    "question": response.question,
                    "hint": response.hint,
                    "learning_point": response.learning_point
                })
        
        return {
            **state,
            "quiz_questions": quiz_questions
        }
        
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
        message_parts.append(
            f"- **{topic['name']}** (confidence: {topic['confidence_score']:.0f}%)"
        )
    
    if quiz_questions:
        message_parts.append("\n📝 **Quick quiz to refresh your memory:**\n")
        for i, quiz in enumerate(quiz_questions, 1):
            message_parts.append(f"\n**Q{i} ({quiz['topic']}):** {quiz['question']}")
            message_parts.append(f"💡 Hint: {quiz['hint']}")
    
    return {
        **state,
        "reminder_message": "\n".join(message_parts)
    }
