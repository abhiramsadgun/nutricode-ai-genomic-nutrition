from PyPDF2 import PdfReader

def extract_text_from_pdf(fp) -> str:
    try:
        reader = PdfReader(fp)
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception:
        return ""
