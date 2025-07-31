from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY", None)
BASE_URL = os.getenv("BASE_URL", None)

misa_llm = ChatOpenAI(
    # model="misa-qwen3-30b",
    model="misa-qwen3-235b",
    base_url=BASE_URL,
    api_key=API_KEY,
    default_headers={
        "App-Code": "fresher"
    },
    max_tokens=1024,
    temperature=0.7,
    extra_body={
        "service": "test-aiservice.misa.com.vn",
        "chat_template_kwargs": {            
            "enable_thinking": False
        }
    }
)

llm = ChatOpenAI(
    model="gpt-4.1-mini",
)