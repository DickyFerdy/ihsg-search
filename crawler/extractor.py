"""Modul ekstraksi artikel berita CNBC Indonesia.

Berisi fungsi validasi URL dan ekstraksi konten artikel dari HTML.
"""

import hashlib
import json
import re
import urllib.parse

from bs4 import BeautifulSoup

ARTICLE_URL_PATTERN = re.compile(r"^https://www\.cnbcindonesia\.com/market/\d{14}-\d+-\d+/[^/?#]+$")
DISALLOWED_SUBSTRINGS = ["?", "/embed", "/logout", "/search", "/api", "/partner", "/indeks/"]


def is_allowed_url(url: str) -> bool:
    """Memeriksa apakah URL mematuhi aturan konservatif robots.txt CNBC."""
    parsed = urllib.parse.urlparse(url)
    full_path_query = parsed.path + ("?" + parsed.query if parsed.query else "")
    for disallowed in DISALLOWED_SUBSTRINGS:
        if disallowed in full_path_query:
            return False
    return True


def extract_article(html_content: str, url: str, min_text_len: int = 300, require_ihsg: bool = True) -> dict | None:
    """Mengekstrak judul, tanggal publikasi, dan isi berita dari HTML artikel CNBC Indonesia."""
    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Judul dari <meta property="og:title"> dengan fallback ke <title>
    og_title = soup.find("meta", property="og:title")
    title = og_title.get("content", "").strip() if og_title else ""
    if not title:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

    # 2. Tanggal publikasi dari JSON-LD datePublished
    date_published = ""
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    if "datePublished" in item:
                        date_published = item["datePublished"]
                        break
                    for sub in item.get("@graph", []):
                        if isinstance(sub, dict) and "datePublished" in sub:
                            date_published = sub["datePublished"]
                            break
            if date_published:
                break
        except (json.JSONDecodeError, AttributeError):
            continue

    # 3. Ekstraksi teks isi dari div.detail-text terdalam
    detail_divs = soup.find_all("div", class_="detail-text")
    if not detail_divs:
        return None
    inner_detail = detail_divs[-1]

    paragraphs = []
    for p in inner_detail.find_all("p"):
        p_text = p.get_text(strip=True)
        if len(p_text) <= 30:
            continue
        if p_text.startswith("Baca:") or p_text.startswith("Foto:") or "Gambas:" in p_text:
            continue
        paragraphs.append(p_text)

    full_text = " ".join(paragraphs)

    # Menghapus awalan dateline 'Jakarta, CNBC Indonesia -'
    full_text = re.sub(r"^(?:Jakarta,\s*)?CNBC\s+Indonesia\s*[-\u2013\u2014]\s*", "", full_text, flags=re.IGNORECASE)
    full_text = re.sub(r"\s+", " ", full_text).strip()

    # Filter dokumen: > min_text_len karakter dan (opsional) memuat 'ihsg'
    text_lower = full_text.lower()
    if len(full_text) <= min_text_len:
        return None
    if require_ihsg and "ihsg" not in text_lower and "indeks harga saham gabungan" not in text_lower:
        return None

    doc_id = "d" + hashlib.md5(url.encode("utf-8")).hexdigest()[:10]
    return {
        "id": doc_id,
        "title": title,
        "date": date_published,
        "text": full_text,
        "url": url,
    }
