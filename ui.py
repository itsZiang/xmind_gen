import streamlit as st
import requests
from core.text_processing import extract_text_from_file
from io import BytesIO
import json

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="XMind Generator", layout="wide")
st.title("🧠 Tạo Mind Map Tự Động")

# Khởi tạo session state để lưu lịch sử hội thoại
if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = []

def get_stream_response_no_docs(user_requirements):
    """Get streaming response from the no-docs API with conversation context"""
    try:
        # Gửi lịch sử hội thoại cùng với yêu cầu
        payload = {
            "user_requirements": user_requirements,
            "conversation_history": st.session_state["conversation_history"]
        }
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark-no-docs",
            json=payload,
            stream=True
        )
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
    except Exception as e:
        raise e

def get_stream_response_with_search(user_requirements):
    """Get streaming response from the search API with conversation context"""
    try:
        payload = {
            "user_requirements": user_requirements,
            "conversation_history": st.session_state["conversation_history"]
        }
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark-with-search",
            json=payload,
            stream=True
        )
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
    except Exception as e:
        raise e

def get_stream_response_with_docs(text, user_requirements):
    """Get streaming response from the documents API with conversation context"""
    try:
        payload = {
            "text": text,
            "user_requirements": user_requirements,
            "conversation_history": st.session_state["conversation_history"]
        }
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark-langgraph-stream",
            json=payload,
            stream=True
        )
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
    except Exception as e:
        raise e

def get_edit_stream_response(current_xmindmark, edit_request):
    """Get streaming response from the edit API with conversation context"""
    try:
        payload = {
            "current_xmindmark": current_xmindmark,
            "edit_request": edit_request,
            "conversation_history": st.session_state["conversation_history"]
        }
        response = requests.post(
            f"{API_BASE_URL}/edit-xmindmark",
            json=payload,
            stream=True
        )
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
    except Exception as e:
        raise e

# --- SIDEBAR ---
with st.sidebar:
    st.header("📌 Nhập yêu cầu & tùy chọn")

    # User requirements - always visible
    user_requirements = st.text_area("Yêu cầu của bạn", height=150)

    st.divider()
    st.subheader("🔧 Tùy chọn tạo mindmap")
    
    # Toggle buttons for different modes
    upload_mode = st.toggle("📄 Tải lên file tài liệu", value=False, help="Bật để tạo mindmap từ file tài liệu")
    search_mode = st.toggle("🔍 Tìm kiếm thông tin", value=False, help="Bật để tự động tìm kiếm thông tin trên internet")

    # File upload section
    uploaded_file = None
    text = None
    if upload_mode:
        st.markdown("##### 📁 Chọn file")
        uploaded_file = st.file_uploader(
            "Tải lên file tài liệu",
            type=['pdf', 'docx', 'md'],
            help="Chọn file PDF, DOC X hoặc MD để tóm tắt",
            label_visibility="collapsed"
        )
        if uploaded_file:
            try:
                text = extract_text_from_file(uploaded_file)
                st.success("✅ Tải file thành công!")
            except Exception as e:
                st.error(f"❌ Lỗi xử lý file: {e}")
                text = None

    # Mode indicator
    st.divider()
    if upload_mode and search_mode:
        st.info("🔄 **Chế độ**: Tài liệu + Tìm kiếm")
        current_mode = "docs_and_search"
    elif upload_mode:
        st.info("📄 **Chế độ**: Từ tài liệu")
        current_mode = "docs_only"
    elif search_mode:
        st.info("🔍 **Chế độ**: Tìm kiếm")
        current_mode = "search_only"
    else:
        st.info("💭 **Chế độ**: Cơ bản")
        current_mode = "basic"

    # Validation and generate button
    can_generate = False
    error_message = ""
    if not user_requirements.strip():
        error_message = "⚠️ Vui lòng nhập yêu cầu"
    elif upload_mode and not text:
        error_message = "⚠️ Vui lòng tải lên file tài liệu"
    else:
        can_generate = True

    if error_message:
        st.warning(error_message)

    if st.button("🚀 Tạo mind map", disabled=not can_generate, type="primary"):
        # Lưu yêu cầu vào lịch sử hội thoại
        st.session_state["conversation_history"].append({
            "role": "user",
            "content": user_requirements
        })
        # Reset session state for new generation
        for key in ["xmindmark", "edited_xmindmark", "svg_url", "xmind_file_url", "previous_edited_xmindmark"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["generating"] = True
        st.session_state["current_mode"] = current_mode
        st.session_state["generation_text"] = text if upload_mode else None
        st.session_state["generation_requirements"] = user_requirements
        st.session_state["generation_search_mode"] = search_mode
        st.rerun()

# --- MAIN DISPLAY ---
col1, col2 = st.columns([2, 1])

# --- Chỉnh sửa nội dung ---
with col2:
    st.subheader("📄 Nội dung XMindMark")
    if st.session_state.get("generating", False):
        current_mode = st.session_state.get("current_mode", "basic")
        if current_mode == "docs_only":
            st.markdown("### 🤖 Đang tạo XMindMark từ tài liệu...")
        elif current_mode == "search_only":
            st.markdown("### 🤖 Đang tìm kiếm và tạo XMindMark...")
        elif current_mode == "docs_and_search":
            st.markdown("### 🤖 Đang tạo XMindMark từ tài liệu + tìm kiếm...")
        else:
            st.markdown("### 🤖 Đang tạo XMindMark...")
        
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            generation_text = st.session_state.get("generation_text")
            generation_requirements = st.session_state.get("generation_requirements")
            generation_search_mode = st.session_state.get("generation_search_mode", False)
            
            if current_mode == "docs_only":
                stream_response = get_stream_response_with_docs(generation_text, generation_requirements)
            elif current_mode == "search_only":
                stream_response = get_stream_response_with_search(generation_requirements)
            elif current_mode == "docs_and_search":
                # Kết hợp tài liệu và tìm kiếm
                stream_response = get_stream_response_with_docs(generation_text, generation_requirements)
            else:
                stream_response = get_stream_response_no_docs(generation_requirements)
            
            for chunk in stream_response:
                full_response += chunk.decode("utf-8")
                message_placeholder.markdown(f"```\n{full_response}▌\n```")
            
            message_placeholder.markdown(f"```\n{full_response}\n```")
            st.session_state["xmindmark"] = full_response
            st.session_state["edited_xmindmark"] = full_response
            st.session_state["generating"] = False
            
            # Lưu phản hồi vào lịch sử hội thoại
            st.session_state["conversation_history"].append({
                "role": "assistant",
                "content": full_response
            })
            
            # Generate SVG
            try:
                svg_res = requests.post(f"{API_BASE_URL}/to-svg", json={"content": full_response})
                if svg_res.status_code == 200:
                    svg_data = svg_res.json()
                    svg_url = svg_data.get("svg_url")
                    st.session_state["svg_url"] = svg_url
                    st.success("✅ Mind map đã tạo và hiển thị!")
                else:
                    st.error(f"❌ Không tạo được SVG: {svg_res.status_code}")
            except Exception as e:
                st.error(f"❌ Lỗi tạo SVG: {str(e)}")
            
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Lỗi kết nối API: {str(e)}")
            st.session_state["generating"] = False
    
    elif st.session_state.get("editing_with_ai", False):
        st.markdown("### 🤖 AI đang chỉnh sửa XMindMark...")
        edit_placeholder = st.empty()
        full_edit_response = ""
        
        try:
            edit_stream = get_edit_stream_response(
                st.session_state.get("xmindmark", ""),
                st.session_state.get("edit_request", "")
            )
            
            for chunk in edit_stream:
                full_edit_response += chunk.decode("utf-8")
                edit_placeholder.markdown(f"```\n{full_edit_response}▌\n```")
            
            edit_placeholder.markdown(f"```\n{full_edit_response}\n```")
            st.session_state["edited_xmindmark"] = full_edit_response
            st.session_state["editing_with_ai"] = False
            
            # Lưu chỉnh sửa vào lịch sử hội thoại
            st.session_state["conversation_history"].append({
                "role": "user",
                "content": st.session_state.get("edit_request", "")
            })
            st.session_state["conversation_history"].append({
                "role": "assistant",
                "content": full_edit_response
            })
            
            try:
                svg_res = requests.post(f"{API_BASE_URL}/to-svg", json={"content": full_edit_response})
                if svg_res.status_code == 200:
                    svg_data = svg_res.json()
                    svg_url = svg_data.get("svg_url")
                    st.session_state["svg_url"] = svg_url
                    st.success("✅ AI đã chỉnh sửa thành công!")
                else:
                    st.error(f"❌ Không tạo được SVG: {svg_res.status_code}")
            except Exception as e:
                st.error(f"❌ Lỗi tạo SVG: {str(e)}")
            
            if "edit_request" in st.session_state:
                del st.session_state["edit_request"]
            
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Lỗi kết nối API: {str(e)}")
            st.session_state["editing_with_ai"] = False
            if "edit_request" in st.session_state:
                del st.session_state["edit_request"]
    
    elif st.session_state.get("xmindmark"):
        xmindmark = st.session_state.get("edited_xmindmark")
        st.code(xmindmark, language="markdown")
        
        # Thêm nút để reset lịch sử hội thoại
        if st.button("🔄 Reset lịch sử hội thoại"):
            st.session_state["conversation_history"] = []
            st.success("Đã reset lịch sử hội thoại!")
            st.rerun()
        
        if st.button("✏️ Chỉnh sửa thủ công"):
            st.session_state["manual_editing"] = True
            st.rerun()
        
        if st.session_state.get("manual_editing", False):
            st.markdown("### ✏️ Chỉnh sửa thủ công")
            edited = st.text_area("Chỉnh sửa nội dung", value=xmindmark, height=400)
            
            col_edit1, col_edit2 = st.columns(2)
            with col_edit1:
                if st.button("✔️ Xác nhận"):
                    st.session_state["edited_xmindmark"] = edited
                    st.session_state["manual_editing"] = False
                    try:
                        res = requests.post(f"{API_BASE_URL}/to-svg", json={"content": edited})
                        if res.status_code == 200:
                            svg_data = res.json()
                            svg_url = svg_data.get("svg_url")
                            st.session_state["svg_url"] = svg_url
                            st.success("✅ Đã cập nhật hình ảnh!")
                            st.rerun()
                        else:
                            st.error(f"❌ Lỗi chuyển SVG: {res.status_code}")
                    except Exception as e:
                        st.error(f"❌ Lỗi kết nối API: {str(e)}")
            
            with col_edit2:
                if st.button("❌ Hủy"):
                    st.session_state["manual_editing"] = False
                    st.rerun()
        
        st.divider()
        st.markdown("### 🤖 Chỉnh sửa bằng AI hoặc Tìm kiếm")
        with st.form(key="llm_edit_form", clear_on_submit=True):
            edit_request = st.text_area(
                "Yêu cầu chỉnh sửa hoặc tìm kiếm:",
                placeholder="Ví dụ:\n- Thêm chi tiết cho nhánh 'Phương pháp'\n- Tìm kiếm thông tin về 'AI trong giáo dục'\n- Sắp xếp lại cấu trúc theo thứ tự logic\n- Rút gọn các từ khóa quá dài",
                height=160,
                key="edit_request_input"
            )
            edit_with_llm = st.form_submit_button("✨ Chỉnh sửa/Tìm kiếm bằng AI", type="secondary")
        
        if edit_with_llm and edit_request.strip():
            # Phân loại yêu cầu: chỉnh sửa hay tìm kiếm
            if any(keyword in edit_request.lower() for keyword in ["tìm kiếm", "search", "tra cứu"]):
                st.session_state["search_edit_request"] = edit_request
                st.session_state["editing_with_search"] = True
            else:
                st.session_state["edit_request"] = edit_request
                st.session_state["editing_with_ai"] = True
            st.rerun()
        elif edit_with_llm and not edit_request.strip():
            st.warning("⚠️ Vui lòng nhập yêu cầu chỉnh sửa hoặc tìm kiếm.")

# --- Xử lý tìm kiếm trong chỉnh sửa ---
if st.session_state.get("editing_with_search", False):
    st.markdown("### 🔍 Đang tìm kiếm và chỉnh sửa XMindMark...")
    search_placeholder = st.empty()
    full_search_response = ""
    
    try:
        search_stream = get_stream_response_with_search(st.session_state.get("search_edit_request", ""))
        for chunk in search_stream:
            full_search_response += chunk.decode("utf-8")
            search_placeholder.markdown(f"```\n{full_search_response}▌\n```")
        
        search_placeholder.markdown(f"```\n{full_search_response}\n```")
        st.session_state["edited_xmindmark"] = full_search_response
        st.session_state["editing_with_search"] = False
        
        # Lưu vào lịch sử hội thoại
        st.session_state["conversation_history"].append({
            "role": "user",
            "content": st.session_state.get("search_edit_request", "")
        })
        st.session_state["conversation_history"].append({
            "role": "assistant",
            "content": full_search_response
        })
        
        try:
            svg_res = requests.post(f"{API_BASE_URL}/to-svg", json={"content": full_search_response})
            if svg_res.status_code == 200:
                svg_data = svg_res.json()
                svg_url = svg_data.get("svg_url")
                st.session_state["svg_url"] = svg_url
                st.success("✅ Đã chỉnh sửa với tìm kiếm thành công!")
            else:
                st.error(f"❌ Không tạo được SVG: {svg_res.status_code}")
        except Exception as e:
            st.error(f"❌ Lỗi tạo SVG: {str(e)}")
        
        if "search_edit_request" in st.session_state:
            del st.session_state["search_edit_request"]
        
        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Lỗi kết nối API: {str(e)}")
        st.session_state["editing_with_search"] = False
        if "search_edit_request" in st.session_state:
            del st.session_state["search_edit_request"]

# --- Hiển thị SVG ---
with col1:
    st.subheader("🧩 Sơ đồ Mindmap")
    svg_url = st.session_state.get("svg_url")
    if svg_url:
        try:
            svg_response = requests.get(f"http://localhost:8000{svg_url}")
            if svg_response.status_code == 200:
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp_file:
                    tmp_file.write(svg_response.content)
                    tmp_file_path = tmp_file.name
                st.image(tmp_file_path, use_container_width=True)
                os.unlink(tmp_file_path)
            else:
                st.error(f"❌ Không thể tải SVG từ server: {svg_response.status_code}")
        except Exception as e:
            st.error(f"❌ Lỗi khi tải SVG: {str(e)}")
    elif st.session_state.get("generating", False) or st.session_state.get("editing_with_ai", False) or st.session_state.get("editing_with_search", False):
        st.info("⏳ Đang xử lý sơ đồ mind map...")
    else:
        st.info("📋 Sơ đồ mind map sẽ hiển thị ở đây sau khi tạo.")

# --- Nút tải về ---
if st.session_state.get("edited_xmindmark") and not st.session_state.get("generating", False) and not st.session_state.get("editing_with_ai", False) and not st.session_state.get("editing_with_search", False):
    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        svg_url = st.session_state.get("svg_url")
        if svg_url:
            try:
                response = requests.get(f"http://localhost:8000{svg_url}")
                if response.status_code == 200:
                    st.download_button(
                        label="📥 Tải ảnh SVG",
                        data=response.content,
                        file_name=svg_url.split("/")[-1],
                        mime="image/svg+xml"
                    )
                else:
                    st.error("❌ Không thể tải ảnh SVG.")
            except Exception as e:
                st.error(f"❌ Lỗi khi tải SVG: {str(e)}")
    
    with col_dl2:
        edited_content = st.session_state.get("edited_xmindmark")
        prev_content = st.session_state.get("previous_edited_xmindmark")
        if edited_content != prev_content or "xmind_file_url" not in st.session_state:
            try:
                res = requests.post(f"{API_BASE_URL}/to-xmind", json={"content": edited_content})
                if res.status_code == 200:
                    xmind_file_url = res.json()["xmind_file"]
                    st.session_state["xmind_file_url"] = xmind_file_url
                    st.session_state["previous_edited_xmindmark"] = edited_content
                else:
                    st.error("❌ Không tạo được file .xmind")
            except Exception as e:
                st.error(f"❌ Lỗi khi tạo file XMind: {str(e)}")
        
        xmind_file_url = st.session_state.get("xmind_file_url")
        if xmind_file_url:
            try:
                xmind_response = requests.get(f"http://localhost:8000{xmind_file_url}")
                if xmind_response.status_code == 200:
                    st.download_button(
                        label="📥 Tải file XMind",
                        data=xmind_response.content,
                        file_name=xmind_file_url.split("/")[-1],
                        mime="application/octet-stream"
                    )
                else:
                    st.error("❌ Không thể tải file XMind.")
            except Exception as e:
                st.error(f"❌ Lỗi khi tải file XMind: {str(e)}")
        else:
            st.info("Đang xử lý tạo file XMind...")