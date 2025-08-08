from agent.utils.state import DocumentState
from agent.utils.tools import check_need_split, split_text, merge_xmindmarks
from core.llm_handle import generate_xmindmark, generate_global_title
from typing_extensions import TypedDict


def decide_split(state: DocumentState) -> DocumentState:
    state["need_split"] = check_need_split(state["input_text"])
    return state


def split_into_chunks(state: DocumentState) -> DocumentState:
    state["chunks"] = split_text(state["input_text"], state["user_requirements"])
    # THÊM: Khởi tạo list rỗng
    state["xmindmark_chunks_content"] = []
    return state


class ChunkState(TypedDict):
    chunk_index: int
    chunk_content: str
    user_requirements: str

def generate_xmindmark_for_chunk(state: ChunkState):
    # Process current chunk
    print(f"Processing chunk [{state['chunk_index']}]")
    xmind_chunk = generate_xmindmark(state["chunk_content"], state["user_requirements"])
    return {"xmindmark_chunks_content": [xmind_chunk]}


def generate_xmindmark_direct(state: DocumentState):
    response = generate_xmindmark(state["input_text"], state["user_requirements"])
    return {"xmindmark_final": response}


def merge_all_xmindmarks(state: DocumentState):
    response = merge_xmindmarks(state["xmindmark_chunks_content"], state["global_title"], state["user_requirements"])
    return {"xmindmark_final": response}


def generate_global_title_node(state: DocumentState):
    response = generate_global_title(state["input_text"], state["user_requirements"])
    return {"global_title": response}