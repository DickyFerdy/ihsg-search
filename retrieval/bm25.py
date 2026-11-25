"""Modul retriever leksikal BM25 Okapi dan pemuat korpus.

Menyediakan fungsi pemuatan korpus dari JSONL serta kelas BM25Retriever
dengan antarmuka pencarian terstandarisasi search(query, k).
"""

import json
import pickle

from rank_bm25 import BM25Okapi

import config
from preprocess.text import preprocess


def load_corpus(corpus_path=None) -> list[dict]:
    """Memuat dokumen korpus dari berkas corpus.jsonl.

    Mengembalikan daftar objek dokumen [id, title, date, text, url].
    """
    corpus_path = corpus_path or config.PATH_CORPUS
    if not corpus_path.exists():
        print(f"Peringatan: Berkas korpus {corpus_path} belum ditemukan.")
        return []
    docs = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
    print(f"Berhasil memuat {len(docs)} dokumen dari {corpus_path}.")
    return docs


class BM25Retriever:
    """Retriever leksikal berbasis BM25 Okapi dengan antarmuka pencarian terstandarisasi."""

    def __init__(self, doc_ids: list[str], corpus_tokens: list[list[str]],
                 k1: float = None, b: float = None):
        self.doc_ids = doc_ids
        self.corpus_tokens = corpus_tokens
        self.k1 = k1 if k1 is not None else config.BM25_K1
        self.b = b if b is not None else config.BM25_B
        self.bm25 = BM25Okapi(corpus_tokens, k1=self.k1, b=self.b) if corpus_tokens else None

    def search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        """Mencari k dokumen teratas berdasarkan kueri menggunakan skor BM25 Okapi.

        Mengembalikan list pasangan (docid, skor).
        Hanya dokumen dengan skor lebih dari 0 yang dikembalikan.
        """
        if not self.bm25 or not self.doc_ids:
            return []

        query_tokens = preprocess(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Ambil hanya dokumen dengan skor positif
        positive_indices = [i for i, score in enumerate(scores) if score > 0]
        if not positive_indices:
            return []

        # Urutkan berdasarkan skor tertinggi (descending)
        positive_indices.sort(key=lambda i: scores[i], reverse=True)
        top_indices = positive_indices[:k]

        return [(self.doc_ids[i], float(scores[i])) for i in top_indices]


def build_or_load_bm25_index(corpus: list[dict], index_path=None) -> BM25Retriever:
    """Membangun indeks BM25 jika belum ada atau memuat dari berkas token pickle secara idempoten."""
    index_path = index_path or config.PATH_BM25_TOKENS
    if not corpus:
        print("Korpus kosong. Indeks BM25 tidak dibangun.")
        return BM25Retriever([], [])

    corpus_ids = [doc["id"] for doc in corpus]

    # Cek apakah berkas indeks sudah ada dan sesuai dengan korpus saat ini
    if index_path.exists():
        try:
            with open(index_path, "rb") as f:
                saved_data = pickle.load(f)
            if saved_data.get("ids") == corpus_ids:
                print(f"Memuat indeks BM25 yang sudah ada dari {index_path} ({len(corpus_ids)} dokumen).")
                return BM25Retriever(saved_data["ids"], saved_data["tokens"])
            else:
                print("Daftar dokumen korpus berubah. Membangun ulang indeks BM25...")
        except Exception as e:
            print(f"Gagal memuat {index_path} ({e}). Membangun ulang indeks...")

    print(f"Melakukan praproses dan pembuatan indeks BM25 untuk {len(corpus)} dokumen...")
    # Teks yang diindeks: judul + ". " + isi
    corpus_tokens = [preprocess(doc["title"] + ". " + doc["text"]) for doc in corpus]

    # Simpan {"ids", "tokens"} dengan pickle
    with open(index_path, "wb") as f:
        pickle.dump({"ids": corpus_ids, "tokens": corpus_tokens}, f)

    print(f"Indeks BM25 berhasil disimpan ke {index_path}.")
    return BM25Retriever(corpus_ids, corpus_tokens)
