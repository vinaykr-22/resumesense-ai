import io
import pdfplumber
import docx

def extract_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
                
    text = text.strip()
    if not text or len(text) < 50:
        raise ValueError("PDF appears to be scanned or image-only. Please upload a text-based PDF.")
        
    return text

def extract_from_docx(file_bytes: bytes) -> str:
    text = ""
    doc = docx.Document(io.BytesIO(file_bytes))
    for para in doc.paragraphs:
        if para.text:
            text += para.text + "\n"
            
    return text.strip()

def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().split('.')[-1]
    
    if ext == 'pdf':
        return extract_from_pdf(file_bytes)
    elif ext == 'docx':
        return extract_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported format: .{ext}")
