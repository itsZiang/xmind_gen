from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class WorkflowState(BaseModel):
    """State object cho LangGraph workflow"""
    input_text: str = ""
    user_requirements: str = ""
    current_xmindmark: str = ""
    edit_request: str = ""
    validation_errors: List[str] = []
    svg_url: str = ""
    xmind_file_url: str = ""
    workflow_status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3

class WorkflowStep(str, Enum):
    """Enum định nghĩa các bước trong workflow"""
    VALIDATE_INPUT = "validate_input"
    GENERATE_XMINDMARK = "generate_xmindmark"
    VALIDATE_XMINDMARK = "validate_xmindmark"
    EDIT_XMINDMARK = "edit_xmindmark"
    CONVERT_TO_SVG = "convert_to_svg"
    CONVERT_TO_XMIND = "convert_to_xmind"
    ERROR_HANDLER = "error_handler"
    COMPLETE = "complete"

class XMindWorkflow:
    """LangGraph workflow cho việc tạo và xử lý mind map"""
    
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Xây dựng LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Thêm các nodes
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("generate_xmindmark", self._generate_xmindmark)
        workflow.add_node("validate_xmindmark", self._validate_xmindmark)
        workflow.add_node("edit_xmindmark", self._edit_xmindmark)
        workflow.add_node("convert_to_svg", self._convert_to_svg)
        workflow.add_node("convert_to_xmind", self._convert_to_xmind)
        workflow.add_node("error_handler", self._error_handler)
        workflow.add_node("complete", self._complete)
        
        # Định nghĩa entry point
        workflow.set_entry_point("validate_input")
        
        # Định nghĩa các edges có điều kiện
        workflow.add_conditional_edges(
            "validate_input",
            self._should_proceed_after_validation,
            {
                "proceed": "generate_xmindmark",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_xmindmark",
            self._should_validate_xmindmark,
            {
                "validate": "validate_xmindmark",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "validate_xmindmark",
            self._should_proceed_after_xmindmark_validation,
            {
                "convert_svg": "convert_to_svg",
                "retry": "generate_xmindmark",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "edit_xmindmark",
            self._should_proceed_after_edit,
            {
                "validate": "validate_xmindmark",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "convert_to_svg",
            self._should_convert_to_xmind,
            {
                "convert_xmind": "convert_to_xmind",
                "complete": "complete",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "convert_to_xmind",
            lambda state: "complete",
            {
                "complete": "complete"
            }
        )
        
        workflow.add_conditional_edges(
            "error_handler",
            self._should_retry_or_end,
            {
                "retry": "generate_xmindmark",
                "end": END
            }
        )
        
        workflow.add_edge("complete", END)
        
        return workflow.compile()
    
    def _validate_input(self, state: WorkflowState) -> WorkflowState:
        """Validate đầu vào"""
        logger.info("Validating input...")
        
        errors = []
        if not state.input_text.strip():
            errors.append("Input text is required")
        
        if not state.user_requirements.strip():
            errors.append("User requirements are required")
        
        if len(state.input_text) > 50000:  # Giới hạn độ dài
            errors.append("Input text is too long (max 50000 characters)")
        
        state.validation_errors = errors
        state.workflow_status = "input_validated" if not errors else "input_validation_failed"
        
        logger.info(f"Input validation result: {state.workflow_status}")
        return state
    
    def _generate_xmindmark(self, state: WorkflowState) -> WorkflowState:
        """Tạo XMindMark từ text và requirements"""
        logger.info("Generating XMindMark...")
        
        try:
            from core.prompt import create_xmindmark_prompt
            
            prompt = create_xmindmark_prompt(state.input_text, state.user_requirements)
            result = self.llm_provider.call_llm(prompt, "gpt-4.1")
            
            state.current_xmindmark = result.strip()
            state.workflow_status = "xmindmark_generated"
            
            logger.info("XMindMark generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating XMindMark: {str(e)}")
            state.validation_errors.append(f"Failed to generate XMindMark: {str(e)}")
            state.workflow_status = "generation_failed"
        
        return state
    
    def _validate_xmindmark(self, state: WorkflowState) -> WorkflowState:
        """Validate XMindMark format và content"""
        logger.info("Validating XMindMark...")
        
        errors = []
        content = state.current_xmindmark
        
        if not content.strip():
            errors.append("XMindMark content is empty")
        
        # Kiểm tra format cơ bản
        lines = content.strip().split('\n')
        if len(lines) < 2:
            errors.append("XMindMark should have at least 2 lines (title + content)")
        
        # Kiểm tra cấu trúc phân cấp
        has_main_branches = any(line.startswith('- ') for line in lines[1:])
        if not has_main_branches:
            errors.append("XMindMark should have main branches starting with '- '")
        
        # Kiểm tra độ dài từ khóa
        for line in lines:
            clean_line = line.strip().lstrip('- \t')
            if len(clean_line) > 100:  # Từ khóa quá dài
                errors.append(f"Keyword too long: {clean_line[:50]}...")
        
        state.validation_errors = errors
        state.workflow_status = "xmindmark_validated" if not errors else "xmindmark_validation_failed"
        
        logger.info(f"XMindMark validation result: {state.workflow_status}")
        return state
    
    def _edit_xmindmark(self, state: WorkflowState) -> WorkflowState:
        """Chỉnh sửa XMindMark với LLM"""
        logger.info("Editing XMindMark...")
        
        try:
            from core.prompt import create_edit_prompt
            
            prompt = create_edit_prompt(state.current_xmindmark, state.edit_request)
            result = self.llm_provider.call_llm(prompt, "gpt-4.1")
            
            # Clean result
            cleaned_result = result.strip()
            if cleaned_result.startswith('```'):
                lines = cleaned_result.split('\n')
                cleaned_result = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned_result
            
            state.current_xmindmark = cleaned_result
            state.workflow_status = "xmindmark_edited"
            
            logger.info("XMindMark edited successfully")
            
        except Exception as e:
            logger.error(f"Error editing XMindMark: {str(e)}")
            state.validation_errors.append(f"Failed to edit XMindMark: {str(e)}")
            state.workflow_status = "edit_failed"
        
        return state
    
    def _convert_to_svg(self, state: WorkflowState) -> WorkflowState:
        """Convert XMindMark to SVG"""
        logger.info("Converting to SVG...")
        
        try:
            from core.utils import xmindmark_to_svg
            
            svg_url = xmindmark_to_svg(state.current_xmindmark)
            state.svg_url = svg_url
            state.workflow_status = "svg_converted"
            
            logger.info("SVG conversion successful")
            
        except Exception as e:
            logger.error(f"Error converting to SVG: {str(e)}")
            state.validation_errors.append(f"Failed to convert to SVG: {str(e)}")
            state.workflow_status = "svg_conversion_failed"
        
        return state
    
    def _convert_to_xmind(self, state: WorkflowState) -> WorkflowState:
        """Convert XMindMark to XMind file"""
        logger.info("Converting to XMind file...")
        
        try:
            from core.utils import xmindmark_to_xmind_file
            
            xmind_file_url = xmindmark_to_xmind_file(state.current_xmindmark)
            if xmind_file_url:
                state.xmind_file_url = xmind_file_url
                state.workflow_status = "xmind_converted"
                logger.info("XMind conversion successful")
            else:
                state.validation_errors.append("Failed to generate XMind file")
                state.workflow_status = "xmind_conversion_failed"
            
        except Exception as e:
            logger.error(f"Error converting to XMind: {str(e)}")
            state.validation_errors.append(f"Failed to convert to XMind: {str(e)}")
            state.workflow_status = "xmind_conversion_failed"
        
        return state
    
    def _error_handler(self, state: WorkflowState) -> WorkflowState:
        """Xử lý lỗi và quyết định retry"""
        logger.warning(f"Handling errors: {state.validation_errors}")
        
        state.retry_count += 1
        
        if state.retry_count <= state.max_retries:
            logger.info(f"Retrying... (attempt {state.retry_count}/{state.max_retries})")
            state.workflow_status = "retrying"
            # Clear một số lỗi có thể retry được
            state.validation_errors = [err for err in state.validation_errors 
                                     if "Failed to generate" not in err]
        else:
            logger.error("Max retries reached")
            state.workflow_status = "failed"
        
        return state
    
    def _complete(self, state: WorkflowState) -> WorkflowState:
        """Hoàn thành workflow"""
        logger.info("Workflow completed successfully")
        state.workflow_status = "completed"
        return state
    
    # Conditional edge functions
    def _should_proceed_after_validation(self, state: WorkflowState) -> str:
        return "proceed" if not state.validation_errors else "error"
    
    def _should_validate_xmindmark(self, state: WorkflowState) -> str:
        return "validate" if state.workflow_status == "xmindmark_generated" else "error"
    
    def _should_proceed_after_xmindmark_validation(self, state: WorkflowState) -> str:
        if not state.validation_errors:
            return "convert_svg"
        elif state.retry_count < state.max_retries:
            return "retry"
        else:
            return "error"
    
    def _should_proceed_after_edit(self, state: WorkflowState) -> str:
        return "validate" if state.workflow_status == "xmindmark_edited" else "error"
    
    def _should_convert_to_xmind(self, state: WorkflowState) -> str:
        if state.workflow_status == "svg_converted":
            return "convert_xmind"  # Có thể làm optional
        elif state.workflow_status == "svg_conversion_failed":
            return "error"
        else:
            return "complete"
    
    def _should_retry_or_end(self, state: WorkflowState) -> str:
        return "retry" if state.workflow_status == "retrying" else "end"
    
    # Public methods
    def generate_mindmap(self, input_text: str, user_requirements: str) -> WorkflowState:
        """Tạo mind map từ đầu"""
        initial_state = WorkflowState(
            input_text=input_text,
            user_requirements=user_requirements
        )
        
        logger.info("Starting mindmap generation workflow")
        result = self.graph.invoke(initial_state)
        if isinstance(result, dict):
            result = WorkflowState(**result)
        return result
    
    def edit_mindmap(self, current_xmindmark: str, edit_request: str) -> WorkflowState:
        """Chỉnh sửa mind map hiện có"""
        initial_state = WorkflowState(
            current_xmindmark=current_xmindmark,
            edit_request=edit_request,
            input_text="dummy",  # Required for validation
            user_requirements="dummy"
        )
        
        logger.info("Starting mindmap edit workflow")
        # Start từ edit step
        result = self.graph.invoke(initial_state, {"node": "edit_xmindmark"})
        if isinstance(result, dict):
            result = WorkflowState(**result)
        return result