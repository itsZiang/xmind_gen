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
    - Trả về CHỈ nội dung định dạng xmindmark, không bao gồm giải thích hoặc ký tự ngoài định dạng như ```, ```json, ```python, ...
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
  

def create_global_title_prompt(text: str, user_requirements: str) -> str:
    return f"""
Bạn cần tạo một tiêu đề ngắn gọn cho sơ đồ tư duy dựa trên yêu cầu cụ thể của người dùng.

**YÊU CẦU CỦA NGƯỜI DÙNG:**
{user_requirements}

**NHIỆM VỤ:**
Dựa trên yêu cầu trên, hãy tạo một tiêu đề ngắn gọn (3-8 từ) cho toàn bộ sơ đồ tư duy. 
Tiêu đề phải:
- Phản ánh đúng **mục đích và góc nhìn** mà người dùng quan tâm
- Tập trung vào **khía cạnh chính** mà người dùng muốn khai thác từ tài liệu
- Ngắn gọn, dễ hiểu, thu hút

**VÍ DỤ:**
- Nếu user yêu cầu "quy trình làm việc" → "Quy Trình Làm Việc ABC"
- Nếu user yêu cầu "so sánh phương pháp" → "So Sánh Các Phương Pháp XYZ"
- Nếu user yêu cầu "phân tích rủi ro" → "Phân Tích Rủi Ro Dự Án"
- Nếu user yêu cầu "tổng quan kiến thức" → "Tổng Quan [Tên Chủ Đề]"

Chỉ trả về tiêu đề, không giải thích thêm:

--- NỘI DUNG TÀI LIỆU ---
{text}
--- KẾT THÚC ---
"""
    
def create_split_text_prompt(text: str, user_requirements: str) -> str:
    prompt = f"""
Bạn là một trợ lý AI đang xử lý một tài liệu để tạo sơ đồ tư duy dựa trên yêu cầu cụ thể của người dùng.

---

**YÊU CẦU CỦA NGƯỜI DÙNG:**
{user_requirements}

---

**NHIỆM VỤ CỦA BẠN:**
Hãy phân tích nội dung bên dưới và chia thành các đoạn, mỗi đoạn tương ứng với một ý lớn, chủ đề rõ ràng — phục vụ trực tiếp cho yêu cầu của người dùng.

---

**HƯỚNG DẪN CHIA ĐOẠN:**
1. **Ưu tiên nội dung liên quan đến yêu cầu** — lọc hoặc rút gọn phần không liên quan.
2. **Một đoạn = một ý chính hoặc nhóm thông tin liên kết chặt chẽ.**
3. **Nếu nội dung dài hơn 600 từ**, có thể chia nhỏ để dễ phân tích.
4. **Nếu không cần chia**, giữ nguyên toàn bộ thành **một đoạn duy nhất**.
5. **Không được phân mảnh thông tin một cách máy móc.**
6. **Đảm bảo mỗi đoạn có thể dùng làm node chính trong sơ đồ tư duy.**

---

**YÊU CẦU ĐẦU RA:**
- **Chỉ trả về đúng một danh sách Python duy nhất.**
- **Không được trả lời thêm bất kỳ giải thích, mô tả, tiêu đề nào.**
- Định dạng ví dụ hợp lệ:
    ["Đoạn 1 về nội dung chính A", "Đoạn 2 liên quan đến nội dung B", "Đoạn 3 tổng kết hoặc mở rộng"]
- Nếu chỉ cần một đoạn:
    ["Toàn bộ nội dung liên quan đến yêu cầu"]

⚠️ **Lưu ý quan trọng:** Trả lời của bạn sẽ được phân tích bằng `eval(...)`, vì vậy định dạng phải hoàn toàn hợp lệ: **một danh sách Python chứa các chuỗi (`list[str]`)**.

---

**VĂN BẢN CẦN XỬ LÝ:**
{text}
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
    - TUYỆT ĐỐI không dùng các ký tự thừa như ```, ```json, ```python, ...
   
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


def create_merge_xmindmark_prompt(chunks_text: str, global_title: str, user_requirements: str) -> str:
    prompt = f"""
Bạn là chuyên gia tạo sơ đồ tư duy. Nhiệm vụ của bạn là hợp nhất các phần sơ đồ riêng lẻ thành một sơ đồ tư duy hoàn chỉnh, mạch lạc và tối ưu.

**YÊU CẦU CỦA NGƯỜI DÙNG:**
{user_requirements}

**TIÊU ĐỀ CHÍNH:**
{global_title}

**CÁC PHẦN SƠ ĐỒ CẦN HỢP NHẤT:**
{chunks_text}

**NHIỆM VỤ:**
Hãy tạo một sơ đồ tư duy hoàn chỉnh bằng cách:

1. **Tổ chức lại cấu trúc**: Sắp xếp các ý theo logic, tầm quan trọng và mối liên hệ
2. **Loại bỏ trùng lặp**: Gộp các ý tương tự, loại bỏ thông tin lặp lại
3. **Cân bằng độ sâu**: Đảm bảo các nhánh có độ chi tiết phù hợp
4. **Tối ưu hóa**: Rút gọn các cụm từ dài, sử dụng từ ngữ súc tích
5. **Tăng tính logic**: Sắp xếp các nhánh theo thứ tự logic (thời gian, tầm quan trọng, nhân quả...)

**QUY TẮC ĐỊNH DẠNG XMindMark:**
- Dòng đầu tiên: Tiêu đề chính (không có dấu -)
- Level 1: Bắt đầu với "- "
- Level 2: Bắt đầu với "  - " (2 spaces + dash)  
- Level 3: Bắt đầu với "    - " (4 spaces + dash)
- Level 4: Bắt đầu với "      - " (6 spaces + dash)

**VÍ DỤ ĐỊNH DẠNG:**
Tiêu Đề Chính
- Nhánh chính 1
  - Nhánh phụ 1.1
    - Chi tiết 1.1.1
    - Chi tiết 1.1.2
  - Nhánh phụ 1.2
- Nhánh chính 2
  - Nhánh phụ 2.1

**LƯU Ý:**
- Ưu tiên nội dung phù hợp với yêu cầu người dùng
- Đảm bảo mind map dễ đọc và logic
- Tránh quá nhiều level (tối đa 4-5 level)
- Sử dụng từ ngữ ngắn gọn, dễ hiểu
- Trả về CHỈ nội dung XMindMark được chỉnh sửa, không có giải thích hay văn bản khác
- TUYỆT ĐỐI không dùng các ký tự thừa như ```, ```json, ```python, ...

Hãy trả về sơ đồ tư duy hoàn chỉnh:
"""
    return prompt