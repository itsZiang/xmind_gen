from core.llm_provider import LLMProvider
import json
import os
from dotenv import load_dotenv
from core.prompt import create_xmindmark_prompt
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

