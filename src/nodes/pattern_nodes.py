"""
Pattern analysis nodes
"""

from langchain_core.messages import SystemMessage, HumanMessage

from src.models import PatternState
from src.prompts import PATTERN_ANALYSIS_SYSTEM_PROMPT
from src.core import chat_llm
from config.auth import supabase


def collect_patterns_node(state: PatternState) -> PatternState:
    """Analyze mistake patterns across all topics"""
    
    try:
        result = supabase.rpc('get_pattern_analysis', {}).execute()
        
        patterns = []
        for row in result.data:
            patterns.append({
                "pattern": row['pattern'],
                "affected_topics": 1,
                "occurrences": row['frequency'],
                "avg_days_between": round(float(row['avg_days_between']), 1) if row['avg_days_between'] else None
            })
        
        return {
            **state,
            "patterns": patterns
        }
                
    except Exception as e:
        return {
            **state,
            "error": f"Pattern collection failed: {str(e)}",
            "patterns": []
        }


def analyze_patterns_node(state: PatternState) -> PatternState:
    """Generate insights from recurring mistake patterns using LLM"""
    
    patterns = state.get("patterns", [])
    
    if not patterns:
        return {
            **state,
            "insights": "No significant patterns detected in recent learning activity."
        }
    
    try:
        pattern_text = "\n".join([
            f"- {p['pattern']}: {p['occurrences']} times across {p['affected_topics']} topics" +
            (f", roughly every {p['avg_days_between']} days" if p['avg_days_between'] else "")
            for p in patterns
        ])
        
        response = chat_llm.invoke([
            SystemMessage(content=PATTERN_ANALYSIS_SYSTEM_PROMPT),
            HumanMessage(content=f"Recurring patterns:\n{pattern_text}")
        ])
        
        return {
            **state,
            "insights": response.content
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Pattern analysis failed: {str(e)}",
            "insights": "Unable to generate insights at this time."
        }
