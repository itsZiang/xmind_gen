import streamlit as st
import requests
from core.text_processing import extract_text_from_file
from io import BytesIO

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="XMind Generator", layout="wide")
st.title("🧠 Tạo Mind Map Tự Động")

def get_stream_response(text, user_requirements):
    """Get streaming response from the API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark-langgraph-stream",
            json={"text": text, "user_requirements": user_requirements},
            stream=True
        )
        response.raise_for_status()
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
    except Exception as e:
        raise e

def get_edit_stream_response(current_xmindmark, edit_request):
    """Get streaming response from the edit API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/edit-xmindmark",
            json={"current_xmindmark": current_xmindmark, "edit_request": edit_request},
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
    st.header("📌 Nhập yêu cầu & tài liệu")

    user_requirements = st.text_area("Yêu cầu của bạn", height=150)

    uploaded_file = st.file_uploader(
        "📄 Tải lên file tài liệu",
        type=['pdf', 'docx', 'md'],
        help="Chọn file PDF, DOCX hoặc MD để tóm tắt"
    )

    if uploaded_file:
        try:
            text = extract_text_from_file(uploaded_file)
            st.success("✅ Tải file thành công!")
        except Exception as e:
            st.error(f"❌ Lỗi xử lý file: {e}")
            text = None
    else:
        text = None

    if st.button("🚀 Tạo mind map") and user_requirements and text:
        # Reset session state for new generation
        if "xmindmark" in st.session_state:
            del st.session_state["xmindmark"]
        if "edited_xmindmark" in st.session_state:
            del st.session_state["edited_xmindmark"]
        if "svg_url" in st.session_state:
            del st.session_state["svg_url"]
        
        st.session_state["generating"] = True
        st.rerun()

# --- MAIN DISPLAY ---
col1, col2 = st.columns([2, 1])

# --- Chỉnh sửa nội dung ---
with col2:
    st.subheader("📄 Nội dung XMindMark")
    
    # Handle streaming generation
    if st.session_state.get("generating", False):
        st.markdown("### 🤖 Đang tạo XMindMark...")
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Get streaming response
            stream_response = get_stream_response(text, user_requirements)
            
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
            # Get streaming edit response
            edit_stream = get_edit_stream_response(
                st.session_state.get("xmindmark", ""),
                st.session_state.get("edit_request", "")
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
        with st.form(key="llm_edit_form", clear_on_submit=True):
            edit_request = st.text_area(
                "Yêu cầu chỉnh sửa:",
                placeholder="Ví dụ:\n- Thêm chi tiết cho nhánh 'Phương pháp'\n- Xóa nhánh không cần thiết\n- Sắp xếp lại cấu trúc theo thứ tự logic\n- Rút gọn các từ khóa quá dài",
                height=160,
                key="edit_request_input"
            )
           
            edit_with_llm = st.form_submit_button("✨ Chỉnh sửa bằng AI", type="secondary")
       
        if edit_with_llm and edit_request.strip():
            # Store edit request in session state and start editing
            st.session_state["edit_request"] = edit_request
            st.session_state["editing_with_ai"] = True
            st.rerun()
        elif edit_with_llm and not edit_request.strip():
            st.warning("⚠️ Vui lòng nhập yêu cầu chỉnh sửa.")
        
    else:
        st.info("🎯 Vui lòng tải lên tài liệu và nhập yêu cầu để bắt đầu tạo mind map.")

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
        else:
            st.info("Đang xử lý tạo file XMind...")