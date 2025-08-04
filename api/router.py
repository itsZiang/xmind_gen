from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from core.llm_handle import generate_xmindmark, edit_xmindmark_with_llm, generate_xmindmark_no_docs, generate_xmindmark_with_search
from core.utils import xmindmark_to_svg, xmindmark_to_xmind_file
from core.graph import generate_xmindmark_langgraph, generate_xmindmark_langgraph_stream
from pydantic import BaseModel

router = APIRouter()

class GenerateXMindMarkRequest(BaseModel):
    text: str
    user_requirements: str


class GenerateXMindMarkNoDocsRequest(BaseModel):
    user_requirements: str


class GenerateXMindMarkWithSearchRequest(BaseModel):
    user_requirements: str


class XMindMark(BaseModel):
    content: str
    
class EditXMindMarkRequest(BaseModel):
    current_xmindmark: str
    edit_request: str
    
    
@router.post("/edit-xmindmark", tags=["input"])
async def edit_xmindmark_api(request: EditXMindMarkRequest) -> StreamingResponse:
    response = edit_xmindmark_with_llm(request.current_xmindmark, request.edit_request)
    return StreamingResponse(response, media_type="text/event-stream")


@router.post("/generate-xmindmark", tags=["input"])
async def generate_xmindmark_api(request: GenerateXMindMarkRequest):
    xmindmark = generate_xmindmark(request.text, request.user_requirements)
    return {"xmindmark": xmindmark}


@router.post("/generate-xmindmark-langgraph", tags=["input"])
async def generate_xmindmark_langgraph_api(request: GenerateXMindMarkRequest):
    xmindmark = generate_xmindmark_langgraph(request.text, request.user_requirements)
    return {"xmindmark": xmindmark}


@router.post("/generate-xmindmark-langgraph-stream", tags=["input"])
async def generate_xmindmark_langgraph_stream_api(request: GenerateXMindMarkRequest):
    response = generate_xmindmark_langgraph_stream(request.text, request.user_requirements)
    return StreamingResponse(response, media_type="text/event-stream")


@router.post("/to-svg", tags=["output"])
async def to_svg_api(xmindmark: XMindMark):
    svg_url = xmindmark_to_svg(xmindmark.content)
    return {"svg_url": svg_url}


@router.post("/to-xmind", tags=["output"])
async def to_xmind_api(xmindmark: XMindMark):
    xmind_file = xmindmark_to_xmind_file(xmindmark.content)
    return {"xmind_file": xmind_file}


@router.post("/generate-xmindmark-no-docs", tags=["input"])
async def generate_xmindmark_no_docs_api(request: GenerateXMindMarkNoDocsRequest):
    response = generate_xmindmark_no_docs(request.user_requirements)
    return StreamingResponse(response, media_type="text/event-stream")


@router.post("/generate-xmindmark-with-search", tags=["input"])
async def generate_xmindmark_with_search_api(request: GenerateXMindMarkWithSearchRequest):
    response = generate_xmindmark_with_search(request.user_requirements)
    return StreamingResponse(response, media_type="text/event-stream")