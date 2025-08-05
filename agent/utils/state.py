# agent/utils/state.py

from typing_extensions import TypedDict, Annotated
from typing import List, Dict, Optional
from operator import add

class DocumentState(TypedDict):
    input_text: str
    user_requirements: str
    conversation_history: Optional[List[Dict[str, str]]]
    need_split: bool
    chunks: List[str]
    xmindmark_chunks_content: List[str]
    xmindmark_final: str
    global_title: str
    chunk_processing_status: str