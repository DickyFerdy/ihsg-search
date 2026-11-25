"""Modul retriever hybrid dengan Reciprocal Rank Fusion (RRF).

Menyediakan algoritma RRF, kelas HybridRetriever, fungsi pencarian terpadu `cari()`,
dan fungsi pemuatan seluruh sistem retrieval `load_system()`.
"""

import os
from functools import partial

import pandas as pd
import psutil

import config
from retrieval.bm25 import BM25Retriever, load_corpus, build_or_load_bm25_index
from retrieval.dense import DenseRetriever, build_or_load_dense_index


def reciprocal_rank_fusion(
    rankings: list[list[tuple[str, float]]],
    k_rrf: int = None,
) -> list[tuple[str, float]]:
    """Menggabungkan beberapa daftar peringkat retrieval menggunakan Reciprocal Rank Fusion (RRF).

    Formula skor dokumen d: skor(d) = sum 1 / (k_rrf + rank), di mana rank dimulai dari 1.
    """
    k_rrf = k_rrf if k_rrf is not None else config.RRF_K
    rrf_scores = {}
    for ranking in rankings:
        for rank, (doc_id, _) in enumerate(ranking, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k_rrf + rank))

    # Urutkan secara menurun berdasarkan skor fusi RRF tertinggi
    sorted_docs = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
    return sorted_docs


class HybridRetriever:
    """Retriever gabungan (hybrid) berbasis Reciprocal Rank Fusion antara BM25 dan Dense."""

    def __init__(
        self,
        bm25_retriever: BM25Retriever,
        dense_retriever: DenseRetriever,
        candidates: int = None,
        k_rrf: int = None,
    ):
        self.bm25_retriever = bm25_retriever
        self.dense_retriever = dense_retriever
        self.candidates = candidates if candidates is not None else config.CANDIDATES
        self.k_rrf = k_rrf if k_rrf is not None else config.RRF_K

    def search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        """Mencari k dokumen teratas dengan mengambil candidates teratas dari BM25 dan Dense,
        lalu menggabungkannya menggunakan RRF.
        """
        bm25_results = self.bm25_retriever.search(query, k=self.candidates)
        dense_results = self.dense_retriever.search(query, k=self.candidates)

        if not bm25_results and not dense_results:
            return []

        fused = reciprocal_rank_fusion([bm25_results, dense_results], k_rrf=self.k_rrf)
        return fused[:k]


def get_process_memory_mb() -> float:
    """Mengembalikan penggunaan memori Resident Set Size (RSS) proses saat ini dalam MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def cari(
    query: str,
    metode: str = "hybrid_rrf",
    k: int = 10,
    bm25_retriever: BM25Retriever = None,
    dense_retriever: DenseRetriever = None,
    hybrid_retriever: HybridRetriever = None,
    corpus_lookup: dict = None,
) -> pd.DataFrame:
    """Mencari artikel berita IHSG berdasarkan kueri dengan metode yang dipilih.

    Pilihan metode:
      - 'bm25': Pencarian leksikal Okapi BM25
      - 'dense': Pencarian semantik Dense FAISS (multilingual-e5-small)
      - 'hybrid_rrf': Penggabungan leksikal dan dense dengan Reciprocal Rank Fusion

    Mengembalikan DataFrame dengan kolom: rank, skor, tanggal, judul, url.
    """
    metode_clean = metode.lower().strip()
    if metode_clean in ["bm25", "lexical"]:
        results = bm25_retriever.search(query, k=k)
    elif metode_clean in ["dense", "semantic"]:
        results = dense_retriever.search(query, k=k)
    elif metode_clean in ["hybrid_rrf", "hybrid", "rrf"]:
        results = hybrid_retriever.search(query, k=k)
    else:
        raise ValueError(f"Metode '{metode}' tidak dikenal. Pilih: 'bm25', 'dense', atau 'hybrid_rrf'.")

    corpus_lookup = corpus_lookup or {}
    rows = []
    for rank, (doc_id, score) in enumerate(results, start=1):
        doc = corpus_lookup.get(doc_id, {})
        rows.append({
            "rank": rank,
            "skor": round(score, 6),
            "tanggal": doc.get("date", "-"),
            "judul": doc.get("title", "-"),
            "url": doc.get("url", "-"),
        })

    return pd.DataFrame(rows, columns=["rank", "skor", "tanggal", "judul", "url"])


def load_system(corpus=None):
    """Memuat seluruh sistem retrieval dan mengukur estimasi konsumsi memori.

    Mengembalikan tuple:
        (corpus, corpus_lookup, bm25_retriever, dense_retriever,
         hybrid_retriever, system_memory, bound_cari)

    Di mana `bound_cari` adalah fungsi `cari()` yang sudah terikat dengan
    retriever dan corpus_lookup yang dimuat.
    """
    print("Memuat sistem retrieval dan mengukur estimasi konsumsi memori...")
    mem_baseline = get_process_memory_mb()

    if corpus is None:
        corpus = load_corpus()
    corpus_lookup = {doc["id"]: doc for doc in corpus}

    bm25_ret = build_or_load_bm25_index(corpus)
    mem_after_bm25 = get_process_memory_mb()
    bm25_mem = max(0.0, mem_after_bm25 - mem_baseline)

    dense_ret = build_or_load_dense_index(corpus)
    mem_after_dense = get_process_memory_mb()
    dense_mem = max(0.0, mem_after_dense - mem_after_bm25)

    hybrid_ret = HybridRetriever(bm25_ret, dense_ret)
    hybrid_mem = bm25_mem + dense_mem

    system_memory = {
        "BM25": bm25_mem,
        "Dense": dense_mem,
        "Hybrid": hybrid_mem,
    }

    print("Pemuatan sistem selesai. Estimasi Memori RSS:")
    print(f"- BM25          : ~{bm25_mem:.1f} MB")
    print(f"- Dense (e5+FAISS): ~{dense_mem:.1f} MB")
    print(f"- Hybrid (Total): ~{hybrid_mem:.1f} MB")

    # Membuat fungsi cari() yang sudah terikat dengan retriever yang dimuat
    bound_cari = partial(
        cari,
        bm25_retriever=bm25_ret,
        dense_retriever=dense_ret,
        hybrid_retriever=hybrid_ret,
        corpus_lookup=corpus_lookup,
    )

    return corpus, corpus_lookup, bm25_ret, dense_ret, hybrid_ret, system_memory, bound_cari
