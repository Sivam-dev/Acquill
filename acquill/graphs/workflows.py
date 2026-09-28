"""
LangGraph workflow definitions - single consolidated file
"""

from langgraph.graph import StateGraph, END
from acquill.models import LearningState, ReminderState, DigestState, PatternState
from acquill.nodes.chat_nodes import (
    init_state_node,
    extract_event_node,
    analyze_diff_node,
    store_event_node,
    check_dependencies_node,
    retrieve_similar_node,
    generate_reply_node,
)
from acquill.nodes.reminder_nodes import (
    check_reminders_node,
    generate_quiz_node,
    send_reminder_node,
)
from acquill.nodes.digest_nodes import (
    collect_digest_data_node,
    generate_digest_node,
)
from acquill.nodes.pattern_nodes import (
    collect_patterns_node,
    analyze_patterns_node,
)


def build_chat_graph():
    """Build the main chat processing graph with dependency checking"""
    workflow = StateGraph(LearningState)
    workflow.add_node("init", init_state_node)
    workflow.add_node("extract", extract_event_node)
    workflow.add_node("store", store_event_node)
    workflow.add_node("check_dependencies", check_dependencies_node)
    workflow.add_node("retrieve", retrieve_similar_node)
    workflow.add_node("generate", generate_reply_node)
    workflow.set_entry_point("init")
    workflow.add_edge("init", "extract")
    workflow.add_edge("extract", "store")
    workflow.add_edge("store", "check_dependencies")
    workflow.add_edge("check_dependencies", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


def build_diff_graph():
    """Build the diff analysis graph"""
    workflow = StateGraph(LearningState)
    workflow.add_node("analyze", analyze_diff_node)
    workflow.add_node("store", store_event_node)
    workflow.add_node("check_dependencies", check_dependencies_node)
    workflow.add_node("retrieve", retrieve_similar_node)
    workflow.add_node("generate", generate_reply_node)
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "store")
    workflow.add_edge("store", "check_dependencies")
    workflow.add_edge("check_dependencies", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


def build_reminder_graph():
    """Build the reminder checking graph with quiz generation"""
    workflow = StateGraph(ReminderState)
    workflow.add_node("check", check_reminders_node)
    workflow.add_node("quiz", generate_quiz_node)
    workflow.add_node("send", send_reminder_node)
    workflow.set_entry_point("check")
    workflow.add_edge("check", "quiz")
    workflow.add_edge("quiz", "send")
    workflow.add_edge("send", END)
    return workflow.compile()


def build_digest_graph():
    """Build the weekly digest generation graph"""
    workflow = StateGraph(DigestState)
    workflow.add_node("collect", collect_digest_data_node)
    workflow.add_node("generate", generate_digest_node)
    workflow.set_entry_point("collect")
    workflow.add_edge("collect", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


def build_pattern_graph():
    """Build the pattern analysis graph"""
    workflow = StateGraph(PatternState)
    workflow.add_node("collect", collect_patterns_node)
    workflow.add_node("analyze", analyze_patterns_node)
    workflow.set_entry_point("collect")
    workflow.add_edge("collect", "analyze")
    workflow.add_edge("analyze", END)
    return workflow.compile()
