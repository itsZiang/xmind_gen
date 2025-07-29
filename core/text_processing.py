import PyPDF2
from docx import Document
import re

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


def clean_json_string(json_str: str) -> str:
    """Cải thiện JSON string để xử lý các lỗi cú pháp"""
    try:
        start = json_str.find('{')
        end = json_str.rfind('}') + 1
        if start != -1 and end > start:
            json_str = json_str[start:end]
        else:
            json_str = json_str.strip()
    except:
        pass
    
    json_str = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', json_str)
    json_str = json_str.replace("'", '"')
    json_str = re.sub(r'\}\s*\{', '},{', json_str)
    json_str = re.sub(r'\]\s*\{', '],{', json_str)
    json_str = re.sub(r'\}\s*\]', '}]', json_str)
    json_str = re.sub(r',\s*\]', ']', json_str)
    json_str = re.sub(r',\s*\}', '}', json_str)
    json_str = re.sub(r'(\}\s*,\s*\{[^}]*?)(?=\s*\{)', r'\1,', json_str)
    
    return json_str