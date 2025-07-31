from utils.state import DocumentState
from utils.tools import check_need_split, split_text, merge_xmindmarks
from core.llm_handle import generate_xmindmark, generate_global_title 


def decide_split(state: DocumentState) -> DocumentState:
    state["need_split"] = check_need_split(state["input_text"])
    return state


def split_into_chunks(state: DocumentState) -> DocumentState:
    state["chunks"] = split_text(state["input_text"])
    return state


def generate_xmindmark_for_chunk(state: DocumentState) -> DocumentState:
    # Áp dụng từng chunk
    chunk = state["chunks"][len(state["xmindmark_chunks_content"])]
    xmind_chunk = generate_xmindmark(chunk, state["user_requirements"])
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