import streamlit as st
import requests
import base64
import json
from core.text_processing import extract_text_from_file
import re
import unicodedata
import io

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="XMind Generator", layout="wide")
st.title("🧠 Tạo Mind Map Tự Động")


def extract_snake_case_title(xmindmark: str) -> str:
    """Trích tiêu đề từ XMindMark và chuyển thành snake_case không dấu"""
    lines = xmindmark.strip().splitlines()
    if not lines:
        return "mindmap"
    title = lines[0]
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('utf-8')
    title = re.sub(r'[^\w\s-]', '', title).strip().lower()
    title = re.sub(r'[-\s]+', '_', title)
    return title if title else "mindmap"


def parse_json_stream(response):
    """Parse JSON streaming response and yield delta content"""
    try:
        for line in response.iter_lines(decode_unicode=True):
            if line.strip():
                try:
                    chunk_data = json.loads(line)
                    if chunk_data.get("delta"):
                        yield chunk_data["delta"]
                    if chunk_data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        raise e


def get_stream_response_no_docs(user_requirements):
    """Get streaming response from the no-docs API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark",
            json={
                "user_requirements": user_requirements,
                "enable_search": False,
                "stream": True
            },
            stream=True
        )
        response.raise_for_status()
        
        for delta in parse_json_stream(response):
            yield delta
            
    except Exception as e:
        raise e


def get_stream_response_with_search(user_requirements):
    """Get streaming response from the search API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark",
            json={
                "user_requirements": user_requirements,
                "enable_search": True,
                "stream": True
            },
            stream=True
        )
        response.raise_for_status()
        
        for delta in parse_json_stream(response):
            yield delta
            
    except Exception as e:
        raise e


def get_stream_response_with_docs(uploaded_file, user_requirements):
    """Get streaming response from the documents API using file upload"""
    try:
        # Prepare the file for upload
        files = {
            'uploaded_file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
        }
        
        # Prepare form data
        data = {
            'user_requirements': user_requirements,
            'stream': 'true'  # Form data requires string values
        }
        
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark-from-docs",
            files=files,
            data=data,
            stream=True
        )
        response.raise_for_status()
        
        for delta in parse_json_stream(response):
            yield delta
            
    except Exception as e:
        raise e


def get_edit_stream_response(current_xmindmark, edit_request, use_search=False, original_requirements=""):
    """Get streaming response from edit API (with or without search)"""
    try:
        payload = {
            "current_xmindmark": current_xmindmark,
            "edit_request": edit_request,
            "enable_search": use_search,
            "original_user_requirements": original_requirements
        }
        
        response = requests.post(
            f"{API_BASE_URL}/edit-xmindmark",
            json=payload,
            stream=True
        )
        response.raise_for_status()
        
        for delta in parse_json_stream(response):
            yield delta
            
    except Exception as e:
        raise e


def get_non_streaming_response(user_requirements, enable_search=False):
    """Get non-streaming response"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark",
            json={
                "user_requirements": user_requirements,
                "enable_search": enable_search,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()["xmindmark"]
    except Exception as e:
        raise e


def get_non_streaming_docs_response(uploaded_file, user_requirements):
    """Get non-streaming response for docs using file upload"""
    try:
        # Prepare the file for upload
        files = {
            'uploaded_file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
        }
        
        # Prepare form data
        data = {
            'user_requirements': user_requirements,
            'stream': 'false'  # Form data requires string values
        }
        
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark-from-docs",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()["xmindmark"]
    except Exception as e:
        raise e


def render_svg(svg_bytes):
    """Renders the given SVG bytes as HTML"""
    try:
        # Convert bytes to string if needed
        if isinstance(svg_bytes, bytes):
            svg_string = svg_bytes.decode('utf-8')
        else:
            svg_string = svg_bytes
        
        # Encode to base64
        b64 = base64.b64encode(svg_string.encode('utf-8')).decode("utf-8")
        html = f'<img src="data:image/svg+xml;base64,{b64}" style="width: 100%; height: auto;"/>'
        st.markdown(html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Lỗi render SVG: {str(e)}")


def get_svg_bytes(content):
    """Get SVG bytes from API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/to-svg",
            json={"content": content}
        )
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise e


def get_xmind_bytes(content):
    """Get XMind file bytes from API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/to-xmind",
            json={"content": content}
        )
        response.raise_for_status()
        return response.content
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
    
    # Streaming mode toggle
    st.divider()
    streaming_mode = st.toggle(
        "🌊 Streaming mode", 
        value=True,
        help="Bật để xem quá trình tạo mindmap real-time, tắt để đợi kết quả hoàn chỉnh"
    )
    
    uploaded_file = None
    if mode == "docs":
        st.markdown("##### 📁 Chọn file")
        uploaded_file = st.file_uploader(
            "Tải lên file tài liệu",
            type=['pdf', 'docx', 'md'],
            help="Chọn file PDF, DOCX hoặc MD để tóm tắt",
            label_visibility="collapsed"
        )
        if uploaded_file:
            st.success(f"✅ Đã chọn file: {uploaded_file.name}")

    # Mode indicator
    st.divider()
    if mode == "docs":
        st.info("📄 **Chế độ**: Từ tài liệu")
    elif mode == "search":
        st.info("🔍 **Chế độ**: Tìm kiếm")
    else:
        st.info("💭 **Chế độ**: Cơ bản")

    if streaming_mode:
        st.info("🌊 **Streaming**: Bật")
    else:
        st.info("⏸️ **Streaming**: Tắt")

    # Validation
    can_generate = False
    error_message = ""
    if not user_requirements.strip():
        error_message = "⚠️ Vui lòng nhập yêu cầu"
    elif mode == "docs" and not uploaded_file:
        error_message = "⚠️ Vui lòng tải lên file tài liệu"
    else:
        can_generate = True

    if error_message:
        st.warning(error_message)

    # Single generate button
    if st.button("🚀 Tạo mind map", disabled=not can_generate, type="primary"):
        # Clear previous states
        for key in ["xmindmark", "edited_xmindmark", "svg_bytes", "xmind_bytes", "previous_edited_xmindmark"]:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state["generating"] = True
        st.session_state["current_mode"] = mode
        st.session_state["streaming_enabled"] = streaming_mode
        st.session_state["generation_uploaded_file"] = uploaded_file  # Store the uploaded file
        st.session_state["generation_requirements"] = user_requirements
        st.rerun()


# --- MAIN DISPLAY ---
col1, col2 = st.columns([2, 1])

# --- Chỉnh sửa nội dung ---
with col2:
    st.subheader("📄 Nội dung XMindMark")
    
    # Handle generation
    if st.session_state.get("generating", False):
        current_mode = st.session_state.get("current_mode", "basic")
        streaming_enabled = st.session_state.get("streaming_enabled", True)
        
        generation_uploaded_file = st.session_state.get("generation_uploaded_file")
        generation_requirements = st.session_state.get("generation_requirements")
        
        if streaming_enabled:
            # Streaming mode
            if current_mode == "docs":
                st.markdown("### 🤖 Đang tạo XMindMark từ tài liệu...")
            elif current_mode == "search":
                st.markdown("### 🤖 Đang tìm kiếm và tạo XMindMark...")
            else:
                st.markdown("### 🤖 Đang tạo XMindMark...")
                
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Choose the appropriate API endpoint based on mode
                if current_mode == "docs":
                    stream_response = get_stream_response_with_docs(generation_uploaded_file, generation_requirements)
                elif current_mode == "search":
                    stream_response = get_stream_response_with_search(generation_requirements)
                else:  # basic mode
                    stream_response = get_stream_response_no_docs(generation_requirements)
                
                for delta in stream_response:
                    full_response += delta
                    message_placeholder.markdown(f"```\n{full_response}▌\n```")
                
                # Final response without cursor
                message_placeholder.markdown(f"```\n{full_response}\n```")
                
                # Store the generated content
                st.session_state["xmindmark"] = full_response
                st.session_state["edited_xmindmark"] = full_response
                st.session_state["generating"] = False
                
                # Generate SVG bytes
                try:
                    svg_bytes = get_svg_bytes(full_response)
                    st.session_state["svg_bytes"] = svg_bytes
                    st.success("✅ Mind map đã tạo và hiển thị!")
                except Exception as e:
                    st.error(f"❌ Không tạo được SVG: {str(e)}")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Lỗi kết nối API: {str(e)}")
                st.session_state["generating"] = False
        else:
            # Non-streaming mode
            if current_mode == "docs":
                st.markdown("### 🤖 Đang tạo XMindMark từ tài liệu... (chờ kết quả hoàn chỉnh)")
            elif current_mode == "search":
                st.markdown("### 🤖 Đang tìm kiếm và tạo XMindMark... (chờ kết quả hoàn chỉnh)")
            else:
                st.markdown("### 🤖 Đang tạo XMindMark... (chờ kết quả hoàn chỉnh)")
            
            with st.spinner("Đang xử lý..."):
                try:
                    if current_mode == "docs":
                        full_response = get_non_streaming_docs_response(generation_uploaded_file, generation_requirements)
                    elif current_mode == "search":
                        full_response = get_non_streaming_response(generation_requirements, enable_search=True)
                    else:  # basic mode
                        full_response = get_non_streaming_response(generation_requirements, enable_search=False)
                    
                    st.markdown(f"```\n{full_response}\n```")
                    
                    # Store the generated content
                    st.session_state["xmindmark"] = full_response
                    st.session_state["edited_xmindmark"] = full_response
                    st.session_state["generating"] = False
                    
                    # Generate SVG bytes
                    try:
                        svg_bytes = get_svg_bytes(full_response)
                        st.session_state["svg_bytes"] = svg_bytes
                        st.success("✅ Mind map đã tạo và hiển thị!")
                    except Exception as e:
                        st.error(f"❌ Không tạo được SVG: {str(e)}")
                    
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
            
            for delta in edit_stream:
                full_edit_response += delta
                edit_placeholder.markdown(f"```\n{full_edit_response}▌\n```")
            
            # Final response without cursor
            edit_placeholder.markdown(f"```\n{full_edit_response}\n```")
            
            # Store the edited content
            st.session_state["edited_xmindmark"] = full_edit_response
            st.session_state["editing_with_ai"] = False
            
            # Generate new SVG bytes
            try:
                svg_bytes = get_svg_bytes(full_edit_response)
                st.session_state["svg_bytes"] = svg_bytes
                st.success("✅ AI đã chỉnh sửa thành công!")
            except Exception as e:
                st.error(f"❌ Không tạo được SVG: {str(e)}")
            
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
                        svg_bytes = get_svg_bytes(edited)
                        st.session_state["svg_bytes"] = svg_bytes
                        st.success("✅ Đã cập nhật hình ảnh!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Lỗi tạo SVG: {str(e)}")
            
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
    svg_bytes = st.session_state.get("svg_bytes")

    if svg_bytes:
        try:
            # Display SVG using custom render function
            render_svg(svg_bytes)
        except Exception as e:
            st.error(f"❌ Lỗi khi hiển thị SVG: {str(e)}")
    elif st.session_state.get("generating", False) or st.session_state.get("editing_with_ai", False):
        st.info("⏳ Đang xử lý sơ đồ mind map...")
    else:
        st.info("📋 Sơ đồ mind map sẽ hiển thị ở đây sau khi tạo.")

# --- Nút tải về ---
if st.session_state.get("edited_xmindmark") and not st.session_state.get("generating", False) and not st.session_state.get("editing_with_ai", False):
    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        svg_bytes = st.session_state.get("svg_bytes")
        if svg_bytes:
            st.download_button(
                label="📥 Tải ảnh SVG",
                data=svg_bytes,
                file_name=f"{extract_snake_case_title(st.session_state['edited_xmindmark'])}.svg",
                mime="image/svg+xml"
            )

    with col_dl2:
        edited_content = st.session_state.get("edited_xmindmark")
        prev_content = st.session_state.get("previous_edited_xmindmark")

        # Nếu nội dung thay đổi hoặc chưa có xmind_bytes thì tạo lại file
        if edited_content != prev_content or "xmind_bytes" not in st.session_state:
            try:
                xmind_bytes = get_xmind_bytes(edited_content)
                st.session_state["xmind_bytes"] = xmind_bytes
                st.session_state["previous_edited_xmindmark"] = edited_content  # cập nhật bản ghi
            except Exception as e:
                st.error(f"❌ Lỗi khi tạo file XMind: {str(e)}")

        # Hiển thị nút tải file
        xmind_bytes = st.session_state.get("xmind_bytes")
        if xmind_bytes:
            st.download_button(
                label="📥 Tải file XMind",
                data=xmind_bytes,
                file_name=f"{extract_snake_case_title(st.session_state['edited_xmindmark'])}.svg",
                mime="application/octet-stream"
            )