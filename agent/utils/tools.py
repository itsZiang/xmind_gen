from core.llm_handle import generate_title_text, generate_global_title
import logging
from typing import List

logger = logging.getLogger(__name__)


def check_need_split(text: str, max_length: int = 3000) -> bool:
    return len(text) > max_length


def split_text(text: str) -> List[str]:
    title_list = eval(generate_title_text(text))
    logger.info(f"Title list: {title_list}")
    
    chunks = []
    current_pos = 0

    for i in range(len(title_list)):
        title = title_list[i]
        # Tìm vị trí xuất hiện tiếp theo của title trong text
        start_index = text.find(title, current_pos)
        if start_index == -1:
            continue  # title không tìm thấy (hiếm khi xảy ra nếu prompt đúng)
        
        # Tìm vị trí bắt đầu của title kế tiếp
        if i + 1 < len(title_list):
            next_title = title_list[i + 1]
            end_index = text.find(next_title, start_index + len(title))
        else:
            end_index = len(text)

        chunk = text[start_index:end_index].strip()
        chunks.append(chunk)
        current_pos = end_index

    return chunks



def merge_xmindmarks(chunks: list[str], global_title: str) -> str:
    merged_lines = [global_title]  # Root node
    
    for chunk in chunks:
        lines = chunk.strip().splitlines()
        if not lines:
            continue
            
        # Dòng đầu tiên là "ông nội" - chuyển thành child của root (thêm "- ")
        first_line = lines[0].strip()
        if first_line:
            merged_lines.append(f"- {first_line}")
        
        # Các dòng còn lại thụt vào thêm 1 level (thêm 2 spaces)
        for line in lines[1:]:
            if line.strip():  # Bỏ qua dòng trống
                indented_line = "  " + line
                merged_lines.append(indented_line)
    
    return "\n".join(merged_lines)
