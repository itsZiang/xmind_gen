def main():
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #4F46E5; font-size: 3rem; margin-bottom: 0.5rem;'>
            🧠 Agent AI - Tạo File XMindMark
        </h1>
        <p style='color: #6B7280; font-size: 1.2rem;'>
            Tóm tắt file PDF, DOCX, MD thành file XMindMark và hiển thị mindmap
        </p>
    </div>
    """, unsafe_allow_html=True)

    agent = MindMapAgent()

    with st.sidebar:
        st.header("🔧 Cấu hình")
        provider = st.selectbox("Provider:", ["openai", "g4f"], key="provider_select")
        st.session_state.selected_provider = provider
        
        api_key = ""
        if provider == "openai":
            api_key = st.text_input("OpenAI API Key:", type="password", value="ml-BRLNIyva65v4ltx1diADpn5mgY5ka9W9jpUX2DSy00iECWTiYe-AU7900zpWC0oJJDmI5qDFDXQxD5Ccc0m2lIQDqulCsPxlxfjRs")
        
        agent.llm_provider.initialize_client(provider, api_key)
        models = agent.llm_provider.get_available_models()
        model = st.selectbox("Model:", models, key="model_select")
        
        st.divider()
        
        st.subheader("🛠️ Trạng thái XMindMark CLI")
        cli_status = agent.check_xmindmark_cli()
        if cli_status:
            st.success("✅ XMindMark CLI đã được cài đặt")
            st.info("🎯 SVG và XMind sẽ được tạo bằng CLI chính thức")
        else:
            st.error("❌ XMindMark CLI chưa được cài đặt")
            st.warning("⚠️ SVG sẽ được tạo bằng phương thức dự phòng (Graphviz)")
            st.info("📋 Để cài đặt:\n```bash\nnpm install -g xmindmark\n```")
        
        st.divider()
        uploaded_file = st.file_uploader(
            "📄 Tải lên file",
            type=['pdf', 'docx', 'md'],
            help="Chọn file PDF, DOCX hoặc MD để tóm tắt"
        )
        
        if uploaded_file:
            st.subheader("📊 Thông tin file")
            st.write(f"**Tên file:** {uploaded_file.name}")
            st.write(f"**Kích thước:** {uploaded_file.size:,} bytes")
            st.write(f"**Loại:** {uploaded_file.type}")
            
        if st.session_state.extracted_text:
            st.subheader("📝 Văn bản gốc")
            with st.expander("Xem chi tiết", expanded=False):
                display_text = st.session_state.extracted_text[:2000] + "..." if len(st.session_state.extracted_text) > 2000 else st.session_state.extracted_text
                st.text_area(
                    "Nội dung (đã giới hạn):",
                    value=display_text,
                    height=200,
                    disabled=True
                )
        
        st.divider()
        st.subheader("📖 Hướng dẫn")
        st.markdown("""
        1. **Cấu hình LLM**: Chọn provider, nhập API Key (nếu cần) và chọn model
        2. **Cài đặt CLI**: Đảm bảo xmindmark CLI đã được cài đặt
        3. **Mô tả yêu cầu**: Nêu cách bạn muốn tóm tắt
        4. **Tải file**: Chọn file PDF, DOCX hoặc MD
        5. **Xử lý AI**: Tạo file XMindMark và ảnh mindmap
        6. **Chỉnh sửa**: Điều chỉnh nội dung file, ảnh sẽ tự cập nhật
        7. **Tải về**: Lưu file .xmind sử dụng CLI
        """)

    st.subheader("📝 Yêu cầu tóm tắt")
    user_requirements = st.text_area(
        "Mô tả cách bạn muốn AI tóm tắt và tạo bản đồ tư duy:",
        value=st.session_state.get('user_requirements', ''),
        height=100,
        placeholder="Ví dụ:\n- Tóm tắt bài giảng, tập trung vào các khái niệm chính\n- Phân loại báo cáo theo mục tiêu, phương pháp, kết quả\n- Trích xuất các ý tưởng chính từ tài liệu"
    )
    st.session_state.user_requirements = user_requirements
    
    if uploaded_file is not None and user_requirements.strip():
        if st.button("🚀 Tóm tắt và tạo file XMindMark", type="primary"):
            with st.spinner("🤖 AI đang tóm tắt và tạo file XMindMark..."):
                extracted_text = agent.extract_text_from_file(uploaded_file)
                
                if len(extracted_text) > 50000:
                    st.warning("⚠️ Văn bản quá dài, xử lý phần đầu tiên...")
                    extracted_text = extracted_text[:50000]
                st.session_state.extracted_text = extracted_text
                
                if extracted_text:
                    xmindmark_content = agent.process_text_with_llm(
                        extracted_text,
                        user_requirements,
                        provider,
                        api_key,
                        model
                    )
                    st.session_state.xmindmark_content = xmindmark_content
                    st.success("✅ Hoàn thành! File XMindMark và ảnh mindmap đã được tạo.")

    if st.session_state.xmindmark_content:
        st.divider()
        
        col_mindmap, col_content = st.columns([3, 2])
        
        with col_mindmap:
            st.subheader("🖼️ Bản Đồ Tư Duy")
            if st.session_state.mindmap_svg:
                if "xmindmark" in st.session_state.mindmap_svg.lower() or "xmlns" in st.session_state.mindmap_svg:
                    try:
                        st.image(f"data:image/svg+xml;base64,{base64.b64encode(st.session_state.mindmap_svg.encode('utf-8')).decode('utf-8')}", use_container_width=True)
                    except Exception as e:
                        st.error(f"Lỗi hiển thị SVG: {str(e)}")
                        st.text_area("SVG Content (debug):", value=st.session_state.mindmap_svg[:500] + "...", height=100)
                else:
                    st.error("SVG không hợp lệ")
            else:
                st.info("🔄 Đang tạo ảnh mindmap...")
        
        with col_content:
            st.subheader("📄 Chỉnh sửa XMindMark")
            
            st.markdown("### 🤖 Chỉnh sửa bằng AI")
            with st.form(key="llm_edit_form", clear_on_submit=True):
                edit_request = st.text_area(
                    "Yêu cầu chỉnh sửa:",
                    placeholder="Ví dụ:\n- Thêm chi tiết cho nhánh 'Phương pháp'\n- Xóa nhánh không cần thiết\n- Sắp xếp lại cấu trúc theo thứ tự logic\n- Rút gọn các từ khóa quá dài",
                    height=100,
                    key="edit_request_input"
                )
                
                col_edit_btn, col_edit_info = st.columns([1, 2])
                with col_edit_btn:
                    edit_with_llm = st.form_submit_button("✨ Chỉnh sửa bằng AI", type="secondary")
                with col_edit_info:
                    st.caption("💡 AI sẽ chỉnh sửa theo yêu cầu của bạn")
            
            if edit_with_llm and edit_request.strip():
                with st.spinner("🤖 AI đang chỉnh sửa XMindMark..."):
                    edited_content = agent.edit_xmindmark_with_llm(
                        st.session_state.xmindmark_content,
                        edit_request,
                        provider,
                        api_key,
                        model
                    )
                    
                    if edited_content != st.session_state.xmindmark_content:
                        st.session_state.xmindmark_content = edited_content
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        svg_content = agent.convert_xmindmark_to_svg_cli(edited_content, f"mindmap_ai_edit_{timestamp}")
                        st.session_state.mindmap_svg = svg_content
                        st.success("✅ AI đã chỉnh sửa thành công!")
                        st.rerun()
                    else:
                        st.info("ℹ️ Không có thay đổi nào được thực hiện.")
            elif edit_with_llm and not edit_request.strip():
                st.warning("⚠️ Vui lòng nhập yêu cầu chỉnh sửa.")
            
            st.divider()
            
            st.markdown("### ✏️ Chỉnh sửa thủ công")
            with st.form(key="manual_edit_form", clear_on_submit=False):
                edited_content = st.text_area(
                    "Nội dung file XMindMark (có thể chỉnh sửa):",
                    value=st.session_state.xmindmark_content,
                    height=300,
                    help="Nhấn Ctrl+Enter hoặc click 'Cập nhật' để áp dụng thay đổi"
                )
                
                col_update, col_auto = st.columns([1, 2])
                with col_update:
                    update_clicked = st.form_submit_button("🔄 Cập nhật", type="primary")
                with col_auto:
                    st.caption("💡 Tip: Nhấn Ctrl+Enter để cập nhật nhanh")
            
            if update_clicked and edited_content != st.session_state.xmindmark_content:
                with st.spinner("🔄 Đang cập nhật mindmap..."):
                    st.session_state.edit_history = st.session_state.edit_history[:st.session_state.history_index + 1]
                    st.session_state.edit_history.append(edited_content)
                    st.session_state.history_index += 1
                    if len(st.session_state.edit_history) > 50:
                        st.session_state.edit_history.pop(0)
                        st.session_state.history_index -= 1
                    st.session_state.xmindmark_content = edited_content
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    svg_content = agent.convert_xmindmark_to_svg_cli(edited_content, f"mindmap_manual_edit_{timestamp}")
                    st.session_state.mindmap_svg = svg_content
                st.success("✅ Đã cập nhật nội dung XMindMark và ảnh mindmap!")
                st.rerun()
            elif update_clicked and edited_content == st.session_state.xmindmark_content:
                st.info("ℹ️ Nội dung không thay đổi.")
            
            st.divider()
            st.markdown("### 🔄 Undo/Redo")
            col_undo, col_redo, col_original = st.columns(3)

            with col_undo:
                undo_disabled = st.session_state.history_index <= 0
                if st.button("⏪ Undo", disabled=undo_disabled, help="Hoàn tác thay đổi trước đó"):
                    if st.session_state.history_index > 0:
                        st.session_state.history_index -= 1
                        st.session_state.xmindmark_content = st.session_state.edit_history[st.session_state.history_index]
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        svg_content = agent.convert_xmindmark_to_svg_cli(st.session_state.xmindmark_content, f"mindmap_undo_{timestamp}")
                        st.session_state.mindmap_svg = svg_content
                        st.rerun()

            with col_redo:
                redo_disabled = st.session_state.history_index >= len(st.session_state.edit_history) - 1
                if st.button("⏩ Redo", disabled=redo_disabled, help="Làm lại thay đổi đã hoàn tác"):
                    if st.session_state.history_index < len(st.session_state.edit_history) - 1:
                        st.session_state.history_index += 1
                        st.session_state.xmindmark_content = st.session_state.edit_history[st.session_state.history_index]
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        svg_content = agent.convert_xmindmark_to_svg_cli(st.session_state.xmindmark_content, f"mindmap_redo_{timestamp}")
                        st.session_state.mindmap_svg = svg_content
                        st.rerun()

            with col_original:
                if st.button("📜 Xem Mindmap Gốc", help="Hiển thị mindmap ban đầu"):
                    if st.session_state.original_xmindmark:
                        st.session_state.xmindmark_content = st.session_state.original_xmindmark
                        st.session_state.edit_history.append(st.session_state.original_xmindmark)
                        st.session_state.history_index += 1
                        if len(st.session_state.edit_history) > 50:
                            st.session_state.edit_history.pop(0)
                            st.session_state.history_index -= 1
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        svg_content = agent.convert_xmindmark_to_svg_cli(st.session_state.original_xmindmark, f"mindmap_original_{timestamp}")
                        st.session_state.mindmap_svg = svg_content
                        st.rerun()
                    else:
                        st.warning("⚠️ Không có mindmap gốc nào được lưu.")

            st.divider()
            st.markdown("### ❓ Truy vấn Mindmap Gốc")
            query = st.text_input("Nhập câu hỏi về mindmap gốc:", placeholder="Ví dụ: Các nhánh chính của mindmap gốc là gì?")
            if query and st.session_state.original_xmindmark:
                with st.spinner("🤖 Đang xử lý câu hỏi..."):
                    prompt = f"""
                    Dựa trên nội dung XMindMark gốc sau, trả lời câu hỏi của người dùng.
                    Nội dung XMindMark:
                    {st.session_state.original_xmindmark}
                    Câu hỏi: {query}
                    HƯỚNG DẪN:
                    - Trả lời ngắn gọn, chính xác, tập trung vào câu hỏi
                    - Nếu cần, liệt kê các nhánh hoặc chi tiết liên quan
                    """
                    response = agent.llm_provider.call_llm(prompt, model)
                    st.write("**Trả lời:**")
                    st.write(response)
            elif query and not st.session_state.original_xmindmark:
                st.warning("⚠️ Không có mindmap gốc để truy vấn.")

        st.divider()
        st.subheader("💾 Tải xuống file")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"mindmap_{timestamp}"
        
        col_download1, col_download2, col_download3 = st.columns(3)
        
        with col_download1:
            st.download_button(
                label="📄 Tải .xmindmark",
                data=st.session_state.xmindmark_content,
                file_name=f"{base_filename}.xmindmark",
                mime="text/plain",
                help="Tải file XMindMark (định dạng text)"
            )
        
        with col_download2:
            if st.session_state.mindmap_svg:
                svg_bytes = agent.save_svg_file(st.session_state.mindmap_svg, base_filename)
                if svg_bytes:
                    st.download_button(
                        label="🖼️ Tải .svg",
                        data=svg_bytes,
                        file_name=f"{base_filename}.svg",
                        mime="image/svg+xml",
                        help="Tải ảnh mindmap định dạng SVG"
                    )
            else:
                st.button("🖼️ Tải .svg", disabled=True, help="Chưa có ảnh SVG")
        
        with col_download3:
            if agent.check_xmindmark_cli():
                if st.button("🧠 Tạo & Tải .xmind", help="Chuyển đổi sang XMind bằng CLI"):
                    with st.spinner("🔄 Đang chuyển đổi sang XMind bằng CLI..."):
                        xmind_content = agent.convert_xmindmark_to_xmind_cli(
                            st.session_state.xmindmark_content, 
                            base_filename
                        )
                        if xmind_content:
                            st.download_button(
                                label="💾 Tải file XMind",
                                data=xmind_content,
                                file_name=f"{base_filename}.xmind",
                                mime="application/vnd.xmind",
                                key=f"download_xmind_{timestamp}"
                            )
                            st.success("✅ File XMind đã được tạo thành công bằng CLI!")
                        else:
                            st.error("❌ Không thể tạo file XMind. Kiểm tra log phía trên.")
            else:
                st.button("🧠 Tạo & Tải .xmind", disabled=True, help="XMindMark CLI chưa được cài đặt")
        
        st.info("""
        📋 **Hướng dẫn sử dụng các file:**
        - **📄 .xmindmark**: File text có thể chỉnh sửa, import vào các tool khác
        - **🖼️ .svg**: Ảnh vector có thể xem trong browser, chèn vào document
        - **🧠 .xmind**: File gốc của XMind, được tạo bằng CLI chính thức
        
        **🤖 Tính năng chỉnh sửa bằng AI:**
        - Nhập yêu cầu chỉnh sửa bằng ngôn ngữ tự nhiên
        - AI sẽ hiểu context và thực hiện thay đổi phù hợp
        - Mindmap sẽ tự động cập nhật sau khi chỉnh sửa
        
        **⚠️ Lưu ý về XMindMark CLI:**
        - Cần cài đặt Node.js và chạy: `npm install -g xmindmark`
        - CLI tạo SVG và XMind chất lượng cao hơn
        - Nếu không có CLI, sẽ dùng phương thức dự phòng (Graphviz)
        """)