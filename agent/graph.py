from langgraph.graph import StateGraph, START, END
from agent.utils.state import DocumentState
from agent.utils.nodes import (
    decide_split,
    split_into_chunks,
    generate_xmindmark_direct,
    generate_all_chunks_parallel,
    merge_all_xmindmarks,
    generate_global_title_node,
    process_audio_input,
    generate_xmindmark_from_audio_node,
)
from core.llm_handle import generate_xmindmark_with_search
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def build_graph():
    builder = StateGraph(DocumentState)
    builder.add_node("check_split", decide_split)
    builder.add_node("generate_global_title", generate_global_title_node)
    builder.add_node("split_chunks", split_into_chunks)
    builder.add_node("generate_direct", generate_xmindmark_direct)
    builder.add_node("process_chunks_parallel", generate_all_chunks_parallel)
    builder.add_node("merge_xmind", merge_all_xmindmarks)
    builder.add_node("generate_with_search", generate_with_search_node)
    builder.add_node("process_audio", process_audio_input)
    builder.add_node("generate_from_audio", generate_xmindmark_from_audio_node)
    
    def route_from_start(state: DocumentState):
        if state.get("audio_file"):
            return "process_audio"
        else:
            return "check_split"
        
    builder.add_conditional_edges(
        START,
        route_from_start,
        {
            "process_audio": "process_audio",
            "check_split": "check_split"
        }
    )
    builder.add_edge("process_audio", "check_split")

    def route_after_split(state: DocumentState):
        if state["need_split"]:
            return "split_chunks"
        else:
            if state.get("search_mode", False):
                return "generate_with_search"
            elif state.get("audio_processed", False):
                return "generate_from_audio"
            else:
                return "generate_direct"

    builder.add_conditional_edges(
        "check_split",
        route_after_split,
        {
            "split_chunks": "split_chunks",
            "generate_direct": "generate_direct",
            "generate_with_search": "generate_with_search",
            "generate_from_audio": "generate_from_audio"
        }
    )

    builder.add_edge("split_chunks", "generate_global_title")
    builder.add_edge("generate_global_title", "process_chunks_parallel")
    builder.add_edge("process_chunks_parallel", "merge_xmind")
    builder.add_edge("generate_with_search", END)
    builder.add_edge("generate_direct", END)
    builder.add_edge("generate_from_audio", END)
    builder.add_edge("merge_xmind", END)

    return builder.compile()

def generate_with_search_node(state: DocumentState) -> DocumentState:
    try:
        xmindmark = ""
        for chunk in generate_xmindmark_with_search(
            state["user_requirements"],
            state.get("conversation_history")
        ):
            xmindmark += chunk
        state["xmindmark_final"] = xmindmark
        state["chunk_processing_status"] = "completed"
        state["last_search_time"] = datetime.now().isoformat()
    except Exception as e:
        logger.error(f"Search node failed: {e}")
        state["xmindmark_final"] = f"Error: {str(e)}"
        state["chunk_processing_status"] = "failed"
    return state

