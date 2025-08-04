import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))


def tavily_search(query: str):
    try:
        response = client.search(query, topic="general", max_results=3, include_raw_content="text")
        content_list = []
        for result in response['results']:
            if result.get('raw_content'):  # Check if not None and not empty
                content_list.append(result['raw_content'])
        
        if not content_list:  # If no valid content found
            return "Không tìm thấy thông tin phù hợp."
            
        return "\n\n---\n\n".join(content_list)
    except Exception as e:
        return f"Lỗi tìm kiếm: {str(e)}"

