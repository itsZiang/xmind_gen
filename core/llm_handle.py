from core.llm_provider import LLMProvider
import os
from dotenv import load_dotenv
from core.prompt import create_xmindmark_prompt, create_split_text_prompt, create_global_title_prompt, create_edit_prompt, create_merge_xmindmark_prompt

load_dotenv()

API_KEY = os.getenv("API_KEY", None)
BASE_URL = os.getenv("BASE_URL", None)
MODEL = "gpt-4.1"
PROVIDER = "openai"
llm_provider = LLMProvider()
if BASE_URL:
    llm_provider.initialize_client(BASE_URL, PROVIDER, API_KEY)

def generate_xmindmark(text: str, user_requirements: str) -> str:
    """Xử lý văn bản bằng LLM và trả về nội dung XMindMark"""
    prompt = create_xmindmark_prompt(text, user_requirements)
    result = llm_provider.call_llm(prompt, MODEL)
    return result


# def find_title_text(text: str) -> str:
#     prompt = create_split_text_prompt(text)
#     result = llm_provider.call_llm(prompt, MODEL)
#     return result


def generate_global_title(text: str, user_requirements: str) -> str:
    prompt = create_global_title_prompt(text, user_requirements)
    result = llm_provider.call_llm(prompt, MODEL)
    return result


def split_text_with_llm(text: str, user_requirements: str) -> str:
    prompt = create_split_text_prompt(text, user_requirements)
    result = llm_provider.call_llm(prompt, MODEL)
    return result


def edit_xmindmark_with_llm(current_content: str, edit_request: str) -> str:    
    prompt = create_edit_prompt(current_content, edit_request)
    result = llm_provider.call_llm(prompt, MODEL)
    cleaned_result = result.strip()
    if cleaned_result.startswith('```'):
        lines = cleaned_result.split('\n')
        cleaned_result = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned_result
    return cleaned_result


def merge_xmindmark_with_llm(chunks_text: str, global_title: str, user_requirements: str) -> str:
    prompt = create_merge_xmindmark_prompt(chunks_text, global_title, user_requirements)
    result = llm_provider.call_llm(prompt, MODEL)
    return result