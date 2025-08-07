from langgraph.graph import StateGraph, START, END
from agent.utils.state import DocumentState
from agent.utils.nodes import (
    decide_split,
    split_into_chunks,
    generate_xmindmark_direct,
    generate_xmindmark_for_chunk,
    merge_all_xmindmarks,
    generate_global_title_node,
)
from IPython.display import Image, display
from langgraph.types import Send


def build_graph():
    builder = StateGraph(DocumentState)

    builder.add_node("check_split", decide_split)
    builder.add_node("generate_global_title", generate_global_title_node)
    builder.add_node("split_chunks", split_into_chunks)
    builder.add_node("generate_direct", generate_xmindmark_direct)
    builder.add_node("generate_chunk_xmind", generate_xmindmark_for_chunk)
    builder.add_node("merge_xmind", merge_all_xmindmarks)

    builder.add_edge(START, "check_split")

    def route_after_split(state: DocumentState):
        if state["need_split"]:
            return "split_chunks"
        else:
            return "generate_direct"

    builder.add_conditional_edges(
        "check_split",
        route_after_split,
        {
            "split_chunks": "split_chunks", 
            "generate_direct": "generate_direct"
        }
    )
    
    def continue_generate_chunk_xmind(state: DocumentState):
        return [Send("generate_chunk_xmind", {"chunk_index": idx, "chunk_content": chunk_content, "user_requirements": state["user_requirements"]}) for idx, chunk_content in enumerate(state["chunks"])]


    builder.add_edge("split_chunks", "generate_global_title")
    builder.add_conditional_edges("generate_global_title", continue_generate_chunk_xmind, ["generate_chunk_xmind"])
    
    
    builder.add_edge("generate_chunk_xmind", "merge_xmind")
    builder.add_edge("merge_xmind", END)
    builder.add_edge("generate_direct", END)

    return builder.compile()


# graph = build_graph()

# # Lưu hình ảnh ra file PNG
# graph_image_bytes = graph.get_graph(xray=True).draw_mermaid_png()
# with open("graph1.png", "wb") as f:
#     f.write(graph_image_bytes)

# print("Saved to graph.png")

