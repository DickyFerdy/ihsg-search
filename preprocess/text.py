"""Modul praproses teks bahasa Indonesia untuk sistem retrieval IHSG.

Pipeline praproses (SPEC 4.2):
1. Huruf kecil (case folding)
2. Menghapus tautan URL
3. Tokenisasi [a-z][a-z0-9]* (hanya token diawali huruf a-z)
4. Normalisasi istilah (idx->bei, dollar/usd->dolar, rp->rupiah)
5. Membuang token 1 huruf dan stopword
6. Stemming Sastrawi dengan lru_cache (kecuali istilah domain terproteksi)
"""

import re
from functools import lru_cache

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Stopword standar Sastrawi ditambah istilah web umum
_stopword_factory = StopWordRemoverFactory()
STOPWORDS = set(_stopword_factory.get_stop_words()) | {"cnbc", "com", "www", "http", "https"}

# Kamus normalisasi variasi istilah pasar modal dan mata uang
NORMALIZATION_MAP = {
    "idx": "bei",
    "dollar": "dolar",
    "usd": "dolar",
    "rp": "rupiah",
}

# Istilah domain yang dilindungi dari pemotongan imbuhan (stemming)
PROTECTED_TERMS = {
    "ihsg", "bei", "ojk", "bi", "msci", "ipo", "lq45", "emiten", "asing", "ssi"
}

_stemmer_factory = StemmerFactory()
_stemmer = _stemmer_factory.create_stemmer()


@lru_cache(maxsize=50000)
def cached_stem(word: str) -> str:
    """Melakukan stemming kata bahasa Indonesia dengan cache LRU untuk kecepatan."""
    return _stemmer.stem(word)


def preprocess(text: str) -> list[str]:
    """Melakukan praproses teks sesuai ketentuan SPEC 4.2.

    1. Huruf kecil (case folding)
    2. Menghapus tautan URL
    3. Tokenisasi [a-z][a-z0-9]* (hanya token diawali huruf a-z)
    4. Normalisasi istilah (idx->bei, dollar/usd->dolar, rp->rupiah)
    5. Membuang token 1 huruf dan stopword
    6. Stemming Sastrawi dengan lru_cache (kecuali istilah domain terproteksi)
    """
    if not text:
        return []

    text_lower = text.lower()
    text_no_url = re.sub(r"https?://\S+|www\.\S+", " ", text_lower)
    raw_tokens = re.findall(r"[a-z][a-z0-9]*", text_no_url)

    processed_tokens = []
    for token in raw_tokens:
        norm_token = NORMALIZATION_MAP.get(token, token)
        if len(norm_token) <= 1 or norm_token in STOPWORDS:
            continue

        if norm_token in PROTECTED_TERMS:
            stemmed = norm_token
        else:
            stemmed = cached_stem(norm_token)

        if len(stemmed) > 1 and stemmed not in STOPWORDS:
            processed_tokens.append(stemmed)

    return processed_tokens
