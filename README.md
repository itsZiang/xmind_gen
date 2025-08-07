# XMind Generator - Tạo Mind Map Tự Động

Ứng dụng AI tạo mind map tự động từ văn bản, tài liệu, giọng nói với khả năng tìm kiếm thông tin trực tuyến và chỉnh sửa thông minh.

## Tính năng chính

### Đa dạng nguồn đầu vào
- **Từ tài liệu**: PDF, DOCX, Markdown
- **Từ giọng nói**: Upload file audio hoặc thu âm trực tiếp
- **Tìm kiếm**: Tự động tìm kiếm thông tin từ internet
- **Cơ bản**: Tạo từ yêu cầu người dùng

### Xử lý thông minh
- **Streaming real-time**: Xem quá trình tạo mind map trực tiếp
- **Xử lý song song**: Chia nhỏ văn bản lớn để xử lý hiệu quả
- **Chỉnh sửa AI**: Tự động cập nhật và bổ sung thông tin
- **Tích hợp tìm kiếm**: Tavily Search API cho thông tin cập nhật

### Xuất đa định dạng
- **SVG**: Hình ảnh vector chất lượng cao
- **XMind**: File tương thích với ứng dụng XMind
- **Chỉnh sửa thủ công**: Editor tích hợp

## Kiến trúc hệ thống

```
├── api/                   # FastAPI REST API
│   └── router.py          # API endpoints
├── agent/                 # LangGraph workflow engine
│   ├── graph.py           # Workflow definitions
│   └── utils/
│       ├── nodes.py       # Processing nodes
│       ├── state.py       # State management
│       └── tools.py       # Utility functions
├── core/                  # Core services
│   ├── audio_processing.py # Whisper integration
│   ├── llm_handle.py      # LLM operations
│   ├── llm_provider.py    # LLM configurations
│   ├── prompt.py          # Prompt containing
│   ├── tavily_search.py   # Search integration
│   ├── text_processing.py # Document parsing
│   └── utils.py           # XMind/SVG conversion
├── ui.py                  # Streamlit interface
└── main.py                # FastAPI application
```

## Cài đặt

### Yêu cầu hệ thống
- Python 3.8+
- Node.js (cho xmindmark CLI)
- FFmpeg (cho xử lý audio)

### 1. Clone repository
```bash
git clone https://github.com/itsZiang/xmind_gen.git
cd xmind-gen
```

### 2. Cài đặt Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Cài đặt XMindMark CLI
```bash
npm install -g xmindmark
```

### 4. Cấu hình môi trường
Tạo file `.env`:
```env
# MISA LLM Configuration
API_KEY=your_misa_api_key
BASE_URL=your_misa_base_url

# Tavily Search API
TAVILY_API_KEY=your_tavily_api_key

# OpenAI (optional)
OPENAI_API_KEY=your_openai_api_key
```

### 5. Tạo thư mục cần thiết
```bash
mkdir -p static/output_svg static/output_xmind static/output_audio logs
```

## Chạy ứng dụng

### Khởi động API Server
```bash
bash run.sh (Ubuntu/MacOS)
run.bat (Windows) => Tự chuyển run.sh thành run.bat
```
API sẽ chạy tại: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### Khởi động Streamlit UI
```bash
streamlit run ui.py
```
Web interface: `http://localhost:8501`

## API Endpoints

### Audio Processing
```http
POST /api/generate-xmindmark-from-audio
Content-Type: multipart/form-data

- audio_file: File audio (WAV, MP3, M4A, OGG, FLAC, AAC)
- user_requirements: Yêu cầu tạo mind map
```

```http
POST /api/transcribe-audio
Content-Type: multipart/form-data

- audio_file: File audio cần chuyển đổi
```

### Document Processing
```http
POST /api/generate-xmindmark-from-docs
Content-Type: application/json

{
  "document_content": "Nội dung tài liệu",
  "user_requirements": "Yêu cầu tạo mind map",
  "stream": true
}
```

### General Generation
```http
POST /api/generate-xmindmark
Content-Type: application/json

{
  "user_requirements": "Yêu cầu tạo mind map",
  "enable_search": false,
  "stream": true
}
```

### Editing
```http
POST /api/edit-xmindmark
Content-Type: application/json

{
  "current_xmindmark": "Nội dung hiện tại",
  "edit_request": "Yêu cầu chỉnh sửa",
  "enable_search": false,
  "original_user_requirements": ""
}
```

### Export
```http
POST /api/to-svg
Content-Type: application/json

{
  "content": "XMindMark content"
}
```

```http
POST /api/to-xmind
Content-Type: application/json

{
  "content": "XMindMark content"
}
```

## XMindMark Format

XMindMark là định dạng văn bản đơn giản để tạo mind map:

```
Tiêu đề chính
- Nhánh chính 1
  - Nhánh phụ 1.1
    - Chi tiết 1.1.1
  - Nhánh phụ 1.2
- Nhánh chính 2
  - Nhánh phụ 2.1
```

**Quy tắc:**
- Dòng đầu: Tiêu đề gốc (không thụt lề)
- Level 1: `- Nội dung` 
- Level 2: `  - Nội dung` (2 spaces)
- Level 3: `    - Nội dung` (4 spaces)
- Mỗi node chỉ chứa từ khóa/cụm từ ngắn

## Workflow Engine (LangGraph)

### Luồng xử lý chính:
1. **Input Processing**: Xác định loại đầu vào (text/audio/document)
2. **Content Analysis**: Phân tích và quyết định có cần chia nhỏ không
3. **Parallel Processing**: Xử lý song song các chunk lớn
4. **Information Enhancement**: Tìm kiếm bổ sung (nếu enabled)
5. **Mind Map Generation**: Tạo XMindMark format
6. **Post-processing**: Tối ưu và format cuối cùng

### Decision Points:
```python
def route_from_start(state: DocumentState):
    if state.get("audio_file"):
        return "process_audio"
    else:
        return "check_split"

def route_after_split(state: DocumentState):
    if state["need_split"]:
        return "split_chunks"
    elif state.get("search_mode", False):
        return "generate_with_search"
    elif state.get("audio_processed", False):
        return "generate_from_audio"
    else:
        return "generate_direct"
```

## Audio Processing

### Supported Formats
- **WAV**: Chất lượng cao, không nén
- **MP3**: Phổ biến, nén có mất mát
- **M4A**: Apple format, chất lượng tốt
- **OGG**: Open source, chất lượng cao
- **FLAC**: Lossless compression
- **AAC**: Advanced Audio Codec

### Processing Pipeline
1. **Upload/Record**: Nhận file audio hoặc thu âm
2. **Validation**: Kiểm tra format và kích thước (max 25MB)
3. **Transcription**: Whisper model chuyển speech-to-text
4. **Translation**: Dịch sang tiếng Việt (nếu cần)
5. **Mind Map Generation**: Tạo XMindMark từ văn bản

### Whisper Integration
```python
model = whisper.load_model("tiny")

audio = whisper.load_audio(file_path)
result = model.transcribe(audio, task="translate")
```

## 🔍 Search Integration

### Tavily Search API
- **Real-time Information**: Tìm kiếm thông tin mới nhất
- **Content Filtering**: Lọc nội dung chất lượng cao
- **Deduplication**: Loại bỏ thông tin trùng lặp
- **Context Awareness**: Kết hợp với lịch sử hội thoại

### Search Flow
```python
def tavily_search(query: str) -> str:
    response = client.search(
        query=query,
        topic="general",
        max_results=5,
        include_raw_content="text"
    )
    return formatted_content
```

## Configuration

### LLM Providers
```python
# MISA LLM (Primary)
misa_llm = ChatOpenAI(
    model="misa-qwen3-235b",
    base_url=BASE_URL,
    api_key=API_KEY,
    max_tokens=8192,
    temperature=0.7
)

# OpenAI (Fallback)
llm = ChatOpenAI(model="gpt-4.1-mini")
```

### Processing Limits
- **Text splitting**: 100 characters threshold
- **Parallel processing**: Max 4 workers
- **Audio size**: 25MB limit
- **Search results**: Top 5 results
- **Token limits**: 8192 tokens per request

## Troubleshooting

### Common Issues

**1. Audio processing fails**
```bash
# Install FFmpeg
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

**2. XMindMark CLI not found**
```bash
# Reinstall xmindmark
npm uninstall -g xmindmark
npm install -g xmindmark
```

```
def generate_base_filename() -> str:
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    return timestamp

After that, using generate_base_filename() instead of "xmindmark" in subprocess.run
```

**3. SVG generation errors**
- Kiểm tra XMindMark format
- Verify xmindmark CLI installation
- Check file permissions

**4. API connection issues**
- Verify environment variables
- Check API key validity
- Confirm base URLs

### Logging
Logs được lưu tại: `logs/mindmap_YYYYMMDD.log`

```python
# Enable debug logging
logging.getLogger('agent.utils.nodes').setLevel(logging.DEBUG)
```

## Testing

### Manual Testing
1. **Basic Generation**: Tạo mind map từ text đơn giản
2. **Document Upload**: Test với PDF/DOCX files
3. **Audio Processing**: Upload file WAV ngắn
4. **Search Integration**: Test với yêu cầu cần thông tin mới
5. **Edit Functionality**: Chỉnh sửa mind map existing

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test basic generation
curl -X POST "http://localhost:8000/api/generate-xmindmark" \
  -H "Content-Type: application/json" \
  -d '{"user_requirements": "Tạo mind map về AI", "stream": false}'
```

## Performance Optimization

### Concurrency
- **Parallel chunk processing**: ThreadPoolExecutor với max 4 workers
- **Async streaming**: Real-time response processing
- **Model caching**: Whisper model singleton pattern

### Memory Management
- **Temporary files cleanup**: Auto-delete processed files
- **Streaming responses**: Reduce memory footprint
- **Content length limits**: Prevent OOM errors

### Caching Strategies
- **Model loading**: Load once, reuse multiple times
- **Search results**: Deduplicate similar queries
- **Generated content**: Store in session state

## Contributing

### Development Setup
1. Fork repository
2. Create feature branch
3. Install development dependencies
4. Run tests
5. Submit pull request

### Code Style
- **Python**: Follow PEP 8
- **FastAPI**: Use Pydantic models
- **Streamlit**: Component-based structure
- **Error Handling**: Comprehensive try-catch blocks

### Adding New Features
1. **New input source**: Add to `agent/utils/nodes.py`
2. **New LLM provider**: Extend `core/llm_provider.py`  
3. **New export format**: Add to `core/utils.py`
4. **New API endpoint**: Update `api/router.py`

## License

[Specify your license here]

## Support

- **Issues**: [GitHub Issues]
- **Documentation**: [Wiki/Docs link]
- **Email**: [Support email]

---

## 🔮 Roadmap

- [ ] **Multi-language support**: Hỗ trợ nhiều ngôn ngữ
- [ ] **Advanced templates**: Mind map templates có sẵn  
- [ ] **Collaboration**: Real-time collaborative editing
- [ ] **Mobile app**: React Native/Flutter app
- [ ] **Cloud storage**: Integration với Google Drive/OneDrive
- [ ] **Advanced analytics**: Mind map usage statistics