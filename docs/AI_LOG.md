# AI Log - Pencatatan Penggunaan AI

Dokumen ini mencatat setiap tugas yang dikerjakan dengan bantuan agen AI, berkas yang diubah, serta bagian yang membutuhkan pemeriksaan/tindakan manusia.

---

### [2026-11-22] - Tugas T0: Kerangka Repo dan Notebook
- **Tugas:** Menyiapkan kerangka dasar proyek sesuai panduan `docs/PLAN.md` dan spesifikasi `docs/SPEC.md`.
- **Berkas yang dibuat / diubah:**
  - `requirements.txt`: Daftar pustaka dependensi (`requests`, `beautifulsoup4`, `PySastrawi`, `rank-bm25`, `sentence-transformers`, `torch`, `faiss-cpu`, `numpy`, `pandas`, `scipy`, `ipywidgets`, `psutil`).
  - `.gitignore`: Mengabaikan berkas korpus, data pooling, progres crawling, direktori indeks, `.venv`, serta dokumen kerja agen (`AGENTS.md`, `docs/SPEC.md`, `docs/PLAN.md`).
  - `ihsg_search.ipynb`: Notebook Jupyter awal yang hanya memuat sel markdown judul dan ringkasan tujuan untuk Langkah 1 sampai Langkah 11 sesuai SPEC bagian 6 (tanpa sel kode dan bersih dari output).
  - `docs/AI_LOG.md`: Berkas log awal pencatatan kerja agen.
- **Bagian yang perlu diperiksa manusia:**
  - Pastikan daftar pustaka di `requirements.txt` sesuai dengan lingkungan Python yang akan digunakan (`.venv`).
  - Pastikan berkas `data/queries.csv` dan `tests/fixtures/artikel_contoh.html` disiapkan sebelum melangkah ke tugas berikutnya.
  - Periksa `git status` sebelum melakukan commit mandiri untuk T0.

---

### [2026-11-22] - Tugas T1: Konfigurasi dan Impor
- **Tugas:** Menulis sel Langkah 1 (%pip install) dan sel Langkah 2 (konfigurasi parameter terpusat, impor pustaka, pembuatan direktori) di `ihsg_search.ipynb` sesuai SPEC bagian 5.
- **Berkas yang dibuat / diubah:**
  - `ihsg_search.ipynb`: Menambahkan sel kode Langkah 1 (`%pip install -r requirements.txt`) dan sel kode Langkah 2 memuat semua parameter (seed=42, `CONTACT_EMAIL` kosong, target 2000 dokumen, crawl delay 2.0s, max fetches 8000, parameter BM25, parameter dense e5, parameter hybrid RRF, cutoffs, dan path berkas lengkap) serta pembuatan direktori `data/`, `indexes/`, dan `results/`.
- **Bagian yang perlu diperiksa manusia:**
  - Periksa nilai konfigurasi di sel Langkah 2 notebook.
  - Sebelum menjalankan crawler pada tugas T2, isi `CONTACT_EMAIL` dengan email Anda.
  - Tinjau diff git dan lakukan commit untuk T1.

---

### [2026-11-23] - Tugas T2: Crawler
- **Tugas:** Mengimplementasikan fungsi ekstraksi artikel `extract_article()`, penyaringan aturan situs `is_allowed_url()`, dan fungsi crawler `run_crawler()` pada Langkah 3 `ihsg_search.ipynb` sesuai SPEC 4.1.
- **Berkas yang dibuat / diubah:**
  - `tests/fixtures/artikel_contoh.html`: Fixture pengujian HTML lokal yang merepresentasikan struktur DOM artikel CNBC (dua `div.detail-text` bersarang, tabel 'Baca:', 'Gambas', iklan, JSON-LD `datePublished`, dan dateline).
  - `ihsg_search.ipynb`: Menambahkan sel kode Langkah 3 berisi `extract_article()` dan `run_crawler()`. Sel menolak eksekusi jika `CONTACT_EMAIL` kosong, mendukung penemuan URL BFS berprioritas IHSG, mode reproduksi dari `corpus_urls.txt`, jeda santun `CRAWL_DELAY = 2.0s`, penanganan HTTP 429, serta penyimpanan berkas riwayat URL dan korpus secara idempoten.
- **Bagian yang perlu diperiksa manusia:**
  - Anda dapat mengganti isi `tests/fixtures/artikel_contoh.html` dengan berkas HTML artikel CNBC asli (Ctrl+S dari browser) bila diinginkan untuk verifikasi tambahan.
  - Untuk menjalankan pengumpulan data korpus awal:
    1. Buka sel konfigurasi di Langkah 2, isi `CONTACT_EMAIL` dengan alamat email Anda.
    2. Ubah sementara `TARGET_DOCS = 20` (sesuai aturan AGENTS.md).
    3. Jalankan sel Langkah 3 dan periksa hasil di `data/corpus.jsonl`.
    4. Kembalikan `TARGET_DOCS = 2000` sebelum melanjutkan.
  - Tinjau diff git dan lakukan commit untuk T2.

---

### [2026-11-23] - Tugas T3: Praproses
- **Tugas:** Mengimplementasikan fungsi `preprocess()` pada bagian awal Langkah 4 `ihsg_search.ipynb` sesuai protokol SPEC 4.2.
- **Berkas yang dibuat / diubah:**
  - `ihsg_search.ipynb`: Menambahkan sel kode praproses teks di Langkah 4 yang mencakup huruf kecil, penghapusan URL, tokenisasi regex `[a-z][a-z0-9]*`, kamus normalisasi variasi (`idx->bei`, `dollar/usd->dolar`, `rp->rupiah`), pembersihan token 1 huruf dan stopword (Sastrawi + cnbc, com, www, http, https), serta stemming Sastrawi dengan `lru_cache` (kecuali 10 istilah domain terproteksi: `{ihsg, bei, ojk, bi, msci, ipo, lq45, emiten, asing, ssi}`).
- **Bagian yang perlu diperiksa manusia:**
  - Periksa hasil praproses teks di sel Langkah 4 notebook.
  - Tinjau diff git dan lakukan commit untuk T3.

---

### [2026-11-24] - Tugas T4: BM25 dan Indeks
- **Tugas:** Mengimplementasikan fungsi pemuatan korpus `load_corpus()`, kelas retriever leksikal `BM25Retriever`, dan pembangun indeks `build_or_load_bm25_index()` pada Langkah 4 `ihsg_search.ipynb` sesuai SPEC 4.3.
- **Berkas yang dibuat / diubah:**
  - `ihsg_search.ipynb`: Menambahkan sel BM25 di Langkah 4 yang mengimplementasikan antarmuka seragam `search(query, k) -> list[(docid, skor)]`, penyimpanan `{"ids", "tokens"}` via pickle ke `indexes/bm25_tokens.pkl`, logika idempoten pembangunan/pemuatan indeks, serta membersihkan seluruh output sel notebook sesuai aturan AGENTS.md.
- **Bagian yang perlu diperiksa manusia:**
  - Periksa implementasi BM25 di sel Langkah 4 notebook.
  - Tinjau diff git dan lakukan commit untuk T4.

---

### [2026-11-24] - Tugas T5: Dense dan FAISS
- **Tugas:** Mengimplementasikan kelas `DenseRetriever` dan pembangun indeks `build_or_load_dense_index()` pada Langkah 4 `ihsg_search.ipynb` sesuai SPEC 4.3.
- **Berkas yang dibuat / diubah:**
  - `ihsg_search.ipynb`: Menambahkan sel kode Dense di Langkah 4 yang menggunakan model `intfloat/multilingual-e5-small`, menerapkan konvensi awalan `passage: ` untuk dokumen dan `query: ` untuk kueri, embedding ternormalisasi L2, indeks FAISS `IndexFlatIP` (Cosine Similarity) yang disimpan ke `indexes/faiss.index`, pemetaan ID ke `indexes/dense_ids.json` tanpa duplikasi vektor embedding, serta mekanisme idempoten (melewati encode ulang jika indeks sudah cocok dengan korpus).
- **Bagian yang perlu diperiksa manusia:**
  - Periksa implementasi Dense retriever di sel Langkah 4 notebook.
  - Sesuai PLAN.md, model `intfloat/multilingual-e5-small` membutuhkan unduhan bobot model saat pertama kali dijalankan di kernel oleh manusia.
  - Tinjau diff git dan lakukan commit untuk T5.

---

### [2026-11-24] - Tugas T6: Hybrid RRF dan Pemuatan Sistem
- **Tugas:** Mengimplementasikan algoritma Reciprocal Rank Fusion `reciprocal_rank_fusion()`, kelas retriever gabungan `HybridRetriever`, fungsi pengukuran memori RSS `get_process_memory_mb()`, serta sel pemuatan ketiga sistem (BM25, Dense, Hybrid) pada Langkah 5 `ihsg_search.ipynb` sesuai SPEC 4.3 dan 4.7.
- **Berkas yang dibuat / diubah:**
  - `ihsg_search.ipynb`: Menambahkan sel kode Langkah 5 yang mengintegrasikan BM25 dan Dense menggunakan RRF ($k=60$, 100 kandidat per retriever), antarmuka `search(query, k)`, serta estimasi memori proses menggunakan `psutil` secara lintas platform.
- **Bagian yang perlu diperiksa manusia:**
  - Periksa implementasi RRF dan pemuatan sistem di Langkah 5 notebook.
  - Tinjau diff git dan lakukan commit untuk T6.

---

### [2026-11-24] - Tugas T8: Pooling (Langkah 6)
- **Tugas:** Mengimplementasikan fungsi `generate_pool()` pada Langkah 6 `ihsg_search.ipynb` sesuai protokol SPEC 4.4.
- **Berkas yang dibuat / diubah:**
  - `ihsg_search.ipynb`: Menambahkan sel kode Langkah 6 yang mengambil top-10 kandidat dokumen dari BM25, Dense, dan Hybrid, menggabungkannya secara unik (union) per kueri, mengacak urutannya dengan seed acak agar penilai netral dari bias sistem, dan mengekspornya ke `data/pool_to_label.csv` dengan kolom `rel` yang dibiarkan kosong untuk penilaian manual manusia (mematuhi Aturan 1 AGENTS.md), serta mekanisme proteksi agar tidak menimpa pool atau qrels yang sudah ada.
- **Bagian yang perlu diperiksa manusia:**
  - Siapkan berkas `data/queries.csv` (berisi 25 kueri uji dengan header `qid,query`).
  - Setelah `queries.csv` tersedia, jalankan sel Langkah 6 di notebook untuk menghasilkan `data/pool_to_label.csv`.
  - Tinjau diff git dan lakukan commit untuk T8.

---

### [2026-11-25] - Tugas T9: Pelabelan Manual & Pembaca Qrels (Langkah 7)
- **Tugas:** Mengimplementasikan fungsi pembaca CSV andal `read_csv_robust()` dan pemuat ground truth `load_qrels()` pada Langkah 7 `ihsg_search.ipynb` sesuai SPEC 4.5.
- **Berkas yang dibuat / diubah:**
  - `ihsg_search.ipynb`: Menambahkan sel kode Langkah 7 yang menangani anomali ekspor ulang berkas CSV dari Microsoft Excel (seperti baris terbungkus tanda kutip ganda atau delimiter titik koma), memuat relevance judgements dari `data/pool_to_label.csv`, otomatis menyinkronkan ke `data/qrels.csv` saat label tersedia, dan memberikan peringatan informatif bila penilaian manusia belum selesai tanpa melempar error tak terduga.
- **Bagian yang perlu diperiksa manusia:**
  - Kolom `rel` pada `data/pool_to_label.csv` wajib diisi manual oleh manusia (skala: `0` = tidak relevan, `1` = relevan sebagian, `2` = sangat relevan) sesuai kriteria SPEC 4.5. Agen sama sekali tidak mengisi kolom ini demi menjaga integritas ilmiah (Aturan 1 AGENTS.md).
  - Setelah penilaian relevansi selesai diisi, jalankan sel Langkah 7 di notebook untuk menghasilkan `data/qrels.csv`.
  - Tinjau diff git dan lakukan commit untuk T9.

---

### [2026-11-25] - Penyesuaian Spesifikasi Antarmuka: Adopsi Streamlit
- **Tugas:** Menyesuaikan seluruh dokumentasi spesifikasi (`docs/SPEC.md`, `docs/PLAN.md`, `AGENTS.md`, `requirements.txt`, dan Langkah 11 `ihsg_search.ipynb`) untuk menggunakan antarmuka web interaktif berbasis **Streamlit** (`app.py`) menggantikan `ipywidgets` sesuai permintaan pengguna.
- **Berkas yang dibuat / diubah:**
  - `docs/SPEC.md`: Memperbarui tabel keputusan desain, struktur berkas (menambahkan `app.py`), spesifikasi UI bagian 4.9 menjadi web app Streamlit, dan daftar langkah notebook Langkah 11.
  - `docs/PLAN.md`: Menyesuaikan tugas T7 pada tabel dan rincian kerja untuk mencakup pembuatan antarmuka web Streamlit `app.py`.
  - `AGENTS.md`: Menambahkan pengecualian resmi pada bagian hasil akhir untuk menyertakan modul web `app.py`.
  - `requirements.txt`: Menambahkan pustaka `streamlit>=1.28.0`.
  - `ihsg_search.ipynb`: Memperbarui sel judul Langkah 11 menjadi antarmuka web Streamlit.
- **Bagian yang perlu diperiksa manusia:**
  - Periksa perubahan pada `docs/SPEC.md` dan `requirements.txt`.
  - Lakukan commit git untuk perubahan dependensi dan dokumentasi ini.


---

### [2026-11-25] - Modularisasi Notebook ke Paket Python Terstruktur
- **Tugas:** Memecah sel-sel kode panjang pada `ihsg_search.ipynb` (Langkah 1 sampai Langkah 7, termasuk pembaruan UI `ipywidgets` pada sel Langkah 1 dan sel Langkah 3 yang sebelumnya belum tercatat) menjadi modul-modul Python terkelompok sesuai fungsinya, dan menjadikan `ihsg_search.ipynb` sebagai notebook orchestrator tipis.
- **Berkas yang dibuat / diubah:**
  - `config.py`: Konstanta terpusat, seed (`SEED=42`), parameter crawler, BM25, Dense, RRF, serta path direktori dan berkas.
  - `setup/__init__.py` & `setup/install.py`: Antarmuka instalasi dependensi `requirements.txt` berbasis `ipywidgets` (`show_install_ui()`) dengan progress bar dan pemantauan status pip.
  - `crawler/__init__.py`, `crawler/extractor.py`, `crawler/crawler.py`, & `crawler/ui.py`: Memisahkan validasi URL & ekstraksi artikel (`is_allowed_url()`, `extract_article()`), logika inti crawler (`run_crawler()`), serta launcher UI interaktif (`show_crawler_launcher()`, `_build_crawler_monitor()`).
  - `preprocess/__init__.py` & `preprocess/text.py`: Pipeline praproses teks bahasa Indonesia (`preprocess()`, `cached_stem()`, `STOPWORDS`, `NORMALIZATION_MAP`, `PROTECTED_TERMS`).
  - `retrieval/__init__.py`, `retrieval/bm25.py`, `retrieval/dense.py`, & `retrieval/hybrid.py`: Pemuatan korpus (`load_corpus()`), retriever BM25 (`BM25Retriever`, `build_or_load_bm25_index()`), retriever Dense FAISS (`DenseRetriever`, `build_or_load_dense_index()`), serta Hybrid RRF (`reciprocal_rank_fusion()`, `HybridRetriever`, `get_process_memory_mb()`, `cari()`, `load_system()`).
  - `evaluation/__init__.py`, `evaluation/pooling.py`, & `evaluation/qrels.py`: Pembuatan pool (`generate_pool()`) dan pembaca CSV/qrels andal (`read_csv_robust()`, `load_qrels()`).
  - `ihsg_search.ipynb`: Diringkas menjadi notebook orchestrator di mana setiap sel kode hanya mengimpor dan memanggil fungsi dari modul terkait.
- **Bagian yang perlu diperiksa manusia:**
  - Jalankan sel Langkah 2 sampai Langkah 7 secara berurutan di kernel notebook untuk memastikan seluruh impor modul dan alur eksekusi berjalan sesuai harapan.
  - Periksa `git status` dan lakukan commit untuk struktur modular baru ini.
