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