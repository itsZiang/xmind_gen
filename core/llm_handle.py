from core.llm_provider import llm, misa_llm
from dotenv import load_dotenv
from core.prompt import create_xmindmark_prompt, create_split_text_prompt, create_global_title_prompt, create_edit_prompt, create_merge_xmindmark_prompt, create_xmindmark_no_docs_prompt, create_xmindmark_with_search_prompt, create_edit_with_search_prompt
from core.tavily_search import tavily_search

load_dotenv()


used_llm = misa_llm

def edit_xmindmark_with_llm_search(user_requirements: str, edit_request: str, current_xmindmark: str):
    search_query = f"{user_requirements} {edit_request}".strip()
    context = tavily_search(search_query)

    prompt = create_edit_with_search_prompt(current_xmindmark, edit_request, context, user_requirements)

    for chunk in misa_llm.stream(prompt):
        yield chunk.content
        

def edit_xmindmark_with_llm(current_content: str, edit_request: str):    
    prompt = create_edit_prompt(current_content, edit_request)
    for chunk in used_llm.stream(prompt):
        yield chunk.content


def generate_xmindmark(text: str, user_requirements: str) -> str:
    """Xử lý văn bản bằng LLM và trả về nội dung XMindMark"""
    prompt = create_xmindmark_prompt(text, user_requirements)
    result = used_llm.invoke(prompt).content
    return str(result) if result else ""


def generate_global_title(text: str, user_requirements: str) -> str:
    prompt = create_global_title_prompt(text, user_requirements)
    result = used_llm.invoke(prompt).content
    return str(result) if result else ""


def split_text_with_llm(text: str, user_requirements: str) -> str:
    prompt = create_split_text_prompt(text, user_requirements)
    result = used_llm.invoke(prompt).content
    return str(result) if result else ""


def merge_xmindmark_with_llm(chunks_text: str, global_title: str, user_requirements: str) -> str:
    prompt = create_merge_xmindmark_prompt(chunks_text, global_title, user_requirements)
    result = used_llm.invoke(prompt).content
    return str(result) if result else ""


def generate_xmindmark_no_docs_stream(user_requirements: str):
    prompt = create_xmindmark_no_docs_prompt(user_requirements)
    for chunk in used_llm.stream(prompt):
        if chunk.content:
            yield chunk.content
        
        
def generate_xmindmark_no_docs(user_requirements: str) -> str:
    """Xử lý văn bản bằng LLM và trả về nội dung XMindMark"""
    prompt = create_xmindmark_no_docs_prompt(user_requirements)
    result = used_llm.invoke(prompt).content
    return str(result) if result else ""
        
        
def generate_xmindmark_with_search_stream(user_requirements: str):
    context = tavily_search(user_requirements)
    prompt = create_xmindmark_with_search_prompt(context, user_requirements)
    for chunk in used_llm.stream(prompt):
        if chunk.content:
            yield chunk.content


def generate_xmindmark_with_search(user_requirements: str) -> str:
    context = tavily_search(user_requirements)
    prompt = create_xmindmark_with_search_prompt(context, user_requirements)
    result = used_llm.invoke(prompt).content
    return str(result) if result else ""