"""File reading utilities for various formats."""

from io import BytesIO
from config import TEXT_ENCODINGS

# PDF support
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


def read_pdf(file_bytes):
    """Read PDF from uploaded file bytes."""
    if not PDF_SUPPORT:
        raise Exception("PyPDF2 not installed")
    text = ""
    pdf_file = BytesIO(file_bytes)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text


def read_text_file(file_bytes, encodings=None):
    """Read text file with multiple encoding attempts."""
    if encodings is None:
        encodings = TEXT_ENCODINGS
    
    for encoding in encodings:
        try:
            return file_bytes.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise Exception("Could not decode file")


def read_file_smart(uploaded_file):
    """Smart file reader for Streamlit uploaded files."""
    file_bytes = uploaded_file.read()
    ext = uploaded_file.name.split('.')[-1].lower()
    
    if ext == 'pdf':
        if not PDF_SUPPORT:
            return None, "PDF support not installed"
        try:
            return read_pdf(file_bytes), "PDF"
        except Exception as e:
            return None, f"PDF error: {str(e)}"
    else:
        try:
            content, encoding = read_text_file(file_bytes)
            return content, encoding
        except Exception as e:
            return None, f"Error: {str(e)}"