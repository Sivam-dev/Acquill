"""
Chat processing nodes for the learning graph
"""

import logging
from datetime import datetime, timedelta
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from acquill.models import LearningState, ExtractedEvent, DiffAnalysis
from acquill.prompts import (
    EXTRACT_SYSTEM_PROMPT_STRUCTURED,
    DIFF_ANALYSIS_PROMPT_STRUCTURED,
    REPLY_SYSTEM_PROMPT,
    QUIZ_CODING_PROMPT
)
from acquill.core import embeddings, extract_llm, diff_analysis_llm, reply_llm, quiz_llm
from acquill.core.dsa_map import canonical, prerequisites
from acquill.config.auth import supabase

logger = logging.getLogger(__name__)


def init_state_node(state: LearningState) -> LearningState:
    """Initialize state with default values"""
    return {
        **state,
        "skip_storage": False,
        "weak_prerequisites": [],
        "retrieved_docs": [],
        "error": None
    }


def extract_event_node(state: LearningState) -> LearningState:
    """Extract structured event data from user message using LLM"""
    
    if state.get("error"):
        return state
    
    user_message = state.get("user_message")
    if not user_message:
        return {
            **state,
            "error": "No user message provided"
        }
    
    try:
        structured_llm = extract_llm.with_structured_output(ExtractedEvent)
        
        response = structured_llm.invoke([
            SystemMessage(content=EXTRACT_SYSTEM_PROMPT_STRUCTURED),
            HumanMessage(content=user_message)
        ])
        
        return {
            **state,
            "topic": response.topic,
            "event_type": response.event_type,
            "detail": response.detail,
            "confidence": 1.0
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Extraction failed: {str(e)}"
        }


def analyze_diff_node(state: LearningState) -> LearningState:
    """Analyze git diff to extract learning event"""
    
    if state.get("error"):
        return state
    
    diff = state.get("diff")
    filepath = state.get("filepath", "unknown")
    
    if not diff:
        return {
            **state,
            "error": "No diff provided"
        }
    
    try:
        structured_llm = diff_analysis_llm.with_structured_output(DiffAnalysis)
        
        user_content = f"File: {filepath}\n\nDiff:\n{diff}"
        
        response = structured_llm.invoke([
            SystemMessage(content=DIFF_ANALYSIS_PROMPT_STRUCTURED),
            HumanMessage(content=user_content)
        ])
        
        skip_storage = response.confidence < 0.7 or response.event_type == "neutral"
        
        return {
            **state,
            "topic": response.topic,
            "event_type": response.event_type if not skip_storage else "neutral",
            "detail": response.detail,
            "confidence": response.confidence,
            "skip_storage": skip_storage
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Diff analysis failed: {str(e)}",
            "skip_storage": True
        }


def _dependency_status(events):
    """Classify a prerequisite from its event history."""
    struggles = [e["created_at"] for e in events if e["event_type"] == "struggled"]
    solves = [e["created_at"] for e in events if e["event_type"] == "solved"]

    if struggles and (not solves or max(struggles) > max(solves)):
        return "unresolved"
    if solves:
        return "resolved"
    if events:
        return "seen"
    return "new"


def _has_solved(events):
    return any(e["event_type"] == "solved" for e in events)


def check_dependencies_node(state: LearningState) -> LearningState:
    """Warn about weak prerequisites when the user starts a new topic."""
    
    if state.get("error") or state.get("skip_storage"):
        return state
    
    topic = canonical(state.get("topic"))
    if not topic:
        return {**state, "weak_prerequisites": []}
    
    deps = prerequisites(topic, depth=1)
    if not deps:
        return {**state, "weak_prerequisites": []}
    
    try:
        topics = supabase.table("topics").select(
            "id, name, confidence_score, next_review_at"
        ).execute().data or []
        
        by_name = {}
        for row in topics:
            key = canonical(row.get("name"))
            if key and key not in by_name:
                by_name[key] = row
        
        dep_rows = {d: by_name[d] for d in deps if d in by_name}
        if not dep_rows:
            return {**state, "weak_prerequisites": []}
        
        current = by_name.get(topic)
        ids = [row["id"] for row in dep_rows.values()]
        if current:
            ids.append(current["id"])
        
        events = supabase.table("topic_history").select(
            "topic_id, event_type, created_at"
        ).in_("topic_id", ids).order("created_at", desc=True).limit(500).execute().data or []
        
        by_topic = {}
        for event in events:
            by_topic.setdefault(event["topic_id"], []).append(event)
        
        current_events = by_topic.get(current["id"], []) if current else []
        if current and (len(current_events) > 1 or _has_solved(current_events)):
            return {**state, "weak_prerequisites": []}
        
        weak = []
        for name, row in dep_rows.items():
            status = _dependency_status(by_topic.get(row["id"], []))
            if status in ("unresolved", "seen"):
                weak.append({
                    "name": name,
                    "status": status,
                    "confidence": row["confidence_score"],
                    "next_review_at": row.get("next_review_at")
                })
        
        return {**state, "weak_prerequisites": weak}
        
    except Exception:
        logger.warning("dependency check failed", exc_info=True)
        return {**state, "weak_prerequisites": []}


def store_event_node(state: LearningState) -> LearningState:
    """Store event in database"""
    
    if state.get("error"):
        return state
    
    if state.get("skip_storage"):
        return {
            **state,
            "topic_id": None
        }
    
    topic_name = state["topic"]
    event_type = state["event_type"]
    detail = state["detail"]

    try:
        user_resp = supabase.auth.get_user()
        user = getattr(user_resp, "user", None)
        user_id = getattr(user, "id", None)
        if not user_id:
            return {
                **state,
                "error": "Not logged in: cannot save learning event"
            }

        result = supabase.table('topics').select('id, confidence_score, review_interval_days').eq('name', topic_name).execute()
        
        if result.data:
            topic_id = result.data[0]['id']
            current_confidence = result.data[0]['confidence_score']
            review_interval = result.data[0]['review_interval_days']
        else:
            new_topic = supabase.table('topics').insert({
                'name': topic_name,
                'user_id': user_id,
                'confidence_score': 0.0,
                'review_interval_days': 1
            }).execute()
            topic_id = new_topic.data[0]['id']
            current_confidence = 0.0
            review_interval = 1
        
        supabase.table('topic_history').insert({
            'topic_id': topic_id,
            'user_id': user_id,
            'event_type': event_type,
            'details': detail
        }).execute()
        
        if event_type == "solved":
            new_confidence = min(100.0, current_confidence + 10.0)
            new_interval = min(30, review_interval * 2)
            next_review = (datetime.now() + timedelta(days=new_interval)).isoformat()
            
            supabase.table('topics').update({
                'confidence_score': new_confidence,
                'last_touched_at': datetime.now().isoformat(),
                'next_review_at': next_review,
                'review_interval_days': new_interval
            }).eq('id', topic_id).execute()
            
        elif event_type == "struggled":
            new_confidence = max(0.0, current_confidence - 5.0)
            next_review = (datetime.now() + timedelta(days=1)).isoformat()
            
            supabase.table('topics').update({
                'confidence_score': new_confidence,
                'last_touched_at': datetime.now().isoformat(),
                'next_review_at': next_review,
                'review_interval_days': 1
            }).eq('id', topic_id).execute()
            
        else:
            supabase.table('topics').update({
                'last_touched_at': datetime.now().isoformat()
            }).eq('id', topic_id).execute()
        
        embedding_vector = embeddings.embed_query(detail)
        
        supabase.table('documents').insert({
            'topic_id': topic_id,
            'user_id': user_id,
            'content': detail,
            'embedding': embedding_vector
        }).execute()
        
        return {
            **state,
            "topic_id": str(topic_id)
        }
                
    except Exception as e:
        return {
            **state,
            "error": f"Storage failed: {str(e)}"
        }


def retrieve_similar_node(state: LearningState) -> LearningState:
    """Retrieve similar past experiences using vector search"""
    
    if state.get("error"):
        return state
    
    if state["event_type"] == "solved":
        return {
            **state,
            "retrieved_docs": []
        }
    
    topic_id = state["topic_id"]
    detail = state["detail"]
    
    try:
        query_embedding = embeddings.embed_query(detail)
        
        result = supabase.rpc('match_documents', {
            'query_embedding': query_embedding,
            'match_topic_id': topic_id,
            'match_count': 3
        }).execute()
        
        retrieved_docs = [
            {"content": row['content'], "similarity": row['similarity']} 
            for row in result.data
        ]
        
        return {
            **state,
            "retrieved_docs": retrieved_docs
        }
                
    except Exception as e:
        return {
            **state,
            "error": f"Retrieval failed: {str(e)}",
            "retrieved_docs": []
        }


def _coding_question(topic_name):
    """Generate one short coding question for a weak prerequisite."""
    try:
        response = quiz_llm.invoke([
            SystemMessage(content=QUIZ_CODING_PROMPT.format(topic=topic_name)),
            HumanMessage(content=f"Give me one coding question about {topic_name}.")
        ])
        return response.content.strip()
    except Exception:
        logger.warning("warm-up question generation failed", exc_info=True)
        return None


def generate_reply_node(state: LearningState) -> LearningState:
    """Generate empathetic reply based on event type and context"""
    
    if state.get("error"):
        return {
            **state,
            "reply": f"I encountered an issue: {state['error']}"
        }
    
    if state.get("skip_storage"):
        return {
            **state,
            "reply": None
        }
    
    topic = state["topic"]
    event_type = state["event_type"]
    detail = state["detail"]
    weak_prerequisites = state.get("weak_prerequisites", [])
    retrieved_docs = state.get("retrieved_docs", [])
    
    try:
        context_parts = [f"Topic: {topic}", f"Event: {event_type}", f"Detail: {detail}"]
        
        if weak_prerequisites:
            prereq_text = "\n".join([
                f"- {p['name']} ({p.get('status', 'weak')}, confidence: {p.get('confidence', 0)})"
                for p in weak_prerequisites
            ])
            context_parts.append(f"\nWeak prerequisites:\n{prereq_text}")
        
        if retrieved_docs:
            similar_text = "\n".join([
                f"- {doc['content']} (similarity: {doc['similarity']:.2f})"
                for doc in retrieved_docs
            ])
            context_parts.append(f"\nSimilar past experiences:\n{similar_text}")
        
        context = "\n\n".join(context_parts)
        
        history = state.get("messages") or []
        response = reply_llm.invoke([
            SystemMessage(content=REPLY_SYSTEM_PROMPT),
            *history,
            HumanMessage(content=context)
        ])
        
        reply_text = response.content
        if weak_prerequisites and state.get("user_message"):
            warmup = weak_prerequisites[0]
            question = _coding_question(warmup["name"])
            if question:
                reply_text = (
                    f"{reply_text}\n\n"
                    f"📝 **Quick warm-up ({warmup['name']}):**\n{question}"
                )
        
        update = {
            **state,
            "reply": reply_text
        }
        if state.get("user_message"):
            update["messages"] = [
                HumanMessage(content=state["user_message"]),
                AIMessage(content=reply_text)
            ]
        return update
        
    except Exception as e:
        return {
            **state,
            "reply": "I'm here with you, but I'm having trouble forming a response right now."
        }
