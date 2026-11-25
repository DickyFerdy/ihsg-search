"""Modul pooling kandidat dokumen untuk penilaian relevansi manual.

Mengambil top-k dokumen dari BM25, Dense, dan Hybrid per kueri uji,
menggabungkan secara unik, dan mengekspornya ke pool_to_label.csv.
"""

import csv
import hashlib
import random

import config
from retrieval.bm25 import load_corpus


def generate_pool(
    bm25_retriever,
    dense_retriever,
    hybrid_retriever,
    corpus_lookup=None,
    queries_path=None,
    pool_path=None,
    qrels_path=None,
    pool_depth=None,
    seed=None,
):
    """Menghasilkan berkas pooling kandidat dokumen untuk penilaian relevansi manual manusia.

    Protokol SPEC 4.4:
    - Lewati langkah ini jika pool_to_label.csv atau qrels.csv sudah ada.
    - Ambil top-10 dokumen dari BM25, Dense, dan Hybrid per kueri.
    - Gabungkan secara unik (union) per kueri.
    - Urutkan lalu acak dengan seed agar penilai tidak mengetahui asal sistem.
    - Tulis ke pool_to_label.csv dengan kolom: qid, query, docid, title, url, snippet, rel.
    - Kolom 'rel' WAJIB KOSONG (penilaian manual manusia).
    """
    queries_path = queries_path or config.PATH_QUERIES
    pool_path = pool_path or config.PATH_POOL_TO_LABEL
    qrels_path = qrels_path or config.PATH_QRELS
    pool_depth = pool_depth if pool_depth is not None else config.POOL_DEPTH
    seed = seed if seed is not None else config.SEED

    if qrels_path.exists():
        print(f"Berkas ground truth {qrels_path} sudah ada. Proses pooling dilewati demi melindungi label.")
        return

    if pool_path.exists():
        print(f"Berkas pooling {pool_path} sudah ada. Proses pooling dilewati demi melindungi label manual.")
        return

    if not queries_path.exists():
        print(f"Peringatan: Berkas kueri {queries_path} belum ditemukan.")
        print("Sediakan berkas data/queries.csv (format: qid,query) sebelum menjalankan pooling.")
        return

    # Memuat corpus_lookup jika tidak disediakan
    if corpus_lookup is None:
        corpus_lookup = {d["id"]: d for d in load_corpus()}

    # 1. Baca daftar kueri uji
    queries = []
    with open(queries_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "qid" in row and "query" in row:
                queries.append((row["qid"].strip(), row["query"].strip()))
            elif len(row) >= 2:
                vals = list(row.values())
                queries.append((vals[0].strip(), vals[1].strip()))

    if not queries:
        print("Berkas kueri kosong. Pooling tidak dijalankan.")
        return

    print(f"Memproses pooling untuk {len(queries)} kueri uji (pool_depth={pool_depth})...")

    pool_rows = []

    for qid, query_str in queries:
        # Ambil top kandidat dari tiap retriever
        bm25_res = bm25_retriever.search(query_str, k=pool_depth)
        dense_res = dense_retriever.search(query_str, k=pool_depth)
        hybrid_res = hybrid_retriever.search(query_str, k=pool_depth)

        # Gabungkan docid unik (union)
        retrieved_docids = set()
        for doc_id, _ in bm25_res + dense_res + hybrid_res:
            retrieved_docids.add(doc_id)

        # Urutkan deterministik lalu acak dengan seed
        docid_list = sorted(retrieved_docids)
        qid_hash = int(hashlib.md5(qid.encode("utf-8")).hexdigest()[:6], 16)
        rnd = random.Random(seed + qid_hash)
        rnd.shuffle(docid_list)

        for doc_id in docid_list:
            doc = corpus_lookup.get(doc_id, {})
            title = doc.get("title", "")
            url = doc.get("url", "")
            text = doc.get("text", "")
            snippet = text[:400] if text else ""

            pool_rows.append({
                "qid": qid,
                "query": query_str,
                "docid": doc_id,
                "title": title,
                "url": url,
                "snippet": snippet,
                "rel": "",  # WAJIB KOSONG untuk penilaian manual manusia
            })

    # Tulis berkas pool_to_label.csv
    with open(pool_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["qid", "query", "docid", "title", "url", "snippet", "rel"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pool_rows)

    print(f"Berhasil menghasilkan {len(pool_rows)} pasangan kueri-dokumen di {pool_path}.")
    print("Kolom 'rel' telah disiapkan kosong untuk penilaian relevansi manual manusia.")
