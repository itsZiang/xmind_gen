from typing_extensions import TypedDict, Annotated
from typing import List
from operator import add


class DocumentState(TypedDict):
    input_text: str
    user_requirements: str
    need_split: bool
    chunks: List[str]
    # xmindmark_chunks_content: Annotated[List[str], add]
    xmindmark_chunks_content: Annotated[List[str], add]
    xmindmark_final: str
    global_title: str