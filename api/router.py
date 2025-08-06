from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from core.llm_handle import generate_xmindmark_from_audio_stream, edit_xmindmark_with_llm, generate_xmindmark_no_docs_stream, generate_xmindmark_with_search_stream, edit_xmindmark_with_llm_search, generate_xmindmark_with_search, generate_xmindmark_no_docs
from core.utils import xmindmark_to_svg, xmindmark_to_xmind_file
from core.graph import generate_xmindmark_langgraph, generate_xmindmark_langgraph_stream
from core.audio_processing import process_uploaded_audio, validate_audio_file
from pydantic import BaseModel
from io import BytesIO
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class GenerateXMindMarkFromDocsRequest(BaseModel):
    document_content: str
    user_requirements: str
    stream: bool = True


class GenerateXMindMarkNoDocsRequest(BaseModel):
    user_requirements: str
    enable_search: bool = False
    stream: bool = True


class XMindMark(BaseModel):
    content: str
    
class EditXMindMarkRequest(BaseModel):
    current_xmindmark: str
    edit_request: str
    enable_search: bool = False
    original_user_requirements: str
    
class GenerateFromAudioRequest(BaseModel):
    user_requirements: str

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
        
        return StreamingResponse(generate_response(), media_type="text/event-stream")
        
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
    return StreamingResponse(response, media_type="text/event-stream")


@router.post("/generate-xmindmark-from-docs", tags=["generate xmindmark"])
async def generate_xmindmark_langgraph_api(request: GenerateXMindMarkFromDocsRequest):
    if request.stream:
        response = generate_xmindmark_langgraph_stream(request.document_content, request.user_requirements)
        return StreamingResponse(response, media_type="text/event-stream")
    else:
        xmindmark = generate_xmindmark_langgraph(request.document_content, request.user_requirements)
        return {"xmindmark": xmindmark}


@router.post("/generate-xmindmark", tags=["generate xmindmark"])
async def generate_xmindmark_api(request: GenerateXMindMarkNoDocsRequest):
    if request.enable_search:
        response = generate_xmindmark_with_search_stream(request.user_requirements)
    else:
        response = generate_xmindmark_no_docs_stream(request.user_requirements)
    
    if request.stream:
        return StreamingResponse(response, media_type="text/event-stream")
    else:
        if request.enable_search:
            response = generate_xmindmark_with_search(request.user_requirements)
        else:
            response = generate_xmindmark_no_docs(request.user_requirements)
        return {"xmindmark": response}


# @router.post("/to-svg", tags=["output"])
# async def to_svg_api(xmindmark: XMindMark):
#     svg_url = xmindmark_to_svg(xmindmark.content)
#     return {"svg_url": svg_url}


# @router.post("/to-xmind", tags=["output"])
# async def to_xmind_api(xmindmark: XMindMark):
#     xmind_file = xmindmark_to_xmind_file(xmindmark.content)
#     return {"xmind_file": xmind_file}


@router.post("/to-svg", tags=["save xmindmark"])
async def to_svg_bytes_api(xmindmark: XMindMark):
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