from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from core.llm_handle import edit_xmindmark_with_llm, generate_xmindmark_no_docs_stream, generate_xmindmark_with_search_stream, edit_xmindmark_with_llm_search, generate_xmindmark_with_search, generate_xmindmark_no_docs
from core.utils import xmindmark_to_svg, xmindmark_to_xmind_file
from core.graph import generate_xmindmark_langgraph, generate_xmindmark_langgraph_stream
from core.text_processing import extract_text_from_file
from pydantic import BaseModel, Field
from typing import AsyncIterator
import json
from io import BytesIO

router = APIRouter()

# Response models for JSON streaming
class StreamChunk(BaseModel):
    delta: str = Field(..., description="Delta text content")
    done: bool = Field(False, description="Có phải chunk cuối cùng không")
    metadata: dict = Field(default_factory=dict, description="Metadata bổ sung")

class StreamingXMindMarkResponse(BaseModel):
    xmindmark: str = Field(..., description="Nội dung XMindMark hoàn chỉnh")


class GenerateXMindMarkFromDocsRequest(BaseModel):
    document_content: str = Field(..., description="Nội dung tài liệu cần phân tích để tạo mindmap")
    user_requirements: str = Field(..., description="Yêu cầu cụ thể của người dùng về mindmap")
    stream: bool = Field(True, description="Có sử dụng streaming response hay không")


class GenerateXMindMarkNoDocsRequest(BaseModel):
    user_requirements: str = Field(..., description="Yêu cầu của người dùng để tạo mindmap")
    enable_search: bool = Field(False, description="Có bật tính năng tìm kiếm thông tin bổ sung hay không")
    stream: bool = Field(True, description="Có sử dụng streaming response hay không")


class XMindMark(BaseModel):
    content: str = Field(..., description="Nội dung XMindMark")
    
class EditXMindMarkRequest(BaseModel):
    current_xmindmark: str = Field(..., description="Nội dung XMindMark hiện tại cần chỉnh sửa")
    edit_request: str = Field(..., description="Yêu cầu chỉnh sửa từ người dùng")
    enable_search: bool = Field(False, description="Có bật tính năng tìm kiếm khi chỉnh sửa hay không")
    original_user_requirements: str = Field("", description="Yêu cầu ban đầu của người dùng (cần thiết khi enable_search=True)")
    

# Utility functions for JSON streaming
async def convert_to_json_stream(generator) -> AsyncIterator[str]:
    """
    Convert generator thành JSON streaming format
    Hỗ trợ cả sync và async generators
    """
    chunk_index = 0
    
    try:
        # Try async iteration first
        async for chunk in generator:
            if chunk:  # Only yield non-empty chunks
                response = StreamChunk(
                    delta=chunk,
                    done=False,
                    metadata={"chunk_index": chunk_index}
                )
                yield json.dumps(response.model_dump(), ensure_ascii=False) + "\n"
                chunk_index += 1
    except TypeError:
        # Fall back to sync iteration
        for chunk in generator:
            if chunk:  # Only yield non-empty chunks
                response = StreamChunk(
                    delta=chunk,
                    done=False,
                    metadata={"chunk_index": chunk_index}
                )
                yield json.dumps(response.model_dump(), ensure_ascii=False) + "\n"
                chunk_index += 1
    
    # Final chunk to signal completion
    final_response = StreamChunk(
        delta="",
        done=True,
        metadata={
            "message": "Generation completed",
            "total_chunks": chunk_index
        }
    )
    yield json.dumps(final_response.model_dump(), ensure_ascii=False) + "\n"


 
def create_json_streaming_response(generator) -> StreamingResponse:
    """
    Tạo StreamingResponse cho JSON streaming
    """
    json_generator = convert_to_json_stream(generator)
    
    return StreamingResponse(
        json_generator,
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Content-Type-Options": "nosniff"
        }
    )
    
 
@router.post("/edit-xmindmark", tags=["edit xmindmark"])
async def edit_xmindmark_api(request: EditXMindMarkRequest) -> StreamingResponse:
    """
    Chỉnh sửa mindmap XMindMark hiện có
    
    **Mô tả:**
    API này cho phép chỉnh sửa một mindmap XMindMark đã tồn tại dựa trên yêu cầu của người dùng.
    
    **Tham số:**
    - `current_xmindmark`: Nội dung XMindMark hiện tại cần chỉnh sửa
    - `edit_request`: Yêu cầu chỉnh sửa cụ thể (thêm node, xóa node, thay đổi cấu trúc, v.v.)
    - `enable_search`: Bật/tắt tính năng tìm kiếm thông tin bổ sung khi chỉnh sửa
    - `original_user_requirements`: Yêu cầu ban đầu (bắt buộc khi enable_search=True)
    
    **Ví dụ sử dụng:**
    ```json
    {
        "current_xmindmark": "Node cha 1 - Node con 1.1 - Node con 1.2",
        "edit_request": "Thêm node mới về 'Machine Learning' vào node cha 1",
        "enable_search": false,
        "original_user_requirements": ""
    }
    ```
    
    **Response:**
    - Streaming JSON response với các chunk delta
    - Mỗi chunk chứa phần nội dung được tạo
    - Chunk cuối cùng có `done: true` để báo hiệu hoàn thành
    """
    if request.enable_search:
        if not request.original_user_requirements:
            raise ValueError("original_user_requirements is required when enable_search is True")
        response = edit_xmindmark_with_llm_search(
            user_requirements=request.original_user_requirements,
            edit_request=request.edit_request,
            current_xmindmark=request.current_xmindmark
        )
    else:
        response = edit_xmindmark_with_llm(request.current_xmindmark, request.edit_request)
    return create_json_streaming_response(response)


@router.post("/generate-xmindmark-from-docs", tags=["generate xmindmark"])
async def generate_xmindmark_langgraph_api(
    uploaded_file: UploadFile = File(..., description="Tệp tài liệu (PDF, DOCX, hoặc MD)"),
    user_requirements: str = Form(..., description="Yêu cầu cụ thể của người dùng về mindmap"),
    stream: bool = Form(..., description="Có sử dụng streaming response hay không")
):
    """
    Tạo mindmap XMindMark từ tài liệu sử dụng LangGraph
    """
    try:
        document_content = extract_text_from_file(uploaded_file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if stream:
        response_generator = generate_xmindmark_langgraph_stream(
            document_content,
            user_requirements
        )
        return create_json_streaming_response(response_generator)
    else:
        xmindmark = generate_xmindmark_langgraph(
            document_content,
            user_requirements
        )
        return StreamingXMindMarkResponse(xmindmark=xmindmark)


@router.post("/generate-xmindmark", tags=["generate xmindmark"])
async def generate_xmindmark_api(request: GenerateXMindMarkNoDocsRequest):
    """
    Tạo mindmap XMindMark từ yêu cầu người dùng (không cần tài liệu đầu vào)
    
    **Mô tả:**
    API này tạo mindmap XMindMark dựa trên yêu cầu của người dùng mà không cần tài liệu đầu vào.
    Có thể bật tính năng tìm kiếm để lấy thông tin bổ sung từ internet.
    
    **Tham số:**
    - `user_requirements`: Yêu cầu cụ thể về mindmap (chủ đề, cấu trúc, mức độ chi tiết)
    - `enable_search`: Bật/tắt tính năng tìm kiếm thông tin bổ sung từ internet
    - `stream`: Bật/tắt streaming response (mặc định: True)
    
    **Ví dụ sử dụng:**
    ```json
    {
        "user_requirements": "Giới thiệu về công ty MISA'",
        "enable_search": true,
        "stream": true
    }
    ```
    
    **Lưu ý:**
    - Khi `enable_search=true`: API sẽ tìm kiếm thông tin bổ sung để tạo mindmap chính xác hơn
    - Khi `enable_search=false`: API chỉ dựa vào kiến thức có sẵn để tạo mindmap
    
    **Response:**
    - Nếu `stream=true`: Streaming JSON response với các chunk delta
    - Nếu `stream=false`: JSON object với nội dung XMindMark hoàn chỉnh
    """
    if request.stream:
        # Get appropriate generator based on search option
        if request.enable_search:
            response_generator = generate_xmindmark_with_search_stream(request.user_requirements)
        else:
            response_generator = generate_xmindmark_no_docs_stream(request.user_requirements)
        
        return create_json_streaming_response(response_generator)
    else:
        # Non-streaming response
        if request.enable_search:
            xmindmark_content = generate_xmindmark_with_search(request.user_requirements)
        else:
            xmindmark_content = generate_xmindmark_no_docs(request.user_requirements)
        
        return StreamingXMindMarkResponse(xmindmark=xmindmark_content)


@router.post("/to-svg", tags=["save to svg/xmind"])
async def to_svg_bytes_api(xmindmark: XMindMark):
    """
    Chuyển đổi XMindMark thành file SVG
    
    **Mô tả:**
    API này chuyển đổi nội dung XMindMark thành file SVG để hiển thị mindmap dưới dạng hình ảnh.
    
    **Tham số:**
    - `content`: Nội dung XMindMark cần chuyển đổi
    
    **Ví dụ sử dụng:**
    ```json
    {
        "content": "xmindmark content"
    }
    ```
    
    **Response:**
    - File SVG dưới dạng binary data
    - Content-Type: image/svg+xml
    - Có thể hiển thị trực tiếp trong trình duyệt hoặc lưu thành file
    
    **Lưu ý:**
    - File SVG được tạo với kích thước tự động điều chỉnh theo nội dung
    - Có thể mở file SVG trong trình duyệt web hoặc các ứng dụng hỗ trợ SVG
    """
    svg_path = xmindmark_to_svg(xmindmark.content)
    with open(svg_path, 'rb') as f:
        svg_bytes = BytesIO(f.read())
    return StreamingResponse(
        svg_bytes,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f"inline; filename=result.svg"}
    )
    
    
@router.post("/to-xmind", tags=["save svg/xmind"])
async def to_xmind_bytes_api(xmindmark: XMindMark):
    """
    Chuyển đổi XMindMark thành file .xmind
    
    **Mô tả:**
    API này chuyển đổi nội dung XMindMark thành file .xmind để có thể mở trong ứng dụng XMind.
    
    **Tham số:**
    - `content`: Nội dung XMindMark cần chuyển đổi
    
    **Ví dụ sử dụng:**
    ```json
    {
        "content": "xmindmark content"
    }
    ```
    
    **Response:**
    - File .xmind dưới dạng binary data
    - Content-Type: application/octet-stream
    - File được tải xuống với tên "result.xmind"
    
    **Lưu ý:**
    - File .xmind có thể mở trong ứng dụng XMind Desktop hoặc XMind Online
    - Cấu trúc mindmap sẽ được bảo toàn trong file .xmind
    - Có thể chỉnh sửa file .xmind trong ứng dụng XMind sau khi tải xuống
    """
    xmind_file_path = xmindmark_to_xmind_file(xmindmark.content)
    if not xmind_file_path:
        raise HTTPException(status_code=500, detail="Không tạo được file .xmind")
    with open(xmind_file_path, 'rb') as f:
        xmind_bytes = BytesIO(f.read())
    
    return StreamingResponse(
        xmind_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=result.xmind"}
    )