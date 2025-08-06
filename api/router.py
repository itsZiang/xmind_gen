from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from core.llm_handle import edit_xmindmark_with_llm, generate_xmindmark_no_docs_stream, generate_xmindmark_with_search_stream, edit_xmindmark_with_llm_search, generate_xmindmark_with_search, generate_xmindmark_no_docs
from core.utils import xmindmark_to_svg, xmindmark_to_xmind_file
from core.graph import generate_xmindmark_langgraph, generate_xmindmark_langgraph_stream
from pydantic import BaseModel
from io import BytesIO
import os

router = APIRouter()

class GenerateXMindMarkFromDocsRequest(BaseModel):
    text: str
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
    
    
@router.post("/edit-xmindmark", tags=["input"])
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


@router.post("/generate-xmindmark-from-docs", tags=["input"])
async def generate_xmindmark_langgraph_api(request: GenerateXMindMarkFromDocsRequest):
    if request.stream:
        response = generate_xmindmark_langgraph_stream(request.text, request.user_requirements)
        return StreamingResponse(response, media_type="text/event-stream")
    else:
        xmindmark = generate_xmindmark_langgraph(request.text, request.user_requirements)
        return {"xmindmark": xmindmark}


@router.post("/generate-xmindmark", tags=["input"])
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


@router.post("/to-svg-bytes", tags=["output"])
async def to_svg_bytes_api(xmindmark: XMindMark):
    svg_path = xmindmark_to_svg(xmindmark.content)
    with open(svg_path, 'rb') as f:
        svg_bytes = BytesIO(f.read())
    return StreamingResponse(
        svg_bytes,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f"inline; filename=result.svg"}
    )
    
    
@router.post("/to-xmind-bytes", tags=["output"])
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