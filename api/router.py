from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from core.llm_handle import generate_xmindmark_from_audio_stream, edit_xmindmark_with_llm, generate_xmindmark_no_docs_stream, generate_xmindmark_with_search_stream, edit_xmindmark_with_llm_search, generate_xmindmark_with_search, generate_xmindmark_no_docs
from core.utils import xmindmark_to_svg, xmindmark_to_xmind_file
from core.graph import generate_xmindmark_langgraph, generate_xmindmark_langgraph_stream
from core.audio_processing import process_uploaded_audio, validate_audio_file
from pydantic import BaseModel, Field
from typing import AsyncIterator
import json
from io import BytesIO
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

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
    
class GenerateFromAudioRequest(BaseModel):
    user_requirements: str

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

@router.post("/generate-xmindmark-from-audio", tags=["input"])
async def generate_xmindmark_from_audio_api(
    audio_file: UploadFile = File(...),
    user_requirements: str = Form(...)  
):
    try:
        logger.info(f"Received audio file: {audio_file.filename}, size: {audio_file.size}")
        
        if not user_requirements or not user_requirements.strip():
            raise HTTPException(
                status_code=400,
                detail="User requirements are required and cannot be empty"
            )
        

        if not audio_file or not audio_file.filename:
            raise HTTPException(
                status_code=400,
                detail="Audio file is required"
            )
            
        if not validate_audio_file(audio_file):
            raise HTTPException(
                status_code=400,
                detail="Invalid audio file. Supported formats: wav, mp3, m4a, ogg, flac, aac. Max size: 25MB"
            )
        
        await audio_file.seek(0)
        
        logger.info("Starting audio transcription and translation")
        try:
            vietnamese_text = process_uploaded_audio(audio_file)
        except Exception as audio_error:
            logger.error(f"Audio processing failed: {str(audio_error)}")
            raise HTTPException(
                status_code=400,
                detail=f"Audio processing failed: {str(audio_error)}"
            )
        
        if not vietnamese_text or not vietnamese_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from audio file or transcription is empty"
            )
        
        logger.info(f"Audio processing completed. Transcribed text length: {len(vietnamese_text)}")
        
        def generate_response():
            try:
                for chunk in generate_xmindmark_from_audio_stream(vietnamese_text, user_requirements):
                    if chunk: 
                        yield chunk
            except Exception as e:
                logger.error(f"Error in streaming generation: {str(e)}")
                yield f"Error: {str(e)}"
        
        return create_json_streaming_response(generate_response())        
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in audio processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/transcribe-audio", tags=["input"])
async def transcribe_audio_api(audio_file: UploadFile = File(...)):
    try:
        logger.info(f"Received audio file for transcription: {audio_file.filename}")
        
        if not audio_file or not audio_file.filename:
            raise HTTPException(
                status_code=400,
                detail="Audio file is required"
            )
            
        if not validate_audio_file(audio_file):
            raise HTTPException(
                status_code=400,
                detail="Invalid audio file. Supported formats: wav, mp3, m4a, ogg, flac, aac. Max size: 25MB"
            )
        
        await audio_file.seek(0)
        
        try:
            transcribed_text = process_uploaded_audio(audio_file)
        except Exception as audio_error:
            logger.error(f"Audio transcription failed: {str(audio_error)}")
            raise HTTPException(
                status_code=400,
                detail=f"Audio transcription failed: {str(audio_error)}"
            )
        
        if not transcribed_text or not transcribed_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from audio file or transcription is empty"
            )
        
        logger.info(f"Transcription completed. Text length: {len(transcribed_text)}")
        
        return {
            "transcribed_text": transcribed_text,
            "length": len(transcribed_text),
            "filename": audio_file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in audio transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 
    
 
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
async def generate_xmindmark_langgraph_api(request: GenerateXMindMarkFromDocsRequest):
    """
    Tạo mindmap XMindMark từ tài liệu sử dụng LangGraph
    
    **Mô tả:**
    API này phân tích nội dung tài liệu và tạo mindmap XMindMark dựa trên yêu cầu của người dùng.
    Sử dụng LangGraph để xử lý phức tạp và tạo ra mindmap có cấu trúc tốt.
    
    **Tham số:**
    - `document_content`: Nội dung tài liệu cần phân tích (văn bản, bài viết, tài liệu kỹ thuật, v.v.)
    - `user_requirements`: Yêu cầu cụ thể về mindmap (chủ đề chính, cấu trúc, mức độ chi tiết)
    - `stream`: Bật/tắt streaming response (mặc định: True)
    
    **Ví dụ sử dụng:**
    ```json
    {
        "document_content": "Machine Learning là một nhánh của AI...",
        "user_requirements": "Tạo mindmap về Machine Learning với các khái niệm cơ bản",
        "stream": true
    }
    ```
    
    **Response:**
    - Nếu `stream=true`: Streaming JSON response
    - Nếu `stream=false`: JSON object với nội dung XMindMark hoàn chỉnh
    """
    if request.stream:
        response_generator = generate_xmindmark_langgraph_stream(
            request.document_content, 
            request.user_requirements
        )
        return create_json_streaming_response(response_generator)
    else:
        xmindmark = generate_xmindmark_langgraph(
            request.document_content, 
            request.user_requirements
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


@router.post("/to-svg", tags=["save xmindmark"])
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
    
    
@router.post("/to-xmind", tags=["save xmindmark"])
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