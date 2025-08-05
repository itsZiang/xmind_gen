# agent/utils/tools.py

from core.llm_handle import split_text_with_llm, merge_xmindmark_with_llm
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def check_need_split(text: str, max_length: int = 1000) -> bool:
    return len(text) > max_length

def split_text(text: str, user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> List[str]:
    chunks = eval(split_text_with_llm(text, user_requirements, conversation_history))
    logger.info(f"Chunks: {chunks}")
    return chunks

def merge_xmindmarks(chunks: List[str], global_title: str, user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    if len(chunks) <= 1:
        if chunks:
            return f"{global_title}\n- {chunks[0]}"
        return global_title
    
    chunks_text = ""
    for i, chunk in enumerate(chunks, 1):
        chunks_text += f"\n--- CHUNK {i} ---\n{chunk}\n"
    
    try:
        response = merge_xmindmark_with_llm(chunks_text, global_title, user_requirements, conversation_history)
        refined_mindmap = response.strip()
        if not refined_mindmap or len(refined_mindmap.split('\n')) < 2:
            raise Exception("LLM response quá ngắn hoặc không hợp lệ")
        return refined_mindmap.split('```')[1]
    
    except Exception as e:
        print(f"Warning: LLM merge failed ({e}), fallback to simple merge")
        return merge_xmindmarks_simple(chunks, global_title)

def merge_xmindmarks_simple(chunks: List[str], global_title: str) -> str:
    merged_lines = [global_title]
    for chunk in chunks:
        lines = chunk.strip().splitlines()
        if not lines:
            continue
        first_line = lines[0].strip()
        if first_line:
            merged_lines.append(f"- {first_line}")
        for line in lines[1:]:
            if line.strip():
                indented_line = "  " + line
                merged_lines.append(indented_line)
    return "\n".join(merged_lines)