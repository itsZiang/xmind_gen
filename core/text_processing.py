import PyPDF2
from docx import Document

def extract_text_from_file(uploaded_file) -> str:
    """
    Trích xuất văn bản từ file PDF, DOCX, hoặc MD.
    Hỗ trợ cả Streamlit (BytesIO) và FastAPI (UploadFile).
    """
    try:
        # Lấy tên file từ Streamlit hoặc FastAPI
        filename = getattr(uploaded_file, "name", None) or getattr(uploaded_file, "filename", None)
        if filename is None:
            raise Exception("Không thể xác định tên file.")

        file_extension = filename.split('.')[-1].lower()

        # Lấy stream thực sự để đọc
        if hasattr(uploaded_file, "file"):  # FastAPI UploadFile
            file_stream = uploaded_file.file
        else:  # Streamlit BytesIO
            file_stream = uploaded_file

        file_stream.seek(0)

        if file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfReader(file_stream)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()

        elif file_extension == 'docx':
            doc = Document(file_stream)
            text = "\n".join([p.text for p in doc.paragraphs])
            return text.strip()

        elif file_extension == 'md':
            text = file_stream.read().decode('utf-8')
            return text.strip()

        else:
            raise Exception(f"Định dạng file '{file_extension}' không được hỗ trợ.")

    except Exception as e:
        raise Exception(f"Lỗi khi đọc file: {str(e)}")
