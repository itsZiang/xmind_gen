from core.llm_provider import LLMProvider
import json
import os
from dotenv import load_dotenv
from core.prompt import create_structured_prompt
from core.text_processing import clean_json_string

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASELINE_URL")
MODEL = "gpt-4.1-mini"
PROVIDER = "openai"
llm_provider = LLMProvider()

def generate_xmindmark(text: str, user_requirements: str) -> str:
    """Xử lý văn bản bằng LLM và trả về nội dung XMindMark"""
    llm_provider.initialize_client(BASE_URL, PROVIDER, API_KEY)
    prompt = create_structured_prompt(text, user_requirements)
    result = llm_provider.call_llm(prompt, MODEL)
    json_str = clean_json_string(result)
    mindmap_data = json.loads(json_str)
    xmindmark_content = json_to_xmindmark(mindmap_data)
    return xmindmark_content


def json_to_xmindmark(mindmap_data: dict) -> str:
    """Chuyển đổi JSON thành định dạng XMindMark chính xác"""
    title = mindmap_data.get('title', 'Bản đồ tư duy')
    nodes = mindmap_data.get('nodes', [])
    
    output = f"{title}\n"
    
    def build_xmindmark(nodes, parent_id=None, level=0):
        result = ""
        child_nodes = [node for node in nodes if node.get('parent_id') == parent_id]
        for node in child_nodes:
            indent = "\t" * (level - 1) if level > 0 else ""
            result += f"{indent}- {node['label']}\n"
            result += build_xmindmark(nodes, node['id'], level + 1)
        return result
    
    root_node = next((node for node in nodes if node.get('level') == 0), None)
    if root_node:
        output += build_xmindmark(nodes, root_node['id'], 1)
    return output