from agent.graph import build_graph

def generate_xmindmark_langgraph(text: str, user_requirements: str) -> str:
    graph = build_graph()
    response = graph.invoke({
        "input_text": f"""{text}""", 
        "user_requirements": f"""{user_requirements}""",
        "need_split": False,
        "chunks": [],
        "xmindmark_chunks_content": [],
        "xmindmark_final": "",
        "global_title": ""
    })
    return response["xmindmark_final"]


async def generate_xmindmark_langgraph_stream(text: str, user_requirements: str):
    graph = build_graph()
    async for event in graph.astream_events({
        "input_text": f"""{text}""", 
        "user_requirements": f"""{user_requirements}""",
        "need_split": False,
        "chunks": [],
        "xmindmark_chunks_content": [],
        "xmindmark_final": "",
        "global_title": ""
    }, version="v2"):
        if (event["event"] == "on_chat_model_stream" and 
            event.get("metadata", {}).get('langgraph_node','') in ["merge_xmind", "generate_direct"]):
            data = event.get("data", {})
            if "chunk" in data:
                yield data["chunk"].content
                
    
# async def test_stream():
#     graph = build_graph()
#     async for event in graph.astream_events({
#         "input_text": f"""I. Mục tiêu • Giao tiếp cơ bản sau 3 tháng • Đạt IELTS 6.5 trong 1 năm II. Kỹ năng cần cải thiện • Nghe • Nói • Đọc • Viết III. Tài nguyên học tập • Ứng dụng: Duolingo, ELSA • Sách: English Grammar in Use, Cambridge IELTS • Podcast: BBC Learning English IV. Thời gian biểu hàng tuần • Thứ 2-6: 1 tiếng/ngày (sáng sớm) • Thứ 7, CN: 2 tiếng/ngày (chia sáng + chiều) V. Kiểm tra tiến độ • Kiểm tra từ vựng hàng tuần • Làm đề IELTS mỗi tháng""", 
#         "user_requirements": f"""tóm tắt""",
#         "need_split": False,
#         "chunks": [],
#         "xmindmark_chunks_content": [],
#         "xmindmark_final": "",
#         "global_title": ""
#     }, version="v2"):
#         if (event["event"] == "on_chat_model_stream" and 
#             event.get("metadata", {}).get('langgraph_node','') in ["merge_xmind", "generate_direct"]):
#             data = event.get("data", {})
#             if "chunk" in data:
#                 print(data["chunk"].content, end="", flush=True)
#         # print(f"Node: {event['metadata'].get('langgraph_node','')}. Type: {event['event']}. Name: {event['name']}")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(test_stream())