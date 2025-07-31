# from fastapi import APIRouter
# from core.llm_handle import generate_xmindmark, edit_xmindmark_with_llm
# from core.utils import xmindmark_to_svg, xmindmark_to_xmind_file
# from pydantic import BaseModel

# router = APIRouter()

# class GenerateXMindMarkRequest(BaseModel):
#     text: str
#     user_requirements: str


# class XMindMark(BaseModel):
#     content: str

# class EditXMindMarkRequest(BaseModel):
#     current_xmindmark: str
#     edit_request: str


# @router.post("/generate-xmindmark", tags=["input"])
# async def generate_xmindmark_api(request: GenerateXMindMarkRequest):
#     xmindmark = generate_xmindmark(request.text, request.user_requirements)
#     return {"xmindmark": xmindmark}

# @router.post("/edit-xmindmark", tags=["input"])
# async def edit_xmindmark_api(request: EditXMindMarkRequest):
#     edited_xmindmark = edit_xmindmark_with_llm(request.current_xmindmark, request.edit_request)
#     return {"edited_xmindmark": edited_xmindmark}


# @router.post("/to-svg", tags=["output"])
# async def to_svg_api(xmindmark: XMindMark):
#     svg_url = xmindmark_to_svg(xmindmark.content)
#     return {"svg_url": svg_url}


# @router.post("/to-xmind", tags=["output"])
# async def to_xmind_api(xmindmark: XMindMark):
#     xmind_file = xmindmark_to_xmind_file(xmindmark.content)
#     return {"xmind_file": xmind_file}









from fastapi import APIRouter, HTTPException
from core.llm_handle import (
    generate_xmindmark_with_workflow, 
    edit_xmindmark_with_workflow,
    # Keep legacy functions
    generate_xmindmark, 
    edit_xmindmark_with_llm
)
from core.utils import xmindmark_to_svg, xmindmark_to_xmind_file
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class GenerateXMindMarkRequest(BaseModel):
    text: str
    user_requirements: str

class XMindMark(BaseModel):
    content: str

class EditXMindMarkRequest(BaseModel):
    current_xmindmark: str
    edit_request: str

class WorkflowResponse(BaseModel):
    success: bool
    xmindmark: Optional[str] = None
    edited_xmindmark: Optional[str] = None
    svg_url: Optional[str] = None
    xmind_file_url: Optional[str] = None
    errors: List[str] = []
    status: str

# New workflow endpoints
@router.post("/generate-xmindmark-workflow", tags=["workflow"], response_model=WorkflowResponse)
async def generate_xmindmark_workflow_api(request: GenerateXMindMarkRequest):
    """Tạo XMindMark sử dụng LangGraph workflow với validation và error handling"""
    try:
        result = generate_xmindmark_with_workflow(request.text, request.user_requirements)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail={
                "message": "Workflow failed",
                "errors": result["errors"],
                "status": result["status"]
            })
        
        return WorkflowResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution error: {str(e)}")

@router.post("/edit-xmindmark-workflow", tags=["workflow"], response_model=WorkflowResponse)
async def edit_xmindmark_workflow_api(request: EditXMindMarkRequest):
    """Chỉnh sửa XMindMark sử dụng LangGraph workflow"""
    try:
        result = edit_xmindmark_with_workflow(request.current_xmindmark, request.edit_request)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail={
                "message": "Edit workflow failed", 
                "errors": result["errors"],
                "status": result["status"]
            })
        
        return WorkflowResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Edit workflow execution error: {str(e)}")

# Keep original endpoints for backward compatibility
@router.post("/generate-xmindmark", tags=["input"])
async def generate_xmindmark_api(request: GenerateXMindMarkRequest):
    """Legacy endpoint"""
    xmindmark = generate_xmindmark(request.text, request.user_requirements)
    return {"xmindmark": xmindmark}

@router.post("/edit-xmindmark", tags=["input"])
async def edit_xmindmark_api(request: EditXMindMarkRequest):
    """Legacy endpoint"""
    edited_xmindmark = edit_xmindmark_with_llm(request.current_xmindmark, request.edit_request)
    return {"edited_xmindmark": edited_xmindmark}

@router.post("/to-svg", tags=["output"])
async def to_svg_api(xmindmark: XMindMark):
    svg_url = xmindmark_to_svg(xmindmark.content)
    return {"svg_url": svg_url}

@router.post("/to-xmind", tags=["output"])
async def to_xmind_api(xmindmark: XMindMark):
    xmind_file = xmindmark_to_xmind_file(xmindmark.content)
    return {"xmind_file": xmind_file}