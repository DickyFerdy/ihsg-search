"""Modul pembaca CSV andal dan pemuat ground truth relevance judgements (qrels).

Menangani anomali berkas CSV yang disimpan ulang oleh Microsoft Excel
(baris terbungkus tanda kutip, delimiter titik koma, encoding BOM).
"""

import csv
import io
from pathlib import Path

import config


def read_csv_robust(filepath) -> list[dict]:
    """Membaca berkas CSV secara andal, menangani kasus file yang disimpan ulang oleh Excel
    di mana seluruh baris terbungkus tanda kutip ganda atau menggunakan delimiter lokal (;).
    """
    path = Path(filepath)
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        lines = f.readlines()

    if not lines:
        return []

    # Memperbaiki anomali simpan ulang Excel (baris terbungkus tanda kutip luar)
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('"') and stripped.endswith('"') and stripped.count('","') == 0 and stripped.count('";"') == 0:
            inner = stripped[1:-1].replace('""', '"')
            cleaned_lines.append(inner + "\n")
        else:
            cleaned_lines.append(line)

    content = "".join(cleaned_lines)

    # Deteksi delimiter (koma atau titik koma)
    first_line = cleaned_lines[0] if cleaned_lines else ""
    delimiter = ";" if ";" in first_line and "," not in first_line else ","

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

    # Fallback jika delimiter terlewat pada baris pertama
    if reader.fieldnames and len(reader.fieldnames) == 1 and ";" in reader.fieldnames[0]:
        reader = csv.DictReader(io.StringIO(content), delimiter=";")

    rows = []
    for r in reader:
        clean_row = {k.strip(): (v.strip() if v else "") for k, v in r.items() if k is not None}
        rows.append(clean_row)
    return rows


def load_qrels(pool_path=None, qrels_path=None) -> dict[str, dict[str, int]] | None:
    """Memuat ground truth relevance judgements (qrels).

    Urutan pemuatan sesuai SPEC 4.5:
    1. Dari pool_to_label.csv jika sudah memiliki baris berlabel (kolom 'rel' terisi 0, 1, 2).
       Otomatis menyinkronkan label tersebut ke data/qrels.csv.
    2. Dari data/qrels.csv jika pool_to_label.csv belum berlabel.
    3. Jika keduanya belum memiliki label, mengembalikan None.

    Format luaran: dict dengan struktur {qid: {docid: int(rel)}}.
    """
    pool_path = pool_path or config.PATH_POOL_TO_LABEL
    qrels_path = qrels_path or config.PATH_QRELS

    # 1. Cek dari pool_to_label.csv
    if Path(pool_path).exists():
        rows = read_csv_robust(pool_path)
        valid_judgements = []
        for r in rows:
            rel_str = r.get("rel", "").strip()
            if rel_str in ["0", "1", "2"] and "qid" in r and "docid" in r:
                valid_judgements.append((r["qid"], r["docid"], int(rel_str)))

        if valid_judgements:
            qrels = {}
            for qid, docid, rel in valid_judgements:
                if qid not in qrels:
                    qrels[qid] = {}
                qrels[qid][docid] = rel

            # Simpan atau perbarui data/qrels.csv
            with open(qrels_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["qid", "docid", "rel"])
                for qid, doc_dict in qrels.items():
                    for docid, rel in doc_dict.items():
                        writer.writerow([qid, docid, rel])

            print(f"Berhasil memuat {len(valid_judgements)} relevance judgements dari {pool_path}.")
            print(f"Berkas ground truth disinkronkan ke {qrels_path}.")
            return qrels

    # 2. Cek dari qrels.csv jika pool belum berlabel
    if Path(qrels_path).exists():
        rows = read_csv_robust(qrels_path)
        qrels = {}
        count = 0
        for r in rows:
            rel_str = r.get("rel", "").strip()
            if rel_str in ["0", "1", "2"] and "qid" in r and "docid" in r:
                qid = r["qid"]
                docid = r["docid"]
                if qid not in qrels:
                    qrels[qid] = {}
                qrels[qid][docid] = int(rel_str)
                count += 1
        if count > 0:
            print(f"Berhasil memuat {count} relevance judgements dari {qrels_path}.")
            return qrels

    print("Perhatian: Relevance judgements belum tersedia.")
    print(f"Silakan isi kolom 'rel' pada {pool_path} (skala: 0=tidak relevan, 1=relevan sebagian, 2=sangat relevan).")
    return None
