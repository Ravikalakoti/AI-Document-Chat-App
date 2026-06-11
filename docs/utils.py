from pathlib import Path
from bs4 import BeautifulSoup
from django.conf import settings
import subprocess

def convert_document_to_html(file_path):
    file_path = Path(file_path)
    outdir = file_path.parent
    subprocess.run([
        "libreoffice", "--headless", "--convert-to", "html",
        "--outdir", str(outdir),
        str(file_path)
    ], check=True)

    return outdir / f"{file_path.stem}.html"

def extract_text_from_html(html_path):
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")
    return " ".join(soup.get_text(separator=" ", strip=True).split())

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