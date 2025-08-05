# agent/utils/nodes.py

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import logging
from agent.utils.state import DocumentState
from agent.utils.tools import check_need_split, split_text, merge_xmindmarks
from core.llm_handle import generate_xmindmark, generate_global_title

logger = logging.getLogger(__name__)

def decide_split(state: DocumentState) -> DocumentState:
    state["need_split"] = check_need_split(state["input_text"])
    return state

def split_into_chunks(state: DocumentState) -> DocumentState:
    state["chunks"] = split_text(state["input_text"], state["user_requirements"], state.get("conversation_history"))
    state["xmindmark_chunks_content"] = []
    state["chunk_processing_status"] = "pending"
    return state

async def process_chunks_parallel(chunks: List[str], user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> List[str]:
    max_workers = min(len(chunks), 4)
    
    def process_single_chunk(chunk_data):
        chunk_index, chunk_content = chunk_data
        try:
            logger.info(f"Processing chunk {chunk_index + 1}/{len(chunks)}")
            result = generate_xmindmark(chunk_content, user_requirements, conversation_history)
            return chunk_index, result
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_index}: {e}")
            return chunk_index, f"Error processing chunk: {str(e)}"
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        chunk_data = [(i, chunk) for i, chunk in enumerate(chunks)]
        future_to_chunk = {
            executor.submit(process_single_chunk, data): data[0]
            for data in chunk_data
        }
        
        results = {}
        for future in as_completed(future_to_chunk):
            chunk_index = future_to_chunk[future]
            try:
                idx, result = future.result()
                results[idx] = result
                logger.info(f"Completed chunk {idx + 1}/{len(chunks)}")
            except Exception as e:
                logger.error(f"Chunk {chunk_index} generated exception: {e}")
                results[chunk_index] = f"Error: {str(e)}"
    
    ordered_results = [results[i] for i in sorted(results.keys())]
    return ordered_results

def generate_all_chunks_parallel(state: DocumentState) -> DocumentState:
    try:
        chunks = state["chunks"]
        user_requirements = state["user_requirements"]
        conversation_history = state.get("conversation_history")
        
        logger.info(f"Starting parallel processing of {len(chunks)} chunks")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                process_chunks_parallel(chunks, user_requirements, conversation_history)
            )
            state["xmindmark_chunks_content"] = results
            state["chunk_processing_status"] = "completed"
            logger.info("Parallel processing completed successfully")
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Parallel processing failed: {e}")
        state["chunk_processing_status"] = "failed"
        state["xmindmark_chunks_content"] = []
        for i, chunk in enumerate(state["chunks"]):
            try:
                result = generate_xmindmark(chunk, state["user_requirements"], state.get("conversation_history"))
                state["xmindmark_chunks_content"].append(result)
                logger.info(f"Fallback: processed chunk {i+1}/{len(state['chunks'])}")
            except Exception as chunk_error:
                logger.error(f"Fallback failed for chunk {i}: {chunk_error}")
                state["xmindmark_chunks_content"].append(f"Error: {str(chunk_error)}")
    
    return state

def generate_xmindmark_direct(state: DocumentState) -> DocumentState:
    state["xmindmark_final"] = generate_xmindmark(
        state["input_text"],
        state["user_requirements"],
        state.get("conversation_history")
    )
    return state

def merge_all_xmindmarks(state: DocumentState) -> DocumentState:
    state["xmindmark_final"] = merge_xmindmarks(
        state["xmindmark_chunks_content"],
        state["global_title"],
        state["user_requirements"],
        state.get("conversation_history")
    )
    return state

def generate_global_title_node(state: DocumentState) -> DocumentState:
    state["global_title"] = generate_global_title(
        state["input_text"],
        state["user_requirements"],
        state.get("conversation_history")
    )
    return state