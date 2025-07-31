from core.llm_provider import llm, misa_llm
from dotenv import load_dotenv
from core.prompt import create_xmindmark_prompt, create_split_text_prompt, create_global_title_prompt, create_edit_prompt, create_merge_xmindmark_prompt

load_dotenv()


def generate_xmindmark(text: str, user_requirements: str) -> str:
    """Xử lý văn bản bằng LLM và trả về nội dung XMindMark"""
    prompt = create_xmindmark_prompt(text, user_requirements)
    result = llm.invoke(prompt).content
    return str(result) if result else ""


# def find_title_text(text: str) -> str:
#     prompt = create_split_text_prompt(text)
#     result = llm_provider.call_llm(prompt, MODEL)
#     return result


def generate_global_title(text: str, user_requirements: str) -> str:
    prompt = create_global_title_prompt(text, user_requirements)
    result = llm.invoke(prompt).content
    return str(result) if result else ""


def split_text_with_llm(text: str, user_requirements: str) -> str:
    prompt = create_split_text_prompt(text, user_requirements)
    result = llm.invoke(prompt).content
    return str(result) if result else ""


def edit_xmindmark_with_llm(current_content: str, edit_request: str):    
    prompt = create_edit_prompt(current_content, edit_request)
    for chunk in llm.stream(prompt):
        yield chunk.content


def merge_xmindmark_with_llm(chunks_text: str, global_title: str, user_requirements: str) -> str:
    prompt = create_merge_xmindmark_prompt(chunks_text, global_title, user_requirements)
    result = llm.invoke(prompt).content
    return str(result) if result else ""