import PyPDF2
from docx import Document

def extract_text_from_file(uploaded_file) -> str:
    """Trích xuất văn bản từ file PDF, DOCX, hoặc MD"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            return text.strip()
        
        elif file_extension == 'docx':
            doc = Document(uploaded_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        
        elif file_extension == 'md':
            text = uploaded_file.read().decode('utf-8')
            return text.strip()
        
        else:
            raise Exception(f"Định dạng file '{file_extension}' không được hỗ trợ.")
            
    except Exception as e:
        raise Exception(f"Lỗi khi đọc file: {str(e)}")
