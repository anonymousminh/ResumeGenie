from docx import Document
from pypdf import PdfReader
import io
import re
import string


def clean_pdf_text(text: str) -> str:
    """Cleans PDF text by removing metadata artifacts, binary data, and normalizing content."""
    if not text:
        return ""

    print(f"Original text length: {len(text)}")  # Debug log
    print(f"First 200 chars: {text[:200]}")  # Debug log

    # Remove PDF metadata patterns
    # Remove patterns like "<< /Linearized 1 /L 130930 /H [ 1277 181 ] /O 7 /E 130335 /N 1 /T 130646 >>"
    text = re.sub(r"<<\s*/[^>]*>>", "", text)

    # Remove other common PDF artifacts
    text = re.sub(r"/\w+\s+\d+", "", text)  # Remove patterns like "/Linearized 1"
    text = re.sub(
        r"\[\s*\d+\s+\d+\s*\]", "", text
    )  # Remove coordinate arrays like "[ 1277 181 ]"

    # Remove binary/encoded data patterns - BE LESS AGGRESSIVE
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        # Skip empty lines
        if len(line.strip()) == 0:
            continue

        # Skip obvious PDF metadata
        if (
            line.strip().startswith("%PDF")
            or "<<" in line
            or "/Linearized" in line
            or line.strip().startswith("obj")
            or line.strip().startswith("endobj")
        ):
            continue

        # Keep lines that have some readable content
        readable_chars = len(re.findall(r"[a-zA-Z0-9\s]", line))
        if readable_chars > 0:  # Much more lenient - just needs some readable chars
            cleaned_lines.append(line)

    # Rejoin lines and clean up
    text = "\n".join(cleaned_lines)

    # Remove excessive whitespace and normalize
    text = re.sub(r"\s+", " ", text)  # Replace multiple whitespace with single space
    text = re.sub(r"\n\s*\n", "\n", text)  # Remove empty lines
    text = text.strip()

    print(f"Cleaned text length: {len(text)}")  # Debug log
    print(f"Cleaned first 200 chars: {text[:200]}")  # Debug log

    return text


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text from PDF bytes."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"

        # Clean the extracted text to remove PDF metadata and binary data
        cleaned_text = clean_pdf_text(text)

        # Additional validation - if the cleaned text is too short or contains mostly garbage
        if (
            len(cleaned_text.strip()) < 50
        ):  # Very short text might indicate extraction failure
            return "Unable to extract readable text from this PDF. Please ensure the PDF contains selectable text."

        return cleaned_text

    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"


def extract_text_from_docx(docx_bytes: bytes) -> str:
    """Extracts text from DOCX bytes."""
    document = Document(io.BytesIO(docx_bytes))
    text = ""
    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"
    return text


def parse_document(file_bytes: bytes, file_type: str) -> str:
    """Parses document bytes based on file type and returns extracted text."""
    if file_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    elif (
        file_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return extract_text_from_docx(file_bytes)
    elif file_type == "application/msword":
        return f"Unsupported .doc file type for full parsing. Raw bytes length: {len(file_bytes)}"
    else:
        return "Unsupported file type"
