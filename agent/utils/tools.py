from core.llm_handle import split_text_with_llm, merge_xmindmark_with_llm
import logging
from typing import List

logger = logging.getLogger(__name__)


def check_need_split(text: str, max_length: int = 100) -> bool:
    return len(text) > max_length


def split_text(text: str, user_requirements: str) -> List[str]:
    chunks = eval(split_text_with_llm(text, user_requirements))
    logger.info(f"Chunks: {chunks}")
    
    return chunks


def merge_xmindmarks(chunks: list[str], global_title: str, user_requirements: str) -> str:
    """
    Sử dụng LLM để merge và refine các XMindMark chunks thành một mind map hoàn chỉnh
    """
    
    # Fallback về method cũ nếu chỉ có 1 chunk
    if len(chunks) <= 1:
        if chunks:
            return f"{global_title}\n- {chunks[0]}"
        return global_title
    
    # Chuẩn bị context cho LLM
    chunks_text = ""
    for i, chunk in enumerate(chunks, 1):
        chunks_text += f"\n--- CHUNK {i} ---\n{chunk}\n"
    
    
    try:
        # Gọi LLM để merge và refine
        response = merge_xmindmark_with_llm(chunks_text, global_title, user_requirements)
        refined_mindmap = response.strip()
        
        # Validation cơ bản
        if not refined_mindmap or len(refined_mindmap.split('\n')) < 2:
            raise Exception("LLM response quá ngắn hoặc không hợp lệ")
            
        # return refined_mindmap.split('```')[1]
        return refined_mindmap
        
    except Exception as e:
        print(f"Warning: LLM merge failed ({e}), fallback to simple merge")
        # Fallback về method cũ
        return merge_xmindmarks_simple(chunks, global_title)


def merge_xmindmarks_simple(chunks: list[str], global_title: str) -> str:
    merged_lines = [global_title]  # Root node
    
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
