from agent.utils.state import DocumentState
from agent.utils.tools import check_need_split, split_text, merge_xmindmarks
from core.llm_handle import generate_xmindmark, generate_global_title 


def decide_split(state: DocumentState) -> DocumentState:
    state["need_split"] = check_need_split(state["input_text"])
    return state


def split_into_chunks(state: DocumentState) -> DocumentState:
    state["chunks"] = split_text(state["input_text"])
    # THÊM: Khởi tạo list rỗng
    state["xmindmark_chunks_content"] = []
    return state


# def generate_xmindmark_for_chunk(state: DocumentState) -> DocumentState:
#     # Áp dụng từng chunk
#     chunk = state["chunks"][len(state["xmindmark_chunks_content"])]
#     xmind_chunk = generate_xmindmark(chunk, state["user_requirements"])
#     state["xmindmark_chunks_content"].append(xmind_chunk)
#     return state

def generate_xmindmark_for_chunk(state: DocumentState) -> DocumentState:
    # Get current chunk index
    current_index = len(state["xmindmark_chunks_content"])
    
    # Safety check
    if current_index >= len(state["chunks"]):
        return state
    
    # Process current chunk
    chunk = state["chunks"][current_index]
    xmind_chunk = generate_xmindmark(chunk, state["user_requirements"])
    
    # Add to results
    state["xmindmark_chunks_content"].append(xmind_chunk)
    return state


def generate_xmindmark_direct(state: DocumentState) -> DocumentState:
    state["xmindmark_final"] = generate_xmindmark(state["input_text"], state["user_requirements"])
    return state


def merge_all_xmindmarks(state: DocumentState) -> DocumentState:
    state["xmindmark_final"] = merge_xmindmarks(state["xmindmark_chunks_content"], state["global_title"])
    return state


def generate_global_title_node(state: DocumentState) -> DocumentState:
    state["global_title"] = generate_global_title(state["input_text"])
    return state