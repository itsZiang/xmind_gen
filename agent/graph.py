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

# response = graph.invoke({
#     "input_text": """Biên bản họp tuần eKYC
# Ngày 01 tháng 03 năm 2023
# I.
# Thành phần tham dự
# 1. Chủ trì buổi họp: VMQuang
# 2. Thư ký: LMHung
# 3. Thành viên tham gia buổi họp
# II.
# - Tham gia: LMHieu, TTAnh, LMHung, TMChien
# - Vắng:
# Nội dung cuộc họp
# Mảng việc
# Kết quả
# Kế hoạch chung - Hiện xác định được 3 trường thông tin chatbot có thể trả lời:
# tính năng, dùng thử và giá cả
# - Chuẩn bị dữ liệu: đang thu thập sản phẩm quản trị doanh
# nghiệp:có khoảng 28 sản phẩm
# Thu thập dữ liệu - Khó khăn là chưa có công cụ crawl vẫn đang còn phải crawl
# bằng tay
# - Xem xét tạo một form thông tin đầu vào chuẩn và nhở các
# PM sản phẩm hỗ trợ gửi thông tin đầu vào.
# - Xem xét khả năng chỉnh sửa dữ liệu sau khi đưa vì giá cả,
# tính năng có thể thay đổi
# Embbeding và search
# vector - Thử nghiệm mô hình sbert nhưng kết quả chỉ đúng với đoạn
# văn ngắn, mà đoạn văn của mình dài.
# - Trước tiên vẫn ưu tiên sử dụng Open AI, sau đó sẽ thay đổi
# sau. Vân sử dụng cosine làm độ đo khi search
# - Tuấn anh tiếp tục thử database dành cho vector - milvus với
# dữ liệu của mình để đánh giá độ chính xác
# Tích hợp với website - Đã trao đổi với dự án website về việc hỗ trợ tích hợp
# - Cần xác định thời gian tích hợp hộp thoại sẽ mất bao lâu
# Công việc tiếp theo:
# - Xây dựng API mapping câu hỏi với document trả lời
# - Tiếp tục bổ sung dữ liệu
# - Nghiên cứu về cách giữ context cho đoạn hội thoại""", 
#     "user_requirements": "Đây là yêu cầu của người dùng",
#     "need_split": False,
#     "chunks": [],
#     "xmindmark_chunks_content": [],
#     "xmindmark_final": "",
#     "global_title": ""
# })
# # print(response["xmindmark_final"])
# print(response)

