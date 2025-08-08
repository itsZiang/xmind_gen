from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY", None)
BASE_URL = os.getenv("BASE_URL", None)

misa_llm = ChatOpenAI(
    # model="misa-qwen3-235b",
    model="misa-qwen3-235b",
    base_url=BASE_URL,
    api_key=API_KEY,
    default_headers={
        "App-Code": "fresher"
    },
    max_tokens=8192,
    temperature=0.4,
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

# from dotenv import load_dotenv
# import os
# from core.g4f_adapter import ChatG4F  # class bạn đã tạo adapter từ g4f

# load_dotenv()

# misa_llm = ChatG4F(
#     model="gpt-4",
# )

# llm = ChatG4F(
#     model="gpt-3.5-turbo"
# )