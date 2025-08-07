from agent.utils.state import DocumentState
from agent.utils.tools import check_need_split, split_text, merge_xmindmarks
from core.llm_handle import generate_xmindmark, generate_global_title
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import asyncio


def decide_split(state: DocumentState) -> DocumentState:
    state["need_split"] = check_need_split(state["input_text"])
    return state


def split_into_chunks(state: DocumentState) -> DocumentState:
    state["chunks"] = split_text(state["input_text"], state["user_requirements"])
    # THÊM: Khởi tạo list rỗng
    state["xmindmark_chunks_content"] = []
    return state


# def generate_xmindmark_for_chunk(state: DocumentState) -> DocumentState:
#     # Get current chunk index
#     current_index = len(state["xmindmark_chunks_content"])
    
#     # Safety check
#     if current_index >= len(state["chunks"]):
#         return state
    
#     # Process current chunk
#     chunk = state["chunks"][current_index]
#     xmind_chunk = generate_xmindmark(chunk, state["user_requirements"])
    
#     # Add to results
#     state["xmindmark_chunks_content"].append(xmind_chunk)
#     return state


async def process_chunks_parallel(chunks: List[str], user_requirements: str) -> List[str]:
    max_workers = min(len(chunks), 4)
    
    def process_single_chunk(chunk_data):
        chunk_index, chunk_content = chunk_data
        try:
            result = generate_xmindmark(chunk_content, user_requirements)
            return chunk_index, result
        except Exception as e:
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
            except Exception as e:
                results[chunk_index] = f"Error: {str(e)}"
    
    ordered_results = [results[i] for i in sorted(results.keys())]
    return ordered_results

def generate_all_chunks_parallel(state: DocumentState) -> DocumentState:
    chunks = state["chunks"]
    user_requirements = state["user_requirements"]
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(
        process_chunks_parallel(chunks, user_requirements)
    )
    state["xmindmark_chunks_content"] = results
    loop.close()
    return state


def generate_xmindmark_direct(state: DocumentState) -> DocumentState:
    state["xmindmark_final"] = generate_xmindmark(state["input_text"], state["user_requirements"])
    return state


def merge_all_xmindmarks(state: DocumentState) -> DocumentState:
    state["xmindmark_final"] = merge_xmindmarks(state["xmindmark_chunks_content"], state["global_title"], state["user_requirements"])
    return state


def generate_global_title_node(state: DocumentState) -> DocumentState:
    state["global_title"] = generate_global_title(state["input_text"], state["user_requirements"])
    return state