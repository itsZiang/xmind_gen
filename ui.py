import streamlit as st
import requests
from core.text_processing import extract_text_from_file

API_BASE_URL = "http://localhost:8000/api" 

st.set_page_config(page_title="XMind Generator", layout="wide")
st.title("🧠 Tạo Mind Map Tự Động")

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
        with st.spinner("Đang tạo mind map..."):
            res = requests.post(f"{API_BASE_URL}/generate-xmindmark", json={
                "text": text,
                "user_requirements": user_requirements
            })
            if res.status_code == 200:
                xmindmark = res.json()["xmindmark"]
                st.session_state["xmindmark"] = xmindmark
                st.session_state["edited_xmindmark"] = xmindmark

                # Gọi thêm /to-svg để lấy ảnh SVG
                svg_res = requests.post(f"{API_BASE_URL}/to-svg", json={"content": xmindmark})
                if svg_res.status_code == 200:
                    try:
                        svg_url = svg_res.json().get("svg_url")
                        st.session_state["svg_url"] = svg_url
                        st.success("✅ Mind map đã tạo và hiển thị!")
                    except Exception as e:
                        st.error(f"❌ Lỗi đọc SVG JSON: {e}\n{svg_res.text}")
                else:
                    st.error(f"❌ Không tạo được SVG: {svg_res.status_code}\n{svg_res.text}")
            else:
                st.error("❌ Gọi API thất bại!")

# --- MAIN DISPLAY ---
col1, col2 = st.columns([2, 1])

# --- Chỉnh sửa nội dung ---
with col2:
    st.subheader("📝 Nội dung XMindMark")
    xmindmark = st.session_state.get("edited_xmindmark")
    if xmindmark:
        edited = st.text_area("Chỉnh sửa nội dung", value=xmindmark, height=400)
        if st.button("✔️ Xác nhận chỉnh sửa"):
            st.session_state["edited_xmindmark"] = edited
            res = requests.post(f"{API_BASE_URL}/to-svg", json={
                "content": edited
            })
            if res.status_code == 200:
                try:
                    svg_url = res.json().get("svg_url")
                    st.session_state["svg_url"] = svg_url
                    st.success("✅ Đã cập nhật hình ảnh!")
                except Exception as e:
                    st.error(f"❌ Lỗi đọc JSON: {e}\nResponse text: {res.text}")
            else:
                st.error(f"❌ Lỗi chuyển SVG: {res.status_code}\n{res.text}")

# --- Hiển thị SVG ---
with col1:
    st.subheader("🧩 Sơ đồ Mindmap")
    svg_url = st.session_state.get("svg_url")

    if svg_url:
        try:
            svg_response = requests.get(f"http://localhost:8000{svg_url}")
            if svg_response.status_code == 200:
                # CÁCH 1: Dùng HTML components (Khuyên dùng)
                # svg_content = svg_response.text
                # st.components.v1.html(
                #     f"""
                #     <div style="
                #         width: 100%; 
                #         height: 600px; 
                #         display: flex; 
                #         justify-content: center; 
                #         align-items: center;
                #         border: 1px solid #ddd;
                #         border-radius: 8px;
                #         background: white;
                #         overflow: auto;
                #     ">
                #         {svg_content}
                #     </div>
                #     """,
                #     height=620,
                #     scrolling=False
                # )
                
                # CÁCH 2: Dùng markdown (Đơn giản hơn)
                # svg_content = svg_response.text
                # st.markdown(
                #     f"""
                #     <div style="
                #         width: 100%; 
                #         text-align: center; 
                #         padding: 20px;
                #         border: 1px solid #ddd;
                #         border-radius: 8px;
                #         background: white;
                #     ">
                #         {svg_content}
                #     </div>
                #     """,
                #     unsafe_allow_html=True
                # )
                
                # CÁCH 3: Lưu tạm và dùng st.image (Nếu cần fullscreen)
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

# --- Nút tải về ---
if st.session_state.get("edited_xmindmark"):
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

        if edited_content and "xmind_file_url" not in st.session_state:
            try:
                # Gọi API để tạo file XMind ngay khi có nội dung
                res = requests.post(f"{API_BASE_URL}/to-xmind", json={
                    "content": edited_content
                })
                if res.status_code == 200:
                    xmind_file_url = res.json()["xmind_file"]
                    st.session_state["xmind_file_url"] = xmind_file_url
                else:
                    st.error("❌ Không tạo được file .xmind")
            except Exception as e:
                st.error(f"❌ Lỗi khi tạo file XMind: {str(e)}")

        # Nếu file đã sẵn sàng, hiển thị nút tải
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