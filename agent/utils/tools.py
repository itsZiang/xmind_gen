from core.llm_handle import split_text_with_llm
import logging
from typing import List

logger = logging.getLogger(__name__)


def check_need_split(text: str, max_length: int = 2000) -> bool:
    return len(text) > max_length


def split_text(text: str) -> List[str]:
    chunks = eval(split_text_with_llm(text))
    logger.info(f"Chunks: {chunks}")
    
    return chunks


def merge_xmindmarks(chunks: list[str], global_title: str) -> str:
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
