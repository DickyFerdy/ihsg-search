"""Konfigurasi terpusat dan konstanta untuk proyek Mini Search Engine IHSG."""

import random
from pathlib import Path

import numpy as np

# Menetapkan seed acak demi reprodusibilitas eksperimen
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Konfigurasi crawler
CONTACT_EMAIL = "dickyferdy5@gmail.com"
TARGET_DOCS = 2000
CRAWL_DELAY = 2.0
MAX_FETCHES = 8000

# Konfigurasi retriever leksikal (BM25 Okapi)
BM25_K1 = 1.5
BM25_B = 0.75

# Konfigurasi retriever dense (multilingual-e5-small)
EMBED_MODEL = "intfloat/multilingual-e5-small"
EMBED_MAX_LEN = 256
EMBED_BATCH = 64

# Konfigurasi hybrid fusion & kedalaman evaluasi
RRF_K = 60
CANDIDATES = 100
POOL_DEPTH = 10
EVAL_K = 10

# Jalur direktori dan berkas (relatif terhadap direktori kerja notebook)
PATH_DATA_DIR = Path("data")
PATH_INDEXES_DIR = Path("indexes")
PATH_RESULTS_DIR = Path("results")

PATH_QUERIES = PATH_DATA_DIR / "queries.csv"
PATH_CORPUS = PATH_DATA_DIR / "corpus.jsonl"
PATH_CORPUS_URLS = PATH_DATA_DIR / "corpus_urls.txt"
PATH_POOL_TO_LABEL = PATH_DATA_DIR / "pool_to_label.csv"
PATH_QRELS = PATH_DATA_DIR / "qrels.csv"
PATH_VISITED_URLS = PATH_DATA_DIR / "visited_urls.txt"
PATH_KNOWN_URLS = PATH_DATA_DIR / "known_urls.txt"

PATH_BM25_TOKENS = PATH_INDEXES_DIR / "bm25_tokens.pkl"
PATH_FAISS_INDEX = PATH_INDEXES_DIR / "faiss.index"
PATH_DENSE_IDS = PATH_INDEXES_DIR / "dense_ids.json"

PATH_PER_QUERY = PATH_RESULTS_DIR / "per_query.csv"
PATH_SUMMARY = PATH_RESULTS_DIR / "summary.csv"
PATH_SIGNIFICANCE = PATH_RESULTS_DIR / "significance.csv"
PATH_ERROR_ANALYSIS = PATH_RESULTS_DIR / "error_analysis.csv"

# Memastikan seluruh direktori output tersedia
for _dir in [PATH_DATA_DIR, PATH_INDEXES_DIR, PATH_RESULTS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

print("Konfigurasi dan pustaka berhasil dimuat. Direktori siap.")
