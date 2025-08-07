import os
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import Optional

def generate_base_filename() -> str:
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    return timestamp

def get_xmindmark_cmd() -> str:
    """Tìm đường dẫn thực thi xmindmark"""
    cmd = shutil.which("xmindmark")
    if cmd is None:
        raise FileNotFoundError(
            "Không tìm thấy tool 'xmindmark'. Hãy chắc chắn bạn đã cài bằng `pip install xmindmark` và thêm vào PATH."
        )
    return cmd

def validate_xmindmark(content: str) -> str:
    """Kiểm tra và chuẩn hóa nội dung XMindMark"""
    # Loại bỏ khoảng trắng thừa ở đầu và cuối
    content = content.strip()
    
    # Kiểm tra xem có nội dung không
    if not content:
        raise ValueError("Nội dung XMindMark không được để trống")

    # Đảm bảo có ít nhất một topic (dòng không trống và không phải comment)
    valid_lines = [line.strip() for line in content.splitlines() 
                  if line.strip() and not line.strip().startswith('#')]
    if not valid_lines:
        raise ValueError("Nội dung XMindMark phải có ít nhất một topic")

    # Đảm bảo dòng đầu tiên là root topic (không có indent)
    if valid_lines[0].startswith((' ', '\t')):
        content = "Root Topic\n" + content

    return content

def xmindmark_to_svg(xmindmark_content: str) -> str:
    """Chuyển đổi XMindMark thành SVG và lưu vào static/output_svg/, trả về đường link ảnh"""
    import time
    
    STATIC_DIR = os.path.join(os.getcwd(), 'static', 'output_svg')
    os.makedirs(STATIC_DIR, exist_ok=True)
    base_filename = generate_base_filename()

    # Validate và chuẩn hóa nội dung XMindMark
    try:
        xmindmark_content = validate_xmindmark(xmindmark_content)
    except ValueError as e:
        raise ValueError(f"Nội dung XMindMark không hợp lệ: {str(e)}")

    # Tạo thư mục tạm thời với cleanup=False để tự kiểm soát việc xóa
    temp_dir = tempfile.mkdtemp()
    try:
        xmindmark_path = os.path.join(temp_dir, f"{base_filename}.xmindmark")
        with open(xmindmark_path, 'w', encoding='utf-8') as f:
            f.write(xmindmark_content)

        # Chạy CLI để sinh SVG và kiểm tra kết quả
        result = subprocess.run(
            [get_xmindmark_cmd(), '--format', 'svg', xmindmark_path],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=20
        )
        if result.returncode != 0:
            raise RuntimeError(f"Lỗi khi chuyển đổi SVG: {result.stderr}")

        # Đợi một chút để đảm bảo file được ghi hoàn tất
        time.sleep(0.5)

        # Tìm file SVG
        svg_path = os.path.join(temp_dir, f"{base_filename}.svg")
        if not os.path.exists(svg_path):
            svg_files = [f for f in os.listdir(temp_dir) if f.endswith('.svg')]
            if svg_files:
                svg_path = os.path.join(temp_dir, svg_files[0])
            else:
                raise FileNotFoundError("Không tìm thấy file SVG sau khi convert. Stderr: " + result.stderr)

        # Copy SVG về static/output_svg/
        output_svg_path = os.path.join(STATIC_DIR, os.path.basename(svg_path))
        shutil.copy2(svg_path, output_svg_path)

        return output_svg_path  # Trả về path thực tế thay vì URL
    except Exception as e:
        # Re-raise exception sau khi cleanup
        raise e
    finally:
        # Cleanup thư mục tạm, bỏ qua lỗi nếu có
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass  # Bỏ qua lỗi khi xóa thư mục tạm
    

def xmindmark_to_xmind_file(xmindmark_content: str) -> Optional[str]:
    """
    Chuyển đổi XMindMark thành file .xmind và trả về đường dẫn tương đối của file.
    """
    import time
    
    output_dir = os.path.join("static", "output_xmind")
    os.makedirs(output_dir, exist_ok=True)
    base_filename = generate_base_filename()

    # Validate và chuẩn hóa nội dung XMindMark
    try:
        xmindmark_content = validate_xmindmark(xmindmark_content)
    except ValueError as e:
        raise ValueError(f"Nội dung XMindMark không hợp lệ: {str(e)}")

    # Tạo thư mục tạm thời
    temp_dir = tempfile.mkdtemp()
    try:
        # Ghi nội dung XMindMark vào file tạm
        xmindmark_file = os.path.join(temp_dir, f"{base_filename}.xmindmark")
        with open(xmindmark_file, 'w', encoding='utf-8') as f:
            f.write(xmindmark_content)

        # Gọi CLI xmindmark và kiểm tra kết quả
        result = subprocess.run(
            [get_xmindmark_cmd(), xmindmark_file],
            cwd=output_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError(f"Lỗi khi chuyển đổi XMind: {result.stderr}")

        # Đợi một chút để đảm bảo file được ghi hoàn tất
        time.sleep(0.5)

        # Tìm file .xmind mới nhất trong output_dir
        xmind_files = [
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.endswith('.xmind')
        ]

        if not xmind_files:
            raise FileNotFoundError("Không tìm thấy file XMind sau khi convert. Stderr: " + result.stderr)

        latest_file = max(xmind_files, key=os.path.getmtime)
        return latest_file  # Trả về path thực tế thay vì URL

    except Exception as e:
        # Re-raise exception sau khi cleanup
        raise e
    finally:
        # Cleanup thư mục tạm, bỏ qua lỗi nếu có
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass  # Bỏ qua lỗi khi xóa thư mục tạm