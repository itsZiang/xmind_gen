from agent.graph import build_graph
import time
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def generate_xmindmark_langgraph(text: str, user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    start_time = time.time()
    graph = build_graph()
    
    try:
        response = graph.invoke({
            "input_text": f"""{text}""",
            "user_requirements": f"""{user_requirements}""",
            "conversation_history": conversation_history or [],
            "need_split": False,
            "chunks": [],
            "xmindmark_chunks_content": [],
            "xmindmark_final": "",
            "global_title": "",
            "chunk_processing_status": "pending"
        })
        
        processing_time = time.time() - start_time
        logger.info(f"LangGraph processing completed in {processing_time:.2f}s")
        return response["xmindmark_final"]
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"LangGraph processing failed after {processing_time:.2f}s: {e}")
        raise e

async def generate_xmindmark_langgraph_stream(text: str, user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None):
    graph = build_graph()
    async for event in graph.astream_events({
        "input_text": f"""{text}""",
        "user_requirements": f"""{user_requirements}""",
        "conversation_history": conversation_history or [],
        "need_split": False,
        "chunks": [],
        "xmindmark_chunks_content": [],
        "xmindmark_final": "",
        "global_title": "",
        "chunk_processing_status": "pending"
    }, version="v2"):
        if (event["event"] == "on_chat_model_stream" and
            event.get("metadata", {}).get('langgraph_node','') in ["merge_xmind", "generate_direct"]):
            data = event.get("data", {})
            if "chunk" in data:
                yield data["chunk"].content