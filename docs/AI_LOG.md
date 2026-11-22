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
