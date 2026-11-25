"""Modul retriever dense berbasis model multilingual-e5-small dan indeks FAISS.

Menyediakan kelas DenseRetriever dengan pencarian semantik menggunakan
cosine similarity pada vektor embedding ternormalisasi.
"""

import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import config


class DenseRetriever:
    """Retriever dense berbasis model multilingual-e5-small dan indeks FAISS IndexFlatIP."""

    def __init__(self, doc_ids: list[str], index: faiss.Index,
                 model_name: str = None):
        self.doc_ids = doc_ids
        self.index = index
        self.model_name = model_name or config.EMBED_MODEL
        self._model = None

    @property
    def model(self):
        """Memuat model SentenceTransformer secara lazy."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
            self._model.max_seq_length = config.EMBED_MAX_LEN
        return self._model

    def search(self, query: str, k: int = 10) -> list[tuple[str, float]]:
        """Mencari k dokumen teratas berdasarkan kueri menggunakan Cosine Similarity dari FAISS.

        Sesuai konvensi model e5, kueri diberi awalan 'query: '.
        """
        if not self.index or self.index.ntotal == 0 or not self.doc_ids:
            return []

        query_clean = query.strip()
        if not query_clean:
            return []

        # Konvensi e5: kueri wajib diawali 'query: '
        query_text = "query: " + query_clean
        query_emb = self.model.encode(
            [query_text],
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype(np.float32)

        # Pencarian pada indeks FAISS (Inner Product pada vektor normal = Cosine Sim)
        top_k = min(k, self.index.ntotal)
        scores, indices = self.index.search(query_emb, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(self.doc_ids):
                results.append((self.doc_ids[idx], float(score)))
        return results


def build_or_load_dense_index(
    corpus: list[dict],
    index_path=None,
    ids_path=None,
    model_name=None,
    model_instance=None,
) -> DenseRetriever:
    """Membangun indeks dense FAISS jika belum ada atau memuat dari disk secara idempoten."""
    index_path = index_path or config.PATH_FAISS_INDEX
    ids_path = ids_path or config.PATH_DENSE_IDS
    model_name = model_name or config.EMBED_MODEL

    if not corpus:
        print("Korpus kosong. Indeks Dense tidak dibangun.")
        return DenseRetriever([], None, model_name=model_name)

    corpus_ids = [doc["id"] for doc in corpus]

    # Cek apakah berkas indeks dan mapping ID sudah ada dan cocok
    if index_path.exists() and ids_path.exists():
        try:
            with open(ids_path, "r", encoding="utf-8") as f:
                saved_ids = json.load(f)
            if saved_ids == corpus_ids:
                print(f"Memuat indeks FAISS yang sudah ada dari {index_path} ({len(corpus_ids)} dokumen).")
                index = faiss.read_index(str(index_path))
                retriever = DenseRetriever(saved_ids, index, model_name=model_name)
                if model_instance:
                    retriever._model = model_instance
                return retriever
            else:
                print("Daftar dokumen korpus berubah. Membangun ulang indeks Dense...")
        except Exception as e:
            print(f"Gagal memuat indeks dense ({e}). Membangun ulang...")

    print(f"Memuat model {model_name} untuk embedding {len(corpus)} dokumen...")
    model = model_instance if model_instance else SentenceTransformer(model_name)
    model.max_seq_length = config.EMBED_MAX_LEN

    # Konvensi e5: dokumen diberi awalan 'passage: '
    # Teks yang diindeks: judul + ". " + isi
    passages = ["passage: " + doc["title"] + ". " + doc["text"] for doc in corpus]

    print(f"Melakukan embedding {len(passages)} teks (batch_size={config.EMBED_BATCH})...")
    embeddings = model.encode(
        passages,
        batch_size=config.EMBED_BATCH,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype(np.float32)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Simpan indeks FAISS dan daftar ID
    faiss.write_index(index, str(index_path))
    with open(ids_path, "w", encoding="utf-8") as f:
        json.dump(corpus_ids, f, ensure_ascii=False)

    print(f"Indeks FAISS ({index.ntotal} vektor) berhasil disimpan ke {index_path}.")
    retriever = DenseRetriever(corpus_ids, index, model_name=model_name)
    retriever._model = model
    return retriever
