from typing_extensions import TypedDict, Annotated
from typing import List, Dict, Optional, Any
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
    audio_file: Optional[Any] 
    audio_processed: bool  
    transcribed_text: Optional[str]  
    search_mode: bool
    last_search_time: Optional[str]