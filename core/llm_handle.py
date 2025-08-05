# core/llm_handle.py

from core.llm_provider import llm, misa_llm
from dotenv import load_dotenv
from core.prompt import create_xmindmark_prompt, create_split_text_prompt, create_global_title_prompt, create_edit_prompt, create_merge_xmindmark_prompt, create_xmindmark_no_docs_prompt, create_xmindmark_with_search_prompt
from core.tavily_search import tavily_search
import time
import logging
from typing import List, Dict, Optional

load_dotenv()
logger = logging.getLogger(__name__)

def generate_xmindmark(text: str, user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    """Xử lý văn bản bằng LLM và trả về nội dung XMindMark với timeout"""
    start_time = time.time()
    try:
        prompt = create_xmindmark_prompt(text, user_requirements, conversation_history)
        result = misa_llm.invoke(prompt, config={"timeout": 60}).content
        processing_time = time.time() - start_time
        logger.info(f"Generated mindmap in {processing_time:.2f}s")
        return str(result) if result else ""
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error generating mindmap after {processing_time:.2f}s: {e}")
        raise e

def generate_global_title(text: str, user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    prompt = create_global_title_prompt(text, user_requirements, conversation_history)
    result = misa_llm.invoke(prompt).content
    return str(result) if result else ""

def split_text_with_llm(text: str, user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    prompt = create_split_text_prompt(text, user_requirements, conversation_history)
    result = misa_llm.invoke(prompt).content
    return str(result) if result else ""

def edit_xmindmark_with_llm(current_content: str, edit_request: str, conversation_history: Optional[List[Dict[str, str]]] = None):
    prompt = create_edit_prompt(current_content, edit_request, conversation_history)
    for chunk in misa_llm.stream(prompt):
        yield chunk.content

def merge_xmindmark_with_llm(chunks_text: str, global_title: str, user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    prompt = create_merge_xmindmark_prompt(chunks_text, global_title, user_requirements, conversation_history)
    result = misa_llm.invoke(prompt).content
    return str(result) if result else ""

def generate_xmindmark_no_docs(user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None):
    prompt = create_xmindmark_no_docs_prompt(user_requirements, conversation_history)
    for chunk in misa_llm.stream(prompt):
        yield chunk.content

def generate_xmindmark_with_search(user_requirements: str, conversation_history: Optional[List[Dict[str, str]]] = None):
    # Tạo truy vấn tìm kiếm dựa trên yêu cầu và lịch sử hội thoại
    search_query = user_requirements
    if conversation_history:
        context = "\n".join([f"{item['role']}: {item['content']}" for item in conversation_history[-5:]])  # Giới hạn 5 tin nhắn gần nhất
        search_query = f"{context}\nCurrent request: {user_requirements}"
    
    context = tavily_search(search_query)
    prompt = create_xmindmark_with_search_prompt(context, user_requirements, conversation_history)
    for chunk in misa_llm.stream(prompt):
        yield chunk.content