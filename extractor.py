import requests
from trafilatura import extract
from pypdf import PdfReader
import tempfile, os

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AI-Agent/1.0)"}

def extract_content(url: str, timeout: int = 12) -> str:
    # fetch
    resp = requests.get(url, timeout=timeout, headers=HEADERS)
    content_type = (resp.headers.get('Content-Type') or '').lower()

    # PDF
    if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name
        try:
            reader = PdfReader(tmp_path)
            text_parts = []
            for p in reader.pages:
                t = p.extract_text()
                if t:
                    text_parts.append(t)
            return "\n\n".join(text_parts).strip()
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass

    # otherwise assume HTML
    html = resp.text
    text = extract(html, url=url)  # trafilatura.extract
    return text or ""
