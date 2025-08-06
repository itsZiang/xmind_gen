import streamlit as st
import requests
from core.text_processing import extract_text_from_file
from io import BytesIO

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="XMind Generator", layout="wide")
st.title("🧠 Tạo Mind Map Tự Động")

def get_stream_response_no_docs(user_requirements):
    """Get streaming response from the no-docs API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark",
            json={"user_requirements": user_requirements,
                  "enable_search": False,
                  "stream": True},
            stream=True
        )
        response.raise_for_status()
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
    except Exception as e:
        raise e

def get_stream_response_with_search(user_requirements):
    """Get streaming response from the search API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark",
            json={"user_requirements": user_requirements,
                  "enable_search": True,
                  "stream": True},
            stream=True
        )
        response.raise_for_status()
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
    except Exception as e:
        raise e

def get_stream_response_with_docs(text, user_requirements):
    """Get streaming response from the documents API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark-from-docs",
            json={"text": text, 
                  "user_requirements": user_requirements, 
                  "stream": True},
            stream=True
        )
        response.raise_for_status()
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
    except Exception as e:
        raise e

def get_edit_stream_response(current_xmindmark, edit_request, use_search=False, original_requirements=""):
    """Get streaming response from edit API (with or without search)"""
    try:
        if use_search:
            response = requests.post(
                f"{API_BASE_URL}/edit-xmindmark",
                json={
                    "current_xmindmark": current_xmindmark,
                    "edit_request": edit_request,
                    "enable_search": True,
                    "original_user_requirements": original_requirements
                },
                stream=True
            )
        else:
            response = requests.post(
                f"{API_BASE_URL}/edit-xmindmark",
                json={"current_xmindmark": current_xmindmark, 
                      "edit_request": edit_request,
                      "enable_search": False,
                      "original_user_requirements": original_requirements},
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
    
    # Toggle buttons for different modes
    st.subheader("🔧 Tùy chọn tạo mindmap")
    
       # Chọn chế độ duy nhất
    mode = st.radio(
        "Chọn chế độ tạo mindmap",
        options=["basic", "docs", "search"],
        format_func=lambda x: {
            "basic": "💭 Cơ bản (không tài liệu)",
            "docs": "📄 Từ tài liệu",
            "search": "🔍 Tìm kiếm thông tin"
        }[x],
        help="Chỉ chọn một chế độ duy nhất"
    )
    uploaded_file = None
    text = None
    if mode == "docs":
        st.markdown("##### 📁 Chọn file")
        uploaded_file = st.file_uploader(
            "Tải lên file tài liệu",
            type=['pdf', 'docx', 'md'],
            help="Chọn file PDF, DOCX hoặc MD để tóm tắt",
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
    if mode == "docs":
        st.info("📄 **Chế độ**: Từ tài liệu")
        current_mode = "docs_only"
    elif mode == "search":
        st.info("🔍 **Chế độ**: Tìm kiếm")
        current_mode = "search_only"
    else:
        st.info("💭 **Chế độ**: Cơ bản")
        current_mode = "basic"

    # Validation
    can_generate = False
    error_message = ""
    if not user_requirements.strip():
        error_message = "⚠️ Vui lòng nhập yêu cầu"
    elif mode == "docs" and not text:
        error_message = "⚠️ Vui lòng tải lên file tài liệu"
    else:
        can_generate = True

    # Single generate button
    if st.button("🚀 Tạo mind map", disabled=not can_generate, type="primary"):
        for key in ["xmindmark", "edited_xmindmark", "svg_url", "xmind_file_url", "previous_edited_xmindmark"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["generating"] = True
        st.session_state["current_mode"] = current_mode
        st.session_state["generation_text"] = text if mode == "docs" else None
        st.session_state["generation_requirements"] = user_requirements
        st.session_state["generation_search_mode"] = (mode == "search")
        st.rerun()

# --- MAIN DISPLAY ---
col1, col2 = st.columns([2, 1])

# --- Chỉnh sửa nội dung ---
with col2:
    st.subheader("📄 Nội dung XMindMark")
    
    # Handle streaming generation
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
            # Choose the appropriate API endpoint based on mode
            generation_text = st.session_state.get("generation_text")
            generation_requirements = st.session_state.get("generation_requirements")
            generation_search_mode = st.session_state.get("generation_search_mode", False)
            
            if current_mode == "docs_only":
                stream_response = get_stream_response_with_docs(generation_text, generation_requirements)
            elif current_mode == "search_only":
                stream_response = get_stream_response_with_search(generation_requirements)
            elif current_mode == "docs_and_search":
                # For now, prioritize docs mode when both are enabled
                # You might want to create a combined endpoint later
                stream_response = get_stream_response_with_docs(generation_text, generation_requirements)
            else:  # basic mode
                stream_response = get_stream_response_no_docs(generation_requirements)
            
            for chunk in stream_response:
                full_response += chunk.decode("utf-8")
                message_placeholder.markdown(f"```\n{full_response}▌\n```")
            
            # Final response without cursor
            message_placeholder.markdown(f"```\n{full_response}\n```")
            
            # Store the generated content
            st.session_state["xmindmark"] = full_response
            st.session_state["edited_xmindmark"] = full_response
            st.session_state["generating"] = False
            
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
    
    # Handle AI editing streaming
    elif st.session_state.get("editing_with_ai", False):
        st.markdown("### 🤖 AI đang chỉnh sửa XMindMark...")
        edit_placeholder = st.empty()
        full_edit_response = ""
        
        try:
            use_search = st.session_state.get("use_search_during_edit", False)
            original_req = st.session_state.get("generation_requirements", "")

            current_xmindmark = st.session_state.get("edited_xmindmark", "")
            edit_stream = get_edit_stream_response(
                current_xmindmark,
                st.session_state.get("edit_request", ""),
                use_search=use_search,
                original_requirements=original_req
            )
            
            for chunk in edit_stream:
                full_edit_response += chunk.decode("utf-8")
                edit_placeholder.markdown(f"```\n{full_edit_response}▌\n```")
            
            # Final response without cursor
            edit_placeholder.markdown(f"```\n{full_edit_response}\n```")
            
            # Store the edited content
            st.session_state["edited_xmindmark"] = full_edit_response
            st.session_state["editing_with_ai"] = False
            
            # Generate new SVG
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
            
            # Clean up edit request from session state
            if "edit_request" in st.session_state:
                del st.session_state["edit_request"]
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Lỗi kết nối API: {str(e)}")
            st.session_state["editing_with_ai"] = False
            if "edit_request" in st.session_state:
                del st.session_state["edit_request"]
    
    # Show generated content and editing options
    elif st.session_state.get("xmindmark"):
        # Display current XMindMark content (read-only with manual edit option)
        xmindmark = st.session_state.get("edited_xmindmark")
        
        # Display content in a code block for better readability
        st.code(xmindmark, language="markdown")
        
        # Option to manually edit
        if st.button("✏️ Chỉnh sửa thủ công"):
            st.session_state["manual_editing"] = True
            st.rerun()
        
        # Manual editing mode
        if st.session_state.get("manual_editing", False):
            st.markdown("### ✏️ Chỉnh sửa thủ công")
            edited = st.text_area("Chỉnh sửa nội dung", value=xmindmark, height=400)
            
            col_edit1, col_edit2 = st.columns(2)
            with col_edit1:
                if st.button("✔️ Xác nhận"):
                    st.session_state["edited_xmindmark"] = edited
                    st.session_state["manual_editing"] = False
                    try:
                        res = requests.post(f"{API_BASE_URL}/to-svg", json={
                            "content": edited
                        })
                        if res.status_code == 200:
                            try:
                                svg_data = res.json()
                                svg_url = svg_data.get("svg_url")
                                st.session_state["svg_url"] = svg_url
                                st.success("✅ Đã cập nhật hình ảnh!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Lỗi đọc JSON: {e}\nResponse: {res.text}")
                        else:
                            st.error(f"❌ Lỗi chuyển SVG: {res.status_code}\nResponse: {res.text}")
                    except Exception as e:
                        st.error(f"❌ Lỗi kết nối API: {str(e)}")
            
            with col_edit2:
                if st.button("❌ Hủy"):
                    st.session_state["manual_editing"] = False
                    st.rerun()
       
        st.divider()
        st.markdown("### 🤖 Chỉnh sửa bằng AI")
        
        # Toggle for search during edit
        enable_search_edit = st.toggle(
            "🔍 Tìm kiếm thông tin mới",
            key="enable_search_toggle",
            help="Bật để AI tìm kiếm thông tin mới trên internet khi chỉnh sửa mindmap"
        )
        
        # Show current status
        if enable_search_edit:
            st.info("🔍 **Chế độ**: AI sẽ tìm kiếm thông tin mới để bổ sung vào mindmap")
        else:
            st.info("📝 **Chế độ**: Chỉ chỉnh sửa nội dung hiện tại (không tìm kiếm)")

        with st.form(key="llm_edit_form", clear_on_submit=True):
            edit_request = st.text_area(
                "Yêu cầu chỉnh sửa:",
                placeholder="Ví dụ:\n- Thêm thông tin về ban lãnh đạo MISA\n- Tìm số liệu mới nhất về doanh thu\n- Bổ sung chi tiết về sản phẩm mới\n- Cập nhật thông tin công nghệ mới nhất",
                height=160,
                key="edit_request_input"
            )
            edit_with_llm = st.form_submit_button("✨ Chỉnh sửa", type="primary")

        if edit_with_llm and edit_request.strip():
            st.session_state["edit_request"] = edit_request
            st.session_state["editing_with_ai"] = True
            st.session_state["use_search_during_edit"] = enable_search_edit
            st.rerun()
        elif edit_with_llm and not edit_request.strip():
            st.warning("⚠️ Vui lòng nhập yêu cầu chỉnh sửa.")
        
    else:
        st.info("🎯 Vui lòng nhập yêu cầu và chọn tùy chọn phù hợp để bắt đầu tạo mind map.")

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
                os.unlink(tmp_file_path)  # Xóa file tạm
               
            else:
                st.error(f"❌ Không thể tải SVG từ server: {svg_response.status_code}")
        except Exception as e:
            st.error(f"❌ Lỗi khi tải SVG: {str(e)}")
    elif st.session_state.get("generating", False) or st.session_state.get("editing_with_ai", False):
        st.info("⏳ Đang xử lý sơ đồ mind map...")
    else:
        st.info("📋 Sơ đồ mind map sẽ hiển thị ở đây sau khi tạo.")

# --- Nút tải về ---
if st.session_state.get("edited_xmindmark") and not st.session_state.get("generating", False) and not st.session_state.get("editing_with_ai", False):
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

        # Nếu nội dung thay đổi hoặc chưa có file_url thì tạo lại file
        if edited_content != prev_content or "xmind_file_url" not in st.session_state:
            try:
                res = requests.post(f"{API_BASE_URL}/to-xmind", json={
                    "content": edited_content
                })
                if res.status_code == 200:
                    xmind_file_url = res.json()["xmind_file"]
                    st.session_state["xmind_file_url"] = xmind_file_url
                    st.session_state["previous_edited_xmindmark"] = edited_content  # cập nhật bản ghi
                else:
                    st.error("❌ Không tạo được file .xmind")
            except Exception as e:
                st.error(f"❌ Lỗi khi tạo file XMind: {str(e)}")

        # Hiển thị nút tải file
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