import os
from tavily import TavilyClient
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional

load_dotenv()
logger = logging.getLogger(__name__)

client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))


def tavily_search(query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    try:
        search_query = query
        if conversation_history:
            context = "\n".join([f"{item['role']}: {item['content']}" for item in conversation_history[-5:]])
            search_query = f"{context}\nCurrent request: {query}"
        
        response = client.search(
            query=search_query,
            topic="general",
            max_results=5,  
            include_raw_content="text"
        )
        
        content_list = []
        seen_content = set()  
        for result in response['results']:
            raw_content = result.get('raw_content')
            if raw_content and raw_content not in seen_content:
                if len(raw_content) > 50 and not any(keyword in raw_content.lower() for keyword in ["ad", "sponsored", "advertisement"]):
                    content_list.append(raw_content)
                    seen_content.add(raw_content)
        
        if not content_list:
            logger.warning(f"No relevant search results for query: {query}")
            return "Không tìm thấy thông tin phù hợp."
        
        # Giới hạn độ dài mỗi nội dung để tránh vượt token
        content_list = [content[:2000] for content in content_list]
        return "\n\n---\n\n".join(content_list)
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return f"Lỗi tìm kiếm: {str(e)}"

