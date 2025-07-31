from typing import Optional
from core.workflow import XMindWorkflow, WorkflowState
from core.llm_provider import LLMProvider
import logging

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Manager class để quản lý các workflow instances"""
    
    def __init__(self):
        self.llm_provider = LLMProvider()
        self.workflow: Optional[XMindWorkflow] = None
    
    def initialize(self, base_url: str, provider: str, api_key: str = None):
        """Khởi tạo LLM provider và workflow"""
        try:
            self.llm_provider.initialize_client(base_url, provider, api_key)
            self.workflow = XMindWorkflow(self.llm_provider)
            logger.info("Workflow manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize workflow manager: {str(e)}")
            raise
    
    def generate_mindmap_with_workflow(self, input_text: str, user_requirements: str) -> dict:
        """Tạo mind map sử dụng workflow"""
        if not self.workflow:
            raise ValueError("Workflow not initialized")
        
        try:
            result = self.workflow.generate_mindmap(input_text, user_requirements)
            
            return {
                "success": result.workflow_status == "completed",
                "xmindmark": result.current_xmindmark,
                "svg_url": result.svg_url,
                "xmind_file_url": result.xmind_file_url,
                "errors": result.validation_errors,
                "status": result.workflow_status
            }
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "success": False,
                "errors": [str(e)],
                "status": "failed"
            }
    
    def edit_mindmap_with_workflow(self, current_xmindmark: str, edit_request: str) -> dict:
        """Chỉnh sửa mind map sử dụng workflow"""
        if not self.workflow:
            raise ValueError("Workflow not initialized")
        
        try:
            result = self.workflow.edit_mindmap(current_xmindmark, edit_request)
            
            return {
                "success": result.workflow_status in ["completed", "svg_converted"],
                "edited_xmindmark": result.current_xmindmark,
                "svg_url": result.svg_url,
                "errors": result.validation_errors,
                "status": result.workflow_status
            }
        except Exception as e:
            logger.error(f"Edit workflow execution failed: {str(e)}")
            return {
                "success": False,
                "errors": [str(e)],
                "status": "failed"
            }