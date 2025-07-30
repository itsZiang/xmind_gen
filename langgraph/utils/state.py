from typing_extensions import TypedDict, Annotated
from typing import List
from operator import add


class DocumentState(TypedDict):
    input_text: str
    chunks: List[str]
    xmindmark_chunks_content: Annotated[List[str], add]
    xmindmark_full_content: str
    need_split: bool
    

