from core.llm_provider import LLMProvider
import json
import os
import streamlit as st
from dotenv import load_dotenv
from core.prompt import create_xmindmark_prompt, create_edit_prompt
from core.text_processing import clean_json_string

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL = "gpt-4.1"
PROVIDER = "openai"
llm_provider = LLMProvider()

def generate_xmindmark(text: str, user_requirements: str) -> str:
    """Xử lý văn bản bằng LLM và trả về nội dung XMindMark"""
    llm_provider.initialize_client(BASE_URL, PROVIDER, API_KEY)
    prompt = create_xmindmark_prompt(text, user_requirements)
    result = llm_provider.call_llm(prompt, MODEL)
    return result

def edit_xmindmark_with_llm(current_content: str, edit_request: str) -> str:
    if not llm_provider.client:
        llm_provider.initialize_client(BASE_URL, PROVIDER, API_KEY)
        
    prompt = create_edit_prompt(current_content, edit_request)
    try:
        result = llm_provider.call_llm(prompt, MODEL)
        cleaned_result = result.strip()
        if cleaned_result.startswith('```'):
            lines = cleaned_result.split('\n')
            cleaned_result = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned_result
        return cleaned_result
    except Exception as e:
        st.error(f"Lỗi khi chỉnh sửa bằng LLM: {str(e)}")
        return current_content
