from langgraph.graph import StateGraph, START, END
from agent.utils.state import DocumentState
from agent.utils.nodes import (
    decide_split,
    split_into_chunks,
    generate_xmindmark_direct,
    # generate_xmindmark_for_chunk,
    generate_all_chunks_parallel,
    merge_all_xmindmarks,
    generate_global_title_node,
)
from IPython.display import Image, display


def build_graph():
    builder = StateGraph(DocumentState)

    builder.add_node("check_split", decide_split)
    builder.add_node("generate_global_title", generate_global_title_node)
    builder.add_node("split_chunks", split_into_chunks)
    builder.add_node("generate_direct", generate_xmindmark_direct)
    builder.add_node("generate_chunk_xmind", generate_all_chunks_parallel)
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

    # FIXED: Global title sau split, trước chunk processing
    builder.add_edge("split_chunks", "generate_global_title")
    builder.add_edge("generate_global_title", "generate_chunk_xmind")

    def should_continue_chunks(state: DocumentState):
        processed = len(state["xmindmark_chunks_content"])
        total = len(state["chunks"])
        
        print(f"DEBUG: Processed {processed}/{total} chunks")
        
        if processed < total:
            return "generate_chunk_xmind"
        else:
            return "merge_xmind"

    builder.add_conditional_edges(
        "generate_chunk_xmind", 
        should_continue_chunks,
        {
            "generate_chunk_xmind": "generate_chunk_xmind",
            "merge_xmind": "merge_xmind"
        }
    )

    builder.add_edge("merge_xmind", END)
    builder.add_edge("generate_direct", END)

    return builder.compile()


# graph = build_graph()

# # Lưu hình ảnh ra file PNG
# graph_image_bytes = graph.get_graph(xray=True).draw_mermaid_png()
# with open("graph.png", "wb") as f:
#     f.write(graph_image_bytes)

# print("Saved to graph.png")

