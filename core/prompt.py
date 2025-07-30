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
    ông nội (root node - tên của cả bản đồ tư duy)
    - cha1 (node cha)
      - con1 (node con)
        - con1.1
      - con2 (node con)
    - cha2 (node cha)
      - con1 (node con)
      - con2 (node con)
    """
    return prompt