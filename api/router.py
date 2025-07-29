from fastapi import APIRouter
from core.llm_handle import generate_xmindmark
from core.utils import xmindmark_to_svg, xmindmark_to_xmind_file
from pydantic import BaseModel

router = APIRouter()

class GenerateXMindMarkRequest(BaseModel):
    text: str
    user_requirements: str


class XMindMark(BaseModel):
    content: str


@router.post("/generate-xmindmark", tags=["input"])
async def generate_xmindmark_api(request: GenerateXMindMarkRequest):
    xmindmark = generate_xmindmark(request.text, request.user_requirements)
    return {"xmindmark": xmindmark}


@router.post("/to-svg", tags=["output"])
async def to_svg_api(xmindmark: XMindMark):
    svg_url = xmindmark_to_svg(xmindmark.content)
    return {"svg_url": svg_url}


@router.post("/to-xmind", tags=["output"])
async def to_xmind_api(xmindmark: XMindMark):
    xmind_file = xmindmark_to_xmind_file(xmindmark.content)
    return {"xmind_file": xmind_file}