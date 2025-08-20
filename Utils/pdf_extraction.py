import PyPDF2
import pytesseract
from pdf2image import convert_from_path

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from both digital and scanned PDFs."""
    text = ""

    # First try direct text extraction
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    # If no text found, fallback to OCR
    if not text.strip():
        images = convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img)

    return text
