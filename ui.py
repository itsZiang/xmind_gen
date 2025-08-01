
# ui_improved.py
import streamlit as st
import requests
from core.text_processing import extract_text_from_file
from io import BytesIO
import cairosvg
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="🧠 XMind Generator with LangGraph", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
.workflow-status {
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
}
.status-success { background-color: #d4edda; color: #155724; }
.status-warning { background-color: #fff3cd; color: #856404; }
.status-error { background-color: #f8d7da; color: #721c24; }
.status-info { background-color: #cce7ff; color: #004085; }

.workflow-step {
    padding: 8px 12px;
    margin: 5px 0;
    border-left: 4px solid #007bff;
    background-color: #f8f9fa;
}
.step-completed { border-left-color: #28a745; }
.step-failed { border-left-color: #dc3545; }
.step-current { border-left-color: #ffc107; background-color: #fff3cd; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 Tạo Mind Map Tự Động với LangGraph")
st.markdown("*Powered by LangGraph Workflow Engine*")

# Initialize session state
if "workflow_history" not in st.session_state:
    st.session_state.workflow_history = []
if "current_workflow_status" not in st.session_state:
    st.session_state.current_workflow_status = None

def display_workflow_status(status_data):
    """Hiển thị trạng thái workflow"""
    if not status_data:
        return
    
    status = status_data.get("status", "unknown")
    success = status_data.get("success", False)
    errors = status_data.get("errors", [])
    
    # Determine status class
    if success:
        status_class = "status-success"
        icon = "✅"
    elif errors:
        status_class = "status-error" 
        icon = "❌"
    else:
        status_class = "status-info"
        icon = "ℹ️"
    
    st.markdown(f"""
    <div class="workflow-status {status_class}">
        {icon} <strong>Workflow Status:</strong> {status.replace('_', ' ').title()}
    </div>
    """, unsafe_allow_html=True)
    
    if errors:
        st.error("**Errors encountered:**")
        for error in errors:
            st.error(f"• {error}")

def display_workflow_steps(status):
    """Hiển thị các bước workflow"""
    steps = [
        ("validate_input", "Input Validation"),
        ("generate_xmindmark", "Generate XMindMark"),
        ("validate_xmindmark", "Validate Content"),
        ("convert_to_svg", "Convert to SVG"),
        ("convert_to_xmind", "Convert to XMind"),
        ("complete", "Complete")
    ]
    
    st.markdown("### 📋 Workflow Progress")
    
    for step_id, step_name in steps:
        if status == step_id or (status == "completed" and step_id in ["validate_input", "generate_xmindmark", "validate_xmindmark", "convert_to_svg"]):
            step_class = "step-completed"
            icon = "✅"
        elif step_id in ["input_validation_failed", "generation_failed", "xmindmark_validation_failed", "svg_conversion_failed"]:
            step_class = "step-failed"
            icon = "❌"
        elif status.endswith("_failed") and step_id in status:
            step_class = "step-failed"
            icon = "❌"
        else:
            step_class = "workflow-step"
            icon = "⏳"
        
        st.markdown(f"""
        <div class="workflow-step {step_class}">
            {icon} {step_name}
        </div>
        """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📌 Input & Configuration")
    
    # Workflow mode selection
    workflow_mode = st.radio(
        "🔧 Processing Mode",
        ["Standard Workflow", "Legacy Mode"],
        help="Standard Workflow sử dụng LangGraph với validation và error handling. Legacy Mode sử dụng cách xử lý truyền thống."
    )
    
    st.divider()
    
    user_requirements = st.text_area(
        "📝 Yêu cầu của bạn", 
        height=150,
        placeholder="Ví dụ: Tạo mind map về các khái niệm chính, sắp xếp theo độ ưu tiên, bao gồm ví dụ cụ thể..."
    )
    
    uploaded_file = st.file_uploader(
        "📄 Tải lên file tài liệu",
        type=['pdf', 'docx', 'md'],
        help="Chọn file PDF, DOCX hoặc MD để tóm tắt"
    )
    
    if uploaded_file:
        try:
            text = extract_text_from_file(uploaded_file)
            st.success(f"✅ Tải file thành công! ({len(text)} ký tự)")
            
            # Preview text
            with st.expander("👀 Preview nội dung"):
                st.text_area("Content preview", value=text[:500] + "..." if len(text) > 500 else text, height=100, disabled=True)
                
        except Exception as e:
            st.error(f"❌ Lỗi xử lý file: {e}")
            text = None
    else:
        text = None
    
    st.divider()
    
    # Generation button
    if st.button("🚀 Tạo mind map", type="primary", use_container_width=True) and user_requirements and text:
        with st.spinner("🔄 Đang xử lý workflow..."):
            try:
                # Choose API endpoint based on mode
                if workflow_mode == "Standard Workflow":
                    endpoint = f"{API_BASE_URL}/generate-xmindmark-workflow"
                else:
                    endpoint = f"{API_BASE_URL}/generate-xmindmark"
                
                res = requests.post(endpoint, json={
                    "text": text,
                    "user_requirements": user_requirements
                })
                
                if res.status_code == 200:
                    response_data = res.json()
                    
                    if workflow_mode == "Standard Workflow":
                        # Handle workflow response
                        if response_data.get("success"):
                            st.session_state["xmindmark"] = response_data.get("xmindmark", "")
                            st.session_state["edited_xmindmark"] = response_data.get("xmindmark", "")
                            st.session_state["svg_url"] = response_data.get("svg_url", "")
                            st.session_state["xmind_file_url"] = response_data.get("xmind_file_url", "")
                            st.session_state["current_workflow_status"] = response_data
                            
                            # Add to history
                            st.session_state.workflow_history.append({
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "action": "Generate",
                                "status": "Success",
                                "details": response_data
                            })
                            
                            st.success("✅ Mind map đã được tạo thành công với workflow!")
                        else:
                            st.session_state["current_workflow_status"] = response_data
                            st.error("❌ Workflow thất bại!")
                    else:
                        # Handle legacy response
                        xmindmark = response_data.get("xmindmark", "")
                        st.session_state["xmindmark"] = xmindmark
                        st.session_state["edited_xmindmark"] = xmindmark
                        
                        # Generate SVG separately for legacy mode
                        svg_res = requests.post(f"{API_BASE_URL}/to-svg", json={"content": xmindmark})
                        if svg_res.status_code == 200:
                            svg_data = svg_res.json()
                            st.session_state["svg_url"] = svg_data.get("svg_url", "")
                        
                        st.success("✅ Mind map đã được tạo (Legacy mode)!")
                        
                else:
                    st.error(f"❌ API Error: {res.status_code}\n{res.text}")
                    
            except Exception as e:
                st.error(f"❌ Connection Error: {str(e)}")
    
    elif user_requirements and not text:
        st.warning("⚠️ Vui lòng tải lên file tài liệu")
    elif text and not user_requirements:
        st.warning("⚠️ Vui lòng nhập yêu cầu của bạn")

# Main content area
col1, col2 = st.columns([2, 1])

# Left column - Display and workflow status
with col1:
    st.subheader("🧩 Sơ đồ Mindmap")
    
    # Display workflow status if available
    if st.session_state.current_workflow_status:
        display_workflow_status(st.session_state.current_workflow_status)
        
        # Show workflow steps
        status = st.session_state.current_workflow_status.get("status", "")
        if status:
            display_workflow_steps(status)
    
    # Display SVG
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
                st.error(f"❌ Không thể tải SVG: {svg_response.status_code}")
        except Exception as e:
            st.error(f"❌ Lỗi hiển thị SVG: {str(e)}")
    else:
        st.info("👆 Tạo mind map để xem kết quả tại đây")

# Right column - Edit and content management
with col2:
    st.subheader("📄 Quản lý nội dung")
    
    # Workflow history
    if st.session_state.workflow_history:
        with st.expander("📊 Lịch sử Workflow", expanded=False):
            for i, entry in enumerate(reversed(st.session_state.workflow_history[-5:])):  # Show last 5
                status_icon = "✅" if entry["status"] == "Success" else "❌"
                st.markdown(f"**{status_icon} {entry['timestamp']}** - {entry['action']}")
                if entry.get("details", {}).get("errors"):
                    st.caption(f"Errors: {len(entry['details']['errors'])}")
    
    st.divider()
    
    # AI-powered editing
    st.markdown("### 🤖 Chỉnh sửa bằng AI")
    with st.form(key="llm_edit_form", clear_on_submit=True):
        edit_request = st.text_area(
            "Yêu cầu chỉnh sửa:",
            placeholder="Ví dụ:\n- Thêm chi tiết cho nhánh 'Phương pháp'\n- Xóa nhánh không cần thiết\n- Sắp xếp lại theo độ ưu tiên\n- Rút gọn các từ khóa dài",
            height=100,
            key="edit_request_input"
        )
        
        col_edit_btn, col_edit_mode = st.columns([1, 1])
        with col_edit_btn:
            edit_with_llm = st.form_submit_button("✨ Chỉnh sửa", type="secondary")
        with col_edit_mode:
            edit_workflow_mode = st.checkbox("Workflow mode", value=True, help="Sử dụng workflow cho chỉnh sửa")
    
    if edit_with_llm and edit_request.strip():
        current_content = st.session_state.get("edited_xmindmark", "")
        if not current_content:
            st.warning("⚠️ Chưa có nội dung để chỉnh sửa")
        else:
            with st.spinner("🤖 AI đang chỉnh sửa..."):
                try:
                    # Choose endpoint based on mode
                    if edit_workflow_mode:
                        endpoint = f"{API_BASE_URL}/edit-xmindmark-workflow"
                    else:
                        endpoint = f"{API_BASE_URL}/edit-xmindmark"
                    
                    edit_response = requests.post(endpoint, json={
                        "current_xmindmark": current_content,
                        "edit_request": edit_request
                    })
                    
                    if edit_response.status_code == 200:
                        edit_data = edit_response.json()
                        
                        if edit_workflow_mode:
                            # Handle workflow response
                            if edit_data.get("success"):
                                edited_content = edit_data.get("edited_xmindmark", "")
                                st.session_state["edited_xmindmark"] = edited_content
                                st.session_state["svg_url"] = edit_data.get("svg_url", "")
                                st.session_state["current_workflow_status"] = edit_data
                                
                                # Add to history
                                st.session_state.workflow_history.append({
                                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                                    "action": "Edit",
                                    "status": "Success",
                                    "details": edit_data
                                })
                                
                                st.success("✅ Chỉnh sửa thành công với workflow!")
                                st.rerun()
                            else:
                                st.session_state["current_workflow_status"] = edit_data
                                st.error("❌ Workflow chỉnh sửa thất bại!")
                        else:
                            # Handle legacy response
                            edited_content = edit_data.get("edited_xmindmark", "")
                            if edited_content != current_content:
                                st.session_state["edited_xmindmark"] = edited_content
                                
                                # Update SVG
                                svg_res = requests.post(f"{API_BASE_URL}/to-svg", json={
                                    "content": edited_content
                                })
                                if svg_res.status_code == 200:
                                    svg_data = svg_res.json()
                                    st.session_state["svg_url"] = svg_data.get("svg_url", "")
                                
                                st.success("✅ Chỉnh sửa thành công!")
                                st.rerun()
                            else:
                                st.info("ℹ️ Không có thay đổi nào.")
                    else:
                        st.error(f"❌ Lỗi chỉnh sửa: {edit_response.status_code}")
                        
                except Exception as e:
                    st.error(f"❌ Lỗi kết nối: {str(e)}")
    
    st.divider()
    
    # Manual editing
    st.markdown("### ✏️ Chỉnh sửa thủ công")
    xmindmark = st.session_state.get("edited_xmindmark")
    if xmindmark:
        edited = st.text_area(
            "Nội dung XMindMark:", 
            value=xmindmark, 
            height=300,
            help="Chỉnh sửa trực tiếp nội dung XMindMark"
        )
        
        col_confirm, col_validate = st.columns([1, 1])
        with col_confirm:
            if st.button("✔️ Cập nhật", use_container_width=True):
                st.session_state["edited_xmindmark"] = edited
                try:
                    res = requests.post(f"{API_BASE_URL}/to-svg", json={
                        "content": edited
                    })
                    if res.status_code == 200:
                        svg_data = res.json()
                        st.session_state["svg_url"] = svg_data.get("svg_url", "")
                        st.success("✅ Đã cập nhật!")
                        st.rerun()
                    else:
                        st.error(f"❌ Lỗi chuyển SVG: {res.status_code}")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
        
        with col_validate:
            if st.button("🔍 Validate", use_container_width=True):
                # Basic validation
                lines = edited.strip().split('\n')
                issues = []
                
                if len(lines) < 2:
                    issues.append("Cần ít nhất 2 dòng (tiêu đề + nội dung)")
                
                has_branches = any(line.strip().startswith('- ') for line in lines[1:])
                if not has_branches:
                    issues.append("Cần có nhánh chính bắt đầu với '- '")
                
                if issues:
                    for issue in issues:
                        st.warning(f"⚠️ {issue}")
                else:
                    st.success("✅ Format hợp lệ!")
    else:
        st.info("📝 Chưa có nội dung để chỉnh sửa")

# Download section
if st.session_state.get("edited_xmindmark"):
    st.markdown("---")
    st.subheader("📥 Tải xuống")
    
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    
    # Download SVG
    with col_dl1:
        svg_url = st.session_state.get("svg_url")
        if svg_url:
            try:
                response = requests.get(f"http://localhost:8000{svg_url}")
                if response.status_code == 200:
                    st.download_button(
                        label="📥 Tải SVG",
                        data=response.content,
                        file_name=f"mindmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                        mime="image/svg+xml",
                        use_container_width=True
                    )
                else:
                    st.error("❌ Không thể tải SVG")
            except Exception as e:
                st.error(f"❌ Lỗi tải SVG: {str(e)}")
    
    # Download XMindMark
    with col_dl2:
        xmindmark_content = st.session_state.get("edited_xmindmark", "")
        if xmindmark_content:
            st.download_button(
                label="📥 Tải XMindMark",
                data=xmindmark_content,
                file_name=f"mindmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmindmark",
                mime="text/plain",
                use_container_width=True
            )
    
    # Generate and download XMind file
    with col_dl3:
        if st.button("📥 Tạo XMind", use_container_width=True):
            with st.spinner("Đang tạo file XMind..."):
                try:
                    res = requests.post(f"{API_BASE_URL}/to-xmind", json={
                        "content": st.session_state["edited_xmindmark"]
                    })
                    if res.status_code == 200:
                        xmind_data = res.json()
                        xmind_file_url = xmind_data.get("xmind_file")
                        if xmind_file_url:
                            st.session_state["xmind_file_url"] = xmind_file_url
                            st.success("✅ File XMind đã sẵn sàng!")
                        else:
                            st.error("❌ Không tạo được file XMind")
                    else:
                        st.error(f"❌ Lỗi: {res.status_code}")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
        
        # Download XMind file if available
        xmind_file_url = st.session_state.get("xmind_file_url")
        if xmind_file_url:
            try:
                xmind_response = requests.get(f"http://localhost:8000{xmind_file_url}")
                if xmind_response.status_code == 200:
                    st.download_button(
                        label="💾 Tải XMind",
                        data=xmind_response.content,
                        file_name=f"mindmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xmind",
                        mime="application/octet-stream",
                        use_container_width=True
                    )
                else:
                    st.error("❌ Không thể tải file XMind")
            except Exception as e:
                st.error(f"❌ Lỗi tải XMind: {str(e)}")

# Footer with workflow info
st.markdown("---")
col_info1, col_info2 = st.columns(2)

with col_info1:
    st.markdown("""
    ### 🔧 Workflow Features
    - **Validation**: Tự động kiểm tra input và format
    - **Error Handling**: Xử lý lỗi và retry thông minh  
    - **Step Tracking**: Theo dõi từng bước xử lý
    - **Quality Control**: Đảm bảo chất lượng đầu ra
    """)

with col_info2:
    st.markdown("""
    ### 📊 Processing Modes
    - **Standard Workflow**: LangGraph với full validation
    - **Legacy Mode**: Xử lý truyền thống nhanh chóng
    - **Hybrid Edit**: Kết hợp cả hai phương pháp
    - **Manual Override**: Chỉnh sửa thủ công hoàn toàn
    """)

# Sidebar footer
with st.sidebar:
    st.markdown("---")
    if st.button("🗑️ Xóa lịch sử", use_container_width=True):
        st.session_state.workflow_history = []
        st.session_state.current_workflow_status = None
        st.success("✅ Đã xóa lịch sử!")
    
    st.markdown("### 📈 Session Stats")
    total_workflows = len(st.session_state.workflow_history)
    successful_workflows = len([w for w in st.session_state.workflow_history if w["status"] == "Success"])
    
    st.metric("Total Workflows", total_workflows)
    if total_workflows > 0:
        success_rate = (successful_workflows / total_workflows) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")