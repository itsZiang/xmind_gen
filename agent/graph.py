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


def build_graph():
    builder = StateGraph(DocumentState)

    builder.add_node("check_split", decide_split)
    builder.add_node("generate_global_title_node", generate_global_title_node)
    builder.add_node("split_chunks", split_into_chunks)
    builder.add_node("generate_direct", generate_xmindmark_direct)
    builder.add_node("generate_chunk_xmind", generate_xmindmark_for_chunk)
    builder.add_node("merge_xmind", merge_all_xmindmarks)

    builder.add_edge(START, "check_split")

    # Điều hướng theo `need_split`
    builder.add_conditional_edges(
        "check_split",
        lambda state: "split_chunks" if state["need_split"] else "generate_direct", path_map={"split_chunks": "split_chunks", "generate_direct": "generate_direct"}
    )

    # Sau khi split
    builder.add_edge("split_chunks", "generate_chunk_xmind")

    # Loop qua từng chunk
    def should_continue(state: DocumentState):
        return (
            "generate_chunk_xmind"
            if len(state["xmindmark_chunks_content"]) < len(state["chunks"])
            else "generate_global_title_node"
        )

    builder.add_conditional_edges("generate_chunk_xmind", should_continue, {"generate_chunk_xmind": "generate_chunk_xmind", "generate_global_title_node": "generate_global_title_node"})

    builder.add_edge("generate_global_title_node", "merge_xmind")

    # Kết thúc
    builder.add_edge("merge_xmind", END)
    builder.add_edge("generate_direct", END)

    return builder.compile()


# graph = build_graph()

# # Lưu hình ảnh ra file PNG
# graph_image_bytes = graph.get_graph(xray=True).draw_mermaid_png()
# with open("graph.png", "wb") as f:
#     f.write(graph_image_bytes)

# print("Saved to graph.png")

    
    
