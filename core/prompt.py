def create_xmindmark_prompt(text: str, user_requirements: str) -> str:
    """Tạo prompt yêu cầu LLM trả về định dạng xmindmark"""
    prompt = f"""
    Hãy phân tích văn bản sau và tạo một bản đồ tư duy theo định dạng xmindmark dựa trên yêu cầu của người dùng.
    YÊU CẦU CỦA NGƯỜI DÙNG: {user_requirements}
    VĂN BẢN CẦN PHÂN TÍCH:
    {text}
    HƯỚNG DẪN:
    - Tự quyết định số lượng nhánh chính, nhánh phụ và tầng dựa trên nội dung và yêu cầu.
    - Mỗi dòng trong định dạng xmindmark đại diện cho một nút (node), chỉ bao gồm từ khóa hoặc cụm từ ngắn (keywords/phrases), KHÔNG PHẢI CÂU HOÀN CHỈNH.
    - Sử dụng định dạng xmindmark:
      - Nhánh gốc bắt đầu trực tiếp (không thụt đầu dòng, chỉ có duy nhất 1 nhánh gốc).
      - Nhánh phụ thụt đầu dòng bằng dấu "- " (dấu trừ và khoảng trắng).
      - Các tầng sâu hơn thụt thêm bằng cách thêm "- " cho mỗi cấp.
    - Trả về CHỈ nội dung định dạng xmindmark, không bao gồm giải thích hoặc ký tự ngoài định dạng.
    Ví dụ:
    ông nội 
    - cha1
        - con1
            - con1.1
        - con2
    - cha2
        - con1
        - con2
    """
    return prompt
  

# def create_split_text_prompt(text: str) -> str:
#     prompt = f"""
# You are given a long document. Your task is to identify the **main section titles or headings** that can be used to split the text into smaller chunks.

# **Requirements:**
# - Only return headings that **exactly appear** in the text.
# - Return only the **text of those headings**, no explanation.
# - Do not modify or paraphrase the headings.
# - The output must be a Python list of strings.

# Here is the document:

# {text}

# Now return the list of headings (as they appear in the document) that can be used to split it.
#     """
#     return prompt
  

def create_global_title_prompt(text: str) -> str:
    return f"""
Given the following document, suggest a super short (for the whole mind map) title, general **title** that best represents the entire content.
Return only the title (do not include explanation or formatting):

{text}
    """
    
def create_split_text_prompt(text: str) -> str:
    prompt = f"""
Bạn là một trợ lý AI đang xử lý một tài liệu để tạo sơ đồ tư duy.

Hãy chia văn bản sau thành các đoạn riêng biệt, mỗi đoạn tương ứng với **một ý chính** trong tài liệu. 
Nếu đoạn quá dài, bạn có thể tóm tắt nó lại sao cho ngắn gọn mà vẫn đủ ý.
Cố gắng chia văn bản thành các đoạn lớn nhất có thể, bao gồm ý tổng quát nhất có thể.

Trả về kết quả dưới dạng danh sách các đoạn, ví dụ: ["Đoạn 1", "Đoạn 2", "Đoạn 3"]

--- BẮT ĐẦU VĂN BẢN ---
{text}
--- KẾT THÚC VĂN BẢN ---
"""
    return prompt
  
  
def create_edit_prompt(current_xmindmark: str, edit_request: str) -> str:  # Xóa self
    """Tạo prompt cho chỉnh sửa XMindMark"""
    prompt = f"""
    Bạn cần chỉnh sửa nội dung XMindMark hiện tại theo yêu cầu của người dùng.
   
    NỘI DUNG XMINDMARK HIỆN TẠI:
    {current_xmindmark}
   
    YÊU CẦU CHỈNH SỬA:
    {edit_request}
   
    HƯỚNG DẪN:
    - Chỉnh sửa nội dung XMindMark theo yêu cầu nhưng vẫn giữ đúng format XMindMark
    - Format XMindMark: Dòng đầu là title, các dòng tiếp theo bắt đầu bằng "- " và sử dụng tab để thể hiện cấp độ
    - Mỗi nút chỉ nên là từ khóa hoặc cụm từ ngắn, không phải câu dài
    - Đảm bảo cấu trúc phân cấp hợp lý (root -> level 1 -> level 2...)
    - Trả về CHỈ nội dung XMindMark được chỉnh sửa, không có giải thích hay văn bản khác
   
    VÍ DỤ FORMAT ĐÚNG:
    Tiêu đề bản đồ tư duy
    - Nhánh chính 1
    \t- Nhánh phụ 1.1
    \t\t- Chi tiết 1.1.1
    \t- Nhánh phụ 1.2
    - Nhánh chính 2
    \t- Nhánh phụ 2.1
    """
    return prompt