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
      - Nhánh chính bắt đầu trực tiếp (không thụt đầu dòng).
      - Nhánh phụ thụt đầu dòng bằng dấu "- " (dấu trừ và khoảng trắng).
      - Các tầng sâu hơn thụt thêm bằng cách thêm "- " cho mỗi cấp.
    - Trả về CHỈ nội dung định dạng xmindmark, không bao gồm giải thích hoặc ký tự ngoài định dạng.
    Ví dụ:
    ông nội
    - cha1
      - con1
      - con2
    - cha2
      - con1
      - con2
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