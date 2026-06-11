from pathlib import Path
from bs4 import BeautifulSoup
import subprocess
from PyPDF2 import PdfReader
from docx import Document as DocxDocument


# -------------------------
# DOC/DOCX → HTML (LibreOffice)
# -------------------------
def convert_document_to_html(file_path):
    file_path = Path(file_path)
    outdir = file_path.parent

    subprocess.run([
        "libreoffice", "--headless", "--convert-to", "html",
        "--outdir", str(outdir),
        str(file_path)
    ], check=True)

    return outdir / f"{file_path.stem}.html"


# -------------------------
# HTML → TEXT
# -------------------------
def extract_text_from_html(html_path):
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")

    return " ".join(
        soup.get_text(separator=" ", strip=True).split()
    )


# -------------------------
# PDF + DOCX + TXT → TEXT (🔥 FIX ADDED)
# -------------------------
def extract_text_from_file(file_path):
    file_path = str(file_path).lower()

    # ---------------- PDF ----------------
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    # ---------------- DOCX ----------------
    elif file_path.endswith(".docx"):
        doc = DocxDocument(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    # ---------------- DOC (fallback) ----------------
    elif file_path.endswith(".doc"):
        # try LibreOffice conversion
        html_path = convert_document_to_html(file_path)
        return extract_text_from_html(html_path)

    return ""


# -------------------------
# TEXT CHUNKING (your logic fixed slightly)
# -------------------------
def chunk_text(text, chunk_size=1000, overlap=150):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])

        start = end - overlap
        if start < 0:
            start = 0

    return [c for c in chunks if c.strip()]