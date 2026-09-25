"""
Digest generation nodes for progress summaries
"""

import json
from datetime import datetime, timedelta
from langchain_core.messages import SystemMessage, HumanMessage

from src.models import DigestState
from src.prompts import DIGEST_SYSTEM_PROMPT
from src.core import chat_llm
from config.auth import supabase


def collect_digest_data_node(state: DigestState) -> DigestState:
    """Collect learning data for the specified time period"""
    
    try:
        start_date = state.get("start_date", (datetime.now() - timedelta(days=7)).isoformat())
        end_date = state.get("end_date", datetime.now().isoformat())
        
        result = supabase.rpc('get_digest_data', {
            'p_start_date': start_date,
            'p_end_date': end_date
        }).execute()
        
        topics_touched = 0
        confidence_changes = {}
        
        if result.data:
            topics_touched = result.data[0]['topics_touched'] if result.data else 0
            for row in result.data:
                if row['topic_name']:
                    confidence_changes[row['topic_name']] = row['confidence_score']
        
        struggles_result = supabase.rpc('get_recurring_struggles', {
            'p_start_date': start_date,
            'p_end_date': end_date
        }).execute()
        
        recurring_struggles = [
            {"topic": row['topic_name'], "count": row['struggle_count']}
            for row in struggles_result.data
        ]
        
        return {
            **state,
            "start_date": start_date,
            "end_date": end_date,
            "topics_touched": topics_touched,
            "confidence_changes": confidence_changes,
            "recurring_struggles": recurring_struggles
        }
                
    except Exception as e:
        return {
            **state,
            "error": f"Data collection failed: {str(e)}"
        }


def generate_digest_node(state: DigestState) -> DigestState:
    """Generate a human-readable progress digest using LLM"""
    
    if state.get("error"):
        return state
    
    topics_touched = state.get("topics_touched", 0)
    confidence_changes = state.get("confidence_changes", {})
    recurring_struggles = state.get("recurring_struggles", [])
    
    try:
        user_content = f"""Period: {state['start_date']} to {state['end_date']}

Topics touched: {topics_touched}
Confidence levels: {json.dumps(confidence_changes)}
Recurring struggles: {json.dumps(recurring_struggles)}"""
        
        response = chat_llm.invoke([
            SystemMessage(content=DIGEST_SYSTEM_PROMPT),
            HumanMessage(content=user_content)
        ])
        
        return {
            **state,
            "digest": response.content
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Digest generation failed: {str(e)}"
        }
