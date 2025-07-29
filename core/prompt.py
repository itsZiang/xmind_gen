def create_structured_prompt(text: str, user_requirements: str) -> str:
    """Tạo prompt yêu cầu LLM trả về JSON hợp lệ"""
    prompt = f"""
    Hãy phân tích văn bản sau và tạo một bản đồ tư duy theo yêu cầu của người dùng.
    YÊU CẦU CỦA NGƯỜI DÙNG: {user_requirements}
    VĂN BẢN CẦN PHÂN TÍCH:
    {text}
    HƯỚNG DẪN:
    - Tự quyết định số lượng nhánh chính, nhánh phụ và tầng dựa trên nội dung và yêu cầu.
    - Mỗi nút (node) trong bản đồ tư duy CHỈ BAO GỒM từ khóa hoặc cụm từ ngắn (keywords/phrases), KHÔNG PHẢI CÂU HOÀN CHỈNH.
    - Trả về CHỈ JSON hợp lệ, không bao gồm bất kỳ văn bản giải thích, ký tự ngoài JSON, hoặc định dạng khác.
    - Đảm bảo cú pháp JSON đúng: sử dụng dấu nháy kép ("), kiểm tra dấu phẩy (,), và đóng tất cả dấu ngoặc.
    - Cấu trúc JSON phải theo định dạng sau:
    {{
        "title": "Tiêu đề chung cho bản đồ tư duy (dưới 10 từ)",
        "nodes": [
        {{
            "id": "unique_id_1",
            "label": "Keyword hoặc cụm từ ngắn cho nút này",
            "level": 0,
            "parent_id": null
        }},
        {{
            "id": "unique_id_2",
            "label": "Keyword hoặc cụm từ ngắn cho nút con",
            "level": 1,
            "parent_id": "unique_id_1"
        }},
        {{
            "id": "unique_id_3",
            "label": "Keyword hoặc cụm từ ngắn cho nút cháu",
            "level": 2,
            "parent_id": "unique_id_2"
        }}
        ]
    }}
    Ví dụ:
    {{
        "title": "ông nội",
        "nodes": [
        {{"id": "root", "label": "ông nội", "level": 0, "parent_id": null}},
        {{"id": "c1", "label": "cha1", "level": 1, "parent_id": "root"}},
        {{"id": "c2", "label": "cha2", "level": 1, "parent_id": "root"}},
        {{"id": "c1_1", "label": "con1", "level": 2, "parent_id": "c1"}},
        {{"id": "c1_2", "label": "con2", "level": 2, "parent_id": "c1"}},
        {{"id": "c2_1", "label": "con1", "level": 2, "parent_id": "c2"}},
        {{"id": "c2_2", "label": "con2", "level": 2, "parent_id": "c2"}}
        ]
    }}
    """
    return prompt