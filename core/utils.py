import os
import subprocess
import tempfile
import shutil
from datetime import datetime

def generate_base_filename() -> str:
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    return timestamp


def xmindmark_to_svg(xmindmark_content: str) -> str:
    """Chuyển đổi XMindMark thành SVG và lưu vào static/output_svg/, trả về đường link ảnh"""
    
    STATIC_DIR = os.path.join(os.getcwd(), 'static', 'output_svg')
    os.makedirs(STATIC_DIR, exist_ok=True)
    base_filename = generate_base_filename()

    with tempfile.TemporaryDirectory() as temp_dir:
        xmindmark_path = os.path.join(temp_dir, f"{base_filename}.xmindmark")
        with open(xmindmark_path, 'w', encoding='utf-8') as f:
            f.write(xmindmark_content)

        # Chạy CLI để sinh SVG
        subprocess.run(
            ['xmindmark', '--format', 'svg', xmindmark_path],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=20
        )

        # Tìm file SVG
        svg_path = os.path.join(temp_dir, f"{base_filename}.svg")
        if not os.path.exists(svg_path):
            svg_files = [f for f in os.listdir(temp_dir) if f.endswith('.svg')]
            if svg_files:
                svg_path = os.path.join(temp_dir, svg_files[0])
            else:
                raise FileNotFoundError("Không tìm thấy file SVG sau khi convert.")

        # Copy SVG về static/output_svg/
        output_svg_path = os.path.join(STATIC_DIR, os.path.basename(svg_path))
        shutil.copy(svg_path, output_svg_path)

        image_url = f"/static/output_svg/{os.path.basename(svg_path)}"
        return image_url
    

def xmindmark_to_xmind_file(xmindmark_content: str) -> str | None:
    """
    Chuyển đổi XMindMark thành XMind và trả về đường dẫn tới file .xmind
    """
    output_dir = os.path.join("static", "output_xmind")
    os.makedirs(output_dir, exist_ok=True)
    base_filename = generate_base_filename()

    # Ghi nội dung .xmindmark vào file tạm
    temp_dir = tempfile.mkdtemp()
    xmindmark_file = os.path.join(temp_dir, f"{base_filename}.xmindmark")
    with open(xmindmark_file, 'w', encoding='utf-8') as f:
        f.write(xmindmark_content)

    # Gọi CLI xmindmark, cwd là output_dir
    subprocess.run(
        ['xmindmark', xmindmark_file],
        cwd=output_dir,
        capture_output=True,
        text=True,
        timeout=10
    )

    # Tìm file .xmind được tạo ra
    xmind_files = [f for f in os.listdir(output_dir) if f.endswith('.xmind')]
    if not xmind_files:
        return None
    
    xmind_file_path = os.path.join(output_dir, xmind_files[0])
    return f"/{xmind_file_path}"
