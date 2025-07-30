import streamlit as st
import PyPDF2
import json
import uuid
import re
import os
import base64
import subprocess
import tempfile
from datetime import datetime
from docx import Document
from openai import OpenAI
import g4f
from graphviz import Digraph

# Cài đặt trang
st.set_page_config(
    page_title="Agent AI - Bản Đồ Tư Duy XMindMark",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

class LLMProvider:
    """Lớp quản lý LLM"""
    def __init__(self):
        self.client = None
        self.provider = None

    def initialize_client(self, provider: str, api_key: str = None):
        """Khởi tạo client cho provider được chọn"""
        self.provider = provider
        try:
            if provider == "openai":
                if not api_key:
                    raise ValueError("API Key is required for OpenAI")
                self.client = OpenAI(
                    base_url="https://test-aiservice.misa.com.vn/llm-router/v1",
                    api_key=api_key,
                    default_headers={"App-Code": "fresher"}
                )
            elif provider == "g4f":
                self.client = g4f
        except Exception as e:
            st.error(f"Lỗi khởi tạo {provider}: {str(e)}")

    def get_available_models(self) -> list:
        """Lấy danh sách model có sẵn cho provider"""
        if self.provider == "openai":
            return ["gpt-4.1", "gpt-4.1-mini", "misa-qwen3-30b", "misa-qwen3-235b", "misa-internvl3-38b", "omni-moderation-latest"]
        elif self.provider == "g4f":
            try:
                return [model.replace('_', '-') for model in dir(g4f.models) if not model.startswith('_')]
            except Exception as e:
                st.error(f"Lỗi khi lấy danh sách model g4f: {str(e)}")
                return ["gpt-3.5-turbo", "gpt-4"]
        return []

    def call_llm(self, prompt: str, model: str = "gpt-4.1-mini") -> str:
        """Gọi LLM"""
        if not self.client:
            return "Client LLM chưa được khởi tạo."
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=15000,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            elif self.provider == "g4f":
                response = self.client.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=15000,
                    temperature=0.3
                )
                if isinstance(response, str):
                    return response.strip()
                elif hasattr(response, 'choices') and response.choices:
                    return response.choices[0].message.content.strip()
                else:
                    st.error(f"Phản hồi g4f không đúng định dạng: {response}")
                    return f"Lỗi: Phản hồi g4f không có thuộc tính 'choices' hoặc không phải chuỗi."
        except Exception as e:
            return f"Lỗi {self.provider}: {str(e)}"

class MindMapAgent:
    def __init__(self):
        self.llm_provider = LLMProvider()
        self.initialize_session_state()

    def initialize_session_state(self):
        """Khởi tạo session state"""
        if 'extracted_text' not in st.session_state:
            st.session_state.extracted_text = ""
        if 'xmindmark_content' not in st.session_state:
            st.session_state.xmindmark_content = ""
        if 'original_xmindmark' not in st.session_state:
            st.session_state.original_xmindmark = ""  # Store original mindmap
        if 'edit_history' not in st.session_state:
            st.session_state.edit_history = []  # List to store edit history
        if 'history_index' not in st.session_state:
            st.session_state.history_index = -1  # Current position in history
        if 'user_requirements' not in st.session_state:
            st.session_state.user_requirements = ""
        if 'llm_raw_response' not in st.session_state:
            st.session_state.llm_raw_response = ""
        if 'mindmap_svg' not in st.session_state:
            st.session_state.mindmap_svg = None
        if 'selected_provider' not in st.session_state:
            st.session_state.selected_provider = "openai"

    def extract_text_from_file(self, uploaded_file) -> str:
        """Trích xuất văn bản từ file PDF, DOCX, hoặc MD"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'pdf':
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                return text.strip()
            
            elif file_extension == 'docx':
                doc = Document(uploaded_file)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text.strip()
            
            elif file_extension == 'md':
                text = uploaded_file.read().decode('utf-8')
                return text.strip()
            
            else:
                st.error(f"Định dạng file '{file_extension}' không được hỗ trợ.")
                return ""
                
        except Exception as e:
            st.error(f"Lỗi khi đọc file: {str(e)}")
            return ""

    def create_structured_prompt(self, text: str, user_requirements: str) -> str:
        """Tạo prompt yêu cầu LLM trả về JSON hợp lệ"""
        prompt = f"""
        Hãy phân tích văn bản sau và tạo một bản đồ tư duy theo yêu cầu của người dùng.
        YÊU CẦU CỦA NGƯỜI DÙNG: {user_requirements}
        VĂN BẢN CẦN PHÂN TÍCH:
        {text}
        HƯỚNG DẪN:
        - Tự quyết định số lượng nhánh chính, nhánh phụ và tầng dựa trên nội dung và yêu cầu.
        - Mỗi nút (node) trong bản đổ tư duy CHỈ BAO GỒM từ khóa hoặc cụm từ ngắn (keywords/phrases), KHÔNG PHẢI CÂU HOÀN CHỈNH.
        - Trả về CHỈ JSON hợp lệ, không bao gồm bất kỳ văn bản giải thích, ký tự ngoài JSON, hoặc định dạng khác.
        - Đảm bảo cú pháp JSON đúng: sử dụng dấu nháy kép ("), kiểm tra dấu phẩy (,), và đóng tất cả dấu ngoặc.
        - Cấu trúc JSON phải theo định dạng sau:
        {{
          "title": "Tiêu đề chung cho bản đổ tư duy (dưới 10 từ)",
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

    def create_edit_prompt(self, current_xmindmark: str, edit_request: str) -> str:
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

    def clean_json_string(self, json_str: str) -> str:
        """Cải thiện JSON string để xử lý các lỗi cú pháp"""
        try:
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start != -1 and end > start:
                json_str = json_str[start:end]
            else:
                json_str = json_str.strip()
        except:
            pass
        
        json_str = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_str)
        json_str = json_str.replace("'", '"')
        json_str = re.sub(r'\}\s*\{', '},{', json_str)
        json_str = re.sub(r'\]\s*\{', '],{', json_str)
        json_str = re.sub(r'\}\s*\]', '}]', json_str)
        json_str = re.sub(r',\s*\]', ']', json_str)
        json_str = re.sub(r',\s*\}', '}', json_str)
        json_str = re.sub(r'(\}\s*,\s*\{[^}]*?)(?=\s*\{)', r'\1,', json_str)
        
        return json_str

    def convert_xmindmark_to_svg_cli(self, xmindmark_content: str, base_filename: str) -> str:
        """Chuyển đổi XMindMark thành SVG sử dụng CLI tool"""
        try:
            if not self.check_xmindmark_cli():
                st.error("❌ XMindMark CLI chưa được cài đặt. Không thể tạo SVG.")
                return self.fallback_svg_creation(xmindmark_content)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                xmindmark_dir = os.path.join(temp_dir, 'xmindmark')
                output_dir = os.path.join(temp_dir, 'output')
                os.makedirs(xmindmark_dir, exist_ok=True)
                os.makedirs(output_dir, exist_ok=True)
                
                xmindmark_file = os.path.join(xmindmark_dir, f"{base_filename}.xmindmark")
                with open(xmindmark_file, 'w', encoding='utf-8') as f:
                    f.write(xmindmark_content)
                
                try:
                    result = subprocess.run(
                        ['xmindmark', '--format', 'svg', xmindmark_file], 
                        cwd=output_dir,
                        capture_output=True, 
                        text=True, 
                        timeout=30
                    )
                    
                    if result.returncode != 0:
                        st.warning(f"⚠️ Cảnh báo từ xmindmark CLI:\n{result.stderr}")
                        st.info("🔄 Đang chuyển sang phương thức tạo SVG dự phòng...")
                        return self.fallback_svg_creation(xmindmark_content)
                    
                    svg_file = os.path.join(output_dir, f"{base_filename}.svg")
                    if not os.path.exists(svg_file):
                        svg_files = [f for f in os.listdir(output_dir) if f.endswith('.svg')]
                        if svg_files:
                            svg_file = os.path.join(output_dir, svg_files[0])
                        else:
                            st.warning("⚠️ Không tìm thấy file SVG từ CLI, sử dụng phương thức dự phòng")
                            return self.fallback_svg_creation(xmindmark_content)
                    
                    with open(svg_file, 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                        
                    with st.expander("🔍 Thông tin SVG từ CLI"):
                        st.success("✅ SVG được tạo bằng XMindMark CLI")
                        st.text(f"File SVG: {os.path.basename(svg_file)}")
                        st.text(f"Kích thước: {len(svg_content):,} ký tự")
                        if result.stdout:
                            st.text(f"Output: {result.stdout}")
                    
                    return svg_content
                        
                except subprocess.TimeoutExpired:
                    st.error("❌ Timeout khi tạo SVG bằng CLI (>30s)")
                    return self.fallback_svg_creation(xmindmark_content)
                except Exception as e:
                    st.warning(f"⚠️ Lỗi khi chạy CLI: {str(e)}")
                    return self.fallback_svg_creation(xmindmark_content)
                    
        except Exception as e:
            st.error(f"❌ Lỗi khi chuyển đổi SVG: {str(e)}")
            return self.fallback_svg_creation(xmindmark_content)

    def fallback_svg_creation(self, xmindmark_content: str) -> str:
        """Tạo SVG dự phòng bằng graphviz khi CLI thất bại"""
        try:
            dot = Digraph(format='svg')
            dot.attr(rankdir='LR')
            dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue', 
                    fontname='Arial', fontsize='10')
            dot.attr('edge', color='blue', fontname='Arial', fontsize='8')

            lines = xmindmark_content.strip().split('\n')
            if not lines:
                return self.create_empty_svg()
            
            root_label = lines[0].strip()
            if not root_label:
                return self.create_empty_svg()
            
            dot.node('root', root_label, fillcolor='lightcoral', fontsize='12')

            parent_stack = [('root', 0)]  # (node_id, level)
            node_counter = 0

            for line_idx, line in enumerate(lines[1:], 1):
                stripped_line = line.rstrip()
                
                if not stripped_line or not stripped_line.strip():
                    continue
                
                leading_spaces = len(line) - len(line.lstrip())
                tab_count = line.count('\t', 0, leading_spaces)
                space_groups = (leading_spaces - tab_count) // 2  
                current_level = tab_count + space_groups
                
                label = re.sub(r'^[\t\s]*-\s*', '', stripped_line).strip()
                if not label:
                    continue
                
                node_counter += 1
                node_id = f"node_{node_counter}"
                
                while len(parent_stack) > 1 and parent_stack[-1][1] >= current_level:
                    parent_stack.pop()
                
                parent_id = parent_stack[-1][0]
                
                colors = ['lightblue', 'lightgreen', 'lightyellow', 'lightpink', 'lightgray']
                node_color = colors[min(current_level, len(colors)-1)]
                
                dot.node(node_id, label, fillcolor=node_color)
                dot.edge(parent_id, node_id)
                
                parent_stack.append((node_id, current_level))

            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            file_name = os.path.join(output_dir, f"mindmap_fallback_{uuid.uuid4()}")
            dot.render(filename=file_name, format='svg', cleanup=False)
            
            svg_file = f"{file_name}.svg"
            with open(svg_file, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            os.remove(svg_file)
            
            with st.expander("🔍 Thông tin SVG dự phòng"):
                st.info("ℹ️ SVG được tạo bằng Graphviz (dự phòng)")
                st.text(f"Tổng số nodes: {node_counter + 1}")
                
            return svg_content
                
        except Exception as e:
            st.error(f"❌ Lỗi khi tạo SVG dự phòng: {str(e)}")
            return self.create_empty_svg()

    def create_empty_svg(self) -> str:
        """Tạo SVG trống khi tất cả phương thức thất bại"""
        return '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">
            <rect width="400" height="200" fill="#f0f0f0" stroke="#ccc"/>
            <text x="200" y="100" text-anchor="middle" font-family="Arial" font-size="16" fill="#666">
                Không thể tạo mindmap SVG
            </text>
        </svg>'''

    def export_to_xmindmark(self, mindmap_data: dict) -> str:
        """Chuyển đổi JSON thành định dạng XMindMark chính xác"""
        title = mindmap_data.get('title', 'Bản đồ tư duy')
        nodes = mindmap_data.get('nodes', [])
        
        output = f"{title}\n"
        
        def build_xmindmark(nodes, parent_id=None, level=0):
            result = ""
            child_nodes = [node for node in nodes if node.get('parent_id') == parent_id]
            for node in child_nodes:
                indent = "\t" * (level - 1) if level > 0 else ""
                result += f"{indent}- {node['label']}\n"
                result += build_xmindmark(nodes, node['id'], level + 1)
            return result
        
        root_node = next((node for node in nodes if node.get('level') == 0), None)
        if root_node:
            output += build_xmindmark(nodes, root_node['id'], 1)
        return output

    def process_text_with_llm(self, text: str, user_requirements: str, provider: str, api_key: str, model: str) -> str:
        """Xử lý văn bản bằng LLM và trả về nội dung XMindMark"""
        self.llm_provider.initialize_client(provider, api_key)
        prompt = self.create_structured_prompt(text, user_requirements)
        try:
            result = self.llm_provider.call_llm(prompt, model)
            st.session_state.llm_raw_response = result
            
            json_str = self.clean_json_string(result)
            
            try:
                mindmap_data = json.loads(json_str)
            except json.JSONDecodeError as je:
                st.error(f"Lỗi phân tích JSON từ LLM: {str(je)}")
                st.text_area("Phản hồi thô từ LLM:", value=result, height=200, disabled=True)
                error_pos = je.pos
                snippet_start = max(0, error_pos - 50)
                snippet_end = min(len(result), error_pos + 50)
                st.text_area("Đoạn văn bản gần vị trí lỗi:", value=result[snippet_start:snippet_end], height=100, disabled=True)
                return self.fallback_xmindmark(text, user_requirements)
            
            xmindmark_content = self.export_to_xmindmark(mindmap_data)
            # Save original mindmap and initialize edit history
            st.session_state.original_xmindmark = xmindmark_content
            st.session_state.edit_history = [xmindmark_content]
            st.session_state.history_index = 0
            # Update SVG
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            svg_content = self.convert_xmindmark_to_svg_cli(xmindmark_content, f"mindmap_{timestamp}")
            st.session_state.mindmap_svg = svg_content
            return xmindmark_content
        except Exception as e:
            st.error(f"Lỗi khi gọi LLM: {str(e)}")
            st.text_area("Phản hồi thô từ LLM:", value=st.session_state.llm_raw_response, height=200, disabled=True)
            return self.fallback_xmindmark(text, user_requirements)

    def edit_xmindmark_with_llm(self, current_content: str, edit_request: str, provider: str, api_key: str, model: str) -> str:
        """Chỉnh sửa XMindMark bằng LLM"""
        if not self.llm_provider.client:
            self.llm_provider.initialize_client(provider, api_key)
        
        prompt = self.create_edit_prompt(current_content, edit_request)
        try:
            result = self.llm_provider.call_llm(prompt, model)
            cleaned_result = result.strip()
            if cleaned_result.startswith('```'):
                lines = cleaned_result.split('\n')
                cleaned_result = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned_result
            
            # Update edit history
            if cleaned_result != current_content:
                st.session_state.edit_history = st.session_state.edit_history[:st.session_state.history_index + 1]
                st.session_state.edit_history.append(cleaned_result)
                st.session_state.history_index += 1
                if len(st.session_state.edit_history) > 50:
                    st.session_state.edit_history.pop(0)
                    st.session_state.history_index -= 1
            
            return cleaned_result
        except Exception as e:
            st.error(f"Lỗi khi chỉnh sửa bằng LLM: {str(e)}")
            return current_content

    def fallback_xmindmark(self, text: str, user_requirements: str) -> str:
        """Tạo XMindMark dự phòng khi LLM thất bại"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10][:2]
        main_ideas = []
        for i, sentence in enumerate(sentences, 1):
            main_idea = sentence[:50] + "..." if len(sentence) > 50 else sentence
            main_ideas.append(f"- Ý chính {i}\n\t- {main_idea}")
        if not main_ideas:
            main_ideas.append("- Ý chính 1\n\t- ...")
        return f"Bản đồ tư duy\n{''.join(main_ideas)}"

    def check_xmindmark_cli(self) -> bool:
        """Kiểm tra xem xmindmark CLI có được cài đặt không"""
        try:
            result = subprocess.run(['xmindmark', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def convert_xmindmark_to_xmind_cli(self, xmindmark_content: str, base_filename: str) -> bytes:
        """Chuyển đổi XMindMark thành XMind sử dụng CLI tool"""
        try:
            if not self.check_xmindmark_cli():
                st.error("❌ XMindMark CLI chưa được cài đặt. Vui lòng cài đặt bằng lệnh: npm install -g xmindmark")
                st.info("📋 Hướng dẫn cài đặt XMindMark CLI:\n1. Cài đặt Node.js\n2. Chạy: npm install -g xmindmark")
                return None
            
            with tempfile.TemporaryDirectory() as temp_dir:
                xmindmark_dir = os.path.join(temp_dir, 'xmindmark')
                output_dir = os.path.join(temp_dir, 'output')
                os.makedirs(xmindmark_dir, exist_ok=True)
                os.makedirs(output_dir, exist_ok=True)
                
                xmindmark_file = os.path.join(xmindmark_dir, f"{base_filename}.xmindmark")
                with open(xmindmark_file, 'w', encoding='utf-8') as f:
                    f.write(xmindmark_content)
                
                try:
                    result = subprocess.run(
                        ['xmindmark', xmindmark_file], 
                        cwd=output_dir,
                        capture_output=True, 
                        text=True, 
                        timeout=30
                    )
                    
                    if result.returncode != 0:
                        st.error(f"❌ Lỗi khi chạy xmindmark CLI:\n{result.stderr}")
                        return None
                    
                    xmind_file = os.path.join(output_dir, f"{base_filename}.xmind")
                    if not os.path.exists(xmind_file):
                        xmind_files = [f for f in os.listdir(output_dir) if f.endswith('.xmind')]
                        if xmind_files:
                            xmind_file = os.path.join(output_dir, xmind_files[0])
                        else:
                            st.error("❌ Không tìm thấy file XMind được tạo")
                            return None
                    
                    with open(xmind_file, 'rb') as f:
                        return f.read()
                        
                except subprocess.TimeoutExpired:
                    st.error("❌ Timeout khi chạy xmindmark CLI (>30s)")
                    return None
                except Exception as e:
                    st.error(f"❌ Lỗi khi chạy xmindmark CLI: {str(e)}")
                    return None
                    
        except Exception as e:
            st.error(f"❌ Lỗi khi chuyển đổi file: {str(e)}")
            return None

    def save_svg_file(self, svg_content: str, filename: str) -> bytes:
        """Lưu nội dung SVG thành file bytes"""
        try:
            return svg_content.encode('utf-8')
        except Exception as e:
            st.error(f"Lỗi khi tạo file SVG: {str(e)}")
            return None

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

if __name__ == "__main__":
    main()