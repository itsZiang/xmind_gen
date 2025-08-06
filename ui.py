import streamlit as st
import requests
from core.text_processing import extract_text_from_file
from io import BytesIO
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import numpy as np
import wave
import tempfile
import os, logging
import re
import unicodedata
import base64

logger = logging.getLogger(__name__)
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
    
def get_stream_response_from_audio(audio_file, user_requirements):
    try:
        if hasattr(audio_file, 'getvalue'):
            audio_content = audio_file.getvalue()
            filename = getattr(audio_file, 'name', 'audio.wav')
        elif hasattr(audio_file, 'read'):
            audio_file.seek(0)  
            audio_content = audio_file.read()
            filename = getattr(audio_file, 'name', 'audio.wav')
        else:
            raise Exception("Invalid audio file format")
        
        if not audio_content:
            raise Exception("Audio file is empty")
        
        from io import BytesIO
        audio_buffer = BytesIO(audio_content)
        audio_buffer.name = filename
        
        files = {"audio_file": (filename, audio_buffer, "audio/wav")}
        data = {"user_requirements": user_requirements}
        
        response = requests.post(
            f"{API_BASE_URL}/generate-xmindmark-from-audio",
            files=files,
            data=data,
            stream=True,
            timeout=300  
        )
        
        if response.status_code != 200:
            error_detail = response.text
            raise Exception(f"API Error {response.status_code}: {error_detail}")
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
                
    except Exception as e:
        logger.error(f"Audio streaming error: {str(e)}")
        raise e
    
def transcribe_audio_file(audio_file):
    try:
        if hasattr(audio_file, 'getvalue'):
            audio_content = audio_file.getvalue()
            filename = getattr(audio_file, 'name', 'audio.wav')
        elif hasattr(audio_file, 'read'):
            audio_file.seek(0)  # Reset to beginning
            audio_content = audio_file.read()
            filename = getattr(audio_file, 'name', 'audio.wav')
        else:
            raise Exception("Invalid audio file format")
        
        if not audio_content:
            raise Exception("Audio file is empty")
        
        from io import BytesIO
        audio_buffer = BytesIO(audio_content)
        audio_buffer.name = filename
        
        files = {"audio_file": (filename, audio_buffer, "audio/wav")}
        
        response = requests.post(
            f"{API_BASE_URL}/transcribe-audio",
            files=files,
            timeout=300  
        )
        
        if response.status_code != 200:
            error_detail = response.text
            raise Exception(f"API Error {response.status_code}: {error_detail}")
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise e

# --- SIDEBAR ---
with st.sidebar:
    st.header("📌 Nhập yêu cầu & tùy chọn")

    # User requirements - always visible
    user_requirements = st.text_area("Yêu cầu của bạn", height=150)

    st.divider()
    
    st.subheader("🔧 Tùy chọn tạo mindmap")
    
    mode = st.radio(
        "Chọn chế độ tạo mindmap",
        options=["basic", "docs", "audio", "search"],
        format_func=lambda x: {
            "basic": "💭 Cơ bản (không tài liệu)",
            "docs": "📄 Từ tài liệu",
            "audio": "🎤 Từ giọng nói",
            "search": "🔍 Tìm kiếm thông tin"
        }[x],
        help="Chỉ chọn một chế độ duy nhất"
    )

    uploaded_file = None
    audio_file = None
    text = None
    transcribed_text = None

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

    elif mode == "audio":
        st.markdown("##### 🎤 Chọn nguồn âm thanh")
        
        audio_source = st.radio(
            "Nguồn âm thanh:",
            options=["upload", "record"],
            format_func=lambda x: {
                "upload": "📁 Tải file âm thanh",
                "record": "🎙️ Thu âm trực tiếp"
            }[x],
            help="Chọn cách nhập âm thanh"
        )
        
        if audio_source == "upload":
            st.markdown("**Tải file âm thanh:**")
            uploaded_audio_file = st.file_uploader(
                "Chọn file âm thanh",
                type=['wav', 'mp3', 'm4a', 'ogg', 'flac', 'aac'],
                help="Hỗ trợ: WAV, MP3, M4A, OGG, FLAC, AAC (tối đa 25MB)",
                label_visibility="collapsed",
                key="audio_uploader"
            )
            
            if uploaded_audio_file:
                # Validate file size
                if uploaded_audio_file.size > 25 * 1024 * 1024:
                    st.error("❌ File quá lớn! Vui lòng chọn file nhỏ hơn 25MB.")
                    audio_file = None
                else:
                    audio_file = uploaded_audio_file
                    st.success(f"✅ Tải file âm thanh thành công: {audio_file.name}")
                    st.info(f"📊 Kích thước: {audio_file.size / (1024*1024):.1f} MB")
                    
                    # Option to transcribe first
                    if st.button("🎯 Xem nội dung chuyển đổi", help="Chuyển đổi âm thanh thành văn bản để xem trước"):
                        with st.spinner("🔄 Đang chuyển đổi âm thanh..."):
                            try:
                                result = transcribe_audio_file(audio_file)
                                transcribed_text = result["transcribed_text"]
                                st.session_state["transcribed_preview"] = transcribed_text
                                st.success("✅ Chuyển đổi thành công!")
                            except Exception as e:
                                st.error(f"❌ Lỗi chuyển đổi: {str(e)}")
                    
                    # Show transcribed preview if available
                    if "transcribed_preview" in st.session_state:
                        with st.expander("📝 Nội dung đã chuyển đổi", expanded=True):
                            st.text_area(
                                "Văn bản từ âm thanh:",
                                value=st.session_state["transcribed_preview"],
                                height=150,
                                disabled=True
                            )
        
        elif audio_source == "record":
            st.markdown("**Thu âm trực tiếp:**")
            st.info("🎙️ Click 'START' để bắt đầu thu âm, 'STOP' để kết thúc")
            
            # WebRTC audio recorder
            webrtc_ctx = webrtc_streamer(
                key="audio-recorder",
                mode=WebRtcMode.SENDONLY,
                audio_receiver_size=1024,
                media_stream_constraints={"video": False, "audio": True},
                rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
            )
            
            if webrtc_ctx.audio_receiver:
                st.success("🎤 Đang thu âm... Nói vào microphone")
                
                # Process recorded audio
                if st.button("🔚 Kết thúc và xử lý"):
                    audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
                    if audio_frames:
                        # Convert frames to audio data
                        sound_chunk = np.array([frame.to_ndarray() for frame in audio_frames])
                        if sound_chunk.size > 0:
                            # Save to temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                                # Simple WAV file creation
                                with wave.open(tmp_file.name, 'wb') as wav_file:
                                    wav_file.setnchannels(1)  # mono
                                    wav_file.setsampwidth(2)  # 16-bit
                                    wav_file.setframerate(16000)  # 16kHz
                                    wav_file.writeframes(sound_chunk.tobytes())
                                
                                # Read back as file-like object
                                with open(tmp_file.name, 'rb') as f:
                                    audio_data = f.read()
                                
                                # Create a file-like object for the audio
                                audio_file = BytesIO(audio_data)
                                audio_file.name = "recorded_audio.wav"
                                
                                # Clean up temp file
                                os.unlink(tmp_file.name)
                                
                                st.success("✅ Thu âm hoàn tất!")
                        else:
                            st.warning("⚠️ Không có dữ liệu âm thanh")
                    else:
                        st.warning("⚠️ Không thu được âm thanh")

    # Mode indicator
    st.divider()
    if mode == "docs":
        st.info("📄 **Chế độ**: Từ tài liệu")
        current_mode = "docs_only"
    elif mode == "search":
        st.info("🔍 **Chế độ**: Tìm kiếm")
        current_mode = "search_only"
    elif mode == "audio":
        st.info("🎤 **Chế độ**: Từ giọng nói")
        current_mode = "audio_only"
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
    elif mode == "audio" and not audio_file:
        error_message = "⚠️ Vui lòng tải lên file âm thanh hoặc thu âm"
    else:
        can_generate = True

    # Single generate button
    if st.button("🚀 Tạo mind map", disabled=not can_generate, type="primary"):
        for key in ["xmindmark", "edited_xmindmark", "svg_bytes", "xmind_bytes", "previous_edited_xmindmark", "transcribed_preview"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["generating"] = True
        st.session_state["current_mode"] = current_mode
        st.session_state["generation_text"] = text if mode == "docs" else None
        st.session_state["generation_audio_file"] = audio_file if mode == "audio" else None
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
            generation_audio_file = st.session_state.get("generation_audio_file")
            generation_requirements = st.session_state.get("generation_requirements")
            generation_search_mode = st.session_state.get("generation_search_mode", False)
            
            if current_mode == "docs_only":
                stream_response = get_stream_response_with_docs(generation_text, generation_requirements)
            elif current_mode == "search_only":
                stream_response = get_stream_response_with_search(generation_requirements)
            elif current_mode == "audio_only":
                if generation_audio_file:
                    stream_response = get_stream_response_from_audio(generation_audio_file, generation_requirements)
                else:
                    raise Exception("No audio file provided")
            else:  
                stream_response = get_stream_response_no_docs(generation_requirements)
            
            for chunk in stream_response:
                full_response += chunk.decode("utf-8")
                message_placeholder.markdown(f"```\n{full_response}▌\n```")
            
            message_placeholder.markdown(f"```\n{full_response}\n```")
            
            st.session_state["xmindmark"] = full_response
            st.session_state["edited_xmindmark"] = full_response
            st.session_state["generating"] = False
            
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
                # placeholder="Ví dụ:\n- Thêm thông tin về ban lãnh đạo MISA\n- Tìm số liệu mới nhất về doanh thu\n- Bổ sung chi tiết về sản phẩm mới\n- Cập nhật thông tin công nghệ mới nhất",
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
                file_name=f"{extract_snake_case_title(st.session_state['edited_xmindmark'])}.xmind",
                mime="application/octet-stream"
            )