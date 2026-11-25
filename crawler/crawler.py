"""Modul inti crawler berita CNBC Indonesia.

Menjalankan crawling terfokus, etis, dan idempoten terhadap situs CNBC Indonesia
untuk mengumpulkan artikel berita pasar modal/IHSG.
"""

import json
import time
import urllib.parse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

import config
from crawler.extractor import ARTICLE_URL_PATTERN, is_allowed_url, extract_article


def _count_existing_corpus() -> int:
    """Menghitung jumlah artikel yang saat ini tersimpan di PATH_CORPUS."""
    if not config.PATH_CORPUS.exists():
        return 0
    with open(config.PATH_CORPUS, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _create_default_ui(target_docs: int):
    """Membuat UI monitor: widget ipywidgets jika tersedia, fallback ke print."""
    try:
        from crawler.ui import _build_crawler_monitor
        from IPython.display import display
        monitor_box, update_fn = _build_crawler_monitor(target_docs)
        display(monitor_box)
        return update_fn
    except Exception:
        def _print_update(status_msg, detail_msg="", saved=None, bar_style=None, new_max=None):
            print(status_msg)
            if detail_msg:
                print(f"  {detail_msg}")
        return _print_update


def run_crawler(
    target_docs=None,
    crawl_delay=None,
    max_fetches=None,
    contact_email=None,
    use_corpus_urls=True,
    request_timeout=10,
    max_consecutive_errors=8,
    min_text_len=300,
    require_ihsg=True,
    session=None,
    ui_updater=None,
):
    """Menjalankan crawling berita CNBC secara terfokus, etis, dan idempoten."""
    target_docs = int(config.TARGET_DOCS if target_docs is None else target_docs)
    crawl_delay = float(config.CRAWL_DELAY if crawl_delay is None else crawl_delay)
    max_fetches = int(config.MAX_FETCHES if max_fetches is None else max_fetches)
    email = (config.CONTACT_EMAIL if contact_email is None else contact_email).strip()
    if not email:
        raise ValueError("Crawling ditolak: CONTACT_EMAIL wajib diisi sebelum menjalankan crawler.")

    update_ui = ui_updater if ui_updater is not None else _create_default_ui(target_docs)
    update_ui(
        f"Memeriksa korpus lokal di {config.PATH_CORPUS}...",
        "Menghitung artikel yang sudah tersimpan",
        saved=0,
        bar_style="info",
        new_max=target_docs,
    )

    existing_docs = {}
    if config.PATH_CORPUS.exists():
        with open(config.PATH_CORPUS, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    existing_docs[doc["url"]] = doc
        if len(existing_docs) >= target_docs:
            update_ui(
                f"Korpus sudah mencapai target ({len(existing_docs)}/{target_docs} artikel). Pengambilan data dilewati.",
                f"Berkas: {config.PATH_CORPUS}",
                saved=target_docs,
                bar_style="success",
            )
            return

    if session is None:
        session = requests.Session()
        session.headers.update({
            "User-Agent": f"IR-Course-Bot/1.0 (tugas kuliah Information Retrieval; kontak: {email})"
        })

    update_ui(
        "Memuat riwayat visited_urls dan known_urls...",
        f"Artikel lokal saat ini: {len(existing_docs)}/{target_docs}",
        saved=len(existing_docs),
    )

    visited_urls = set(existing_docs.keys())
    if config.PATH_VISITED_URLS.exists():
        with open(config.PATH_VISITED_URLS, "r", encoding="utf-8") as f:
            visited_urls.update(line.strip() for line in f if line.strip())

    known_urls = []
    if config.PATH_KNOWN_URLS.exists():
        with open(config.PATH_KNOWN_URLS, "r", encoding="utf-8") as f:
            known_urls = [line.strip() for line in f if line.strip() and line.strip() not in visited_urls]

    reproduce_mode = False
    if use_corpus_urls and config.PATH_CORPUS_URLS.exists():
        with open(config.PATH_CORPUS_URLS, "r", encoding="utf-8") as f:
            target_urls = [line.strip() for line in f if line.strip()]
        needed_urls = [u for u in target_urls if u not in existing_docs]
        if needed_urls:
            known_urls = needed_urls
            reproduce_mode = True
            update_ui(
                f"Mode reproduksi aktif: {len(needed_urls)} URL target dimuat dari corpus_urls.txt.",
                f"Artikel lokal: {len(existing_docs)}/{target_docs}",
                saved=len(existing_docs),
            )

    if not known_urls and not reproduce_mode:
        sitemaps = [
            "https://www.cnbcindonesia.com/market/sitemap_news.xml",
            "https://www.cnbcindonesia.com/market/sitemap_web.xml",
        ]
        for sm_url in sitemaps:
            update_ui(
                f"Membaca sitemap awal: {sm_url}",
                f"Menemukan kandidat URL artikel (delay {crawl_delay} dtk)",
                saved=len(existing_docs),
            )
            try:
                resp = session.get(sm_url, timeout=request_timeout)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                    for loc in root.findall(".//sm:loc", ns):
                        u = loc.text.strip() if loc.text else ""
                        if u and ARTICLE_URL_PATTERN.match(u) and is_allowed_url(u) and u not in visited_urls:
                            known_urls.append(u)
                time.sleep(crawl_delay)
            except Exception as e:
                update_ui(
                    f"Peringatan: gagal membaca sitemap ({type(e).__name__})",
                    sm_url,
                    saved=len(existing_docs),
                )

    known_urls.sort(key=lambda u: (0 if "ihsg" in u.lower() else 1))
    consecutive_errors = 0
    fetch_count = 0
    saved_count = len(existing_docs)
    mode_label = "Reproduksi (corpus_urls.txt)" if reproduce_mode else "Discovery (BFS + Sitemap)"

    update_ui(
        f"Memulai crawler ({mode_label}) | Antrian: {len(known_urls)} URL",
        f"Target: {target_docs} | Delay: {crawl_delay}s | Max fetch: {max_fetches}",
        saved=saved_count,
    )

    interrupted = False
    try:
        with open(config.PATH_CORPUS, "a", encoding="utf-8") as corpus_file:
            while known_urls and saved_count < target_docs and fetch_count < max_fetches:
                url = known_urls.pop(0)
                if url in visited_urls:
                    continue
                visited_urls.add(url)
                fetch_count += 1

                update_ui(
                    f"[Fetch {fetch_count}/{max_fetches}] Mengunduh: {url}",
                    f"Mode: {mode_label} | Antrian: {len(known_urls)} URL | Error: {consecutive_errors}/{max_consecutive_errors}",
                    saved=saved_count,
                )

                try:
                    resp = session.get(url, timeout=request_timeout)
                    if resp.status_code == 429:
                        update_ui(
                            "HTTP 429 (Rate limit) \u2014 menunggu 60 detik sebelum melanjutkan...",
                            f"URL: {url} | Tersimpan: {saved_count}/{target_docs}",
                            saved=saved_count,
                            bar_style="warning",
                        )
                        time.sleep(60)
                        consecutive_errors += 1
                        continue
                    if resp.status_code != 200:
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            update_ui(
                                f"Berhenti: {consecutive_errors} error beruntun (HTTP {resp.status_code}).",
                                f"URL terakhir: {url}",
                                saved=saved_count,
                                bar_style="danger",
                            )
                            break
                        update_ui(
                            f"HTTP {resp.status_code} dilewati (jeda {crawl_delay}s): {url}",
                            f"Antrian: {len(known_urls)} URL | Error: {consecutive_errors}/{max_consecutive_errors}",
                            saved=saved_count,
                        )
                        time.sleep(crawl_delay)
                        continue

                    consecutive_errors = 0
                    html_content = resp.text

                    if not reproduce_mode:
                        update_ui(
                            f"[Fetch {fetch_count}] Memindai tautan artikel baru di halaman...",
                            f"Antrian: {len(known_urls)} URL",
                            saved=saved_count,
                        )
                        soup = BeautifulSoup(html_content, "html.parser")
                        for a_tag in soup.find_all("a", href=True):
                            href = a_tag["href"]
                            full_u = urllib.parse.urljoin(url, href).split("#")[0]
                            if ARTICLE_URL_PATTERN.match(full_u) and is_allowed_url(full_u):
                                if full_u not in visited_urls and full_u not in known_urls:
                                    if "ihsg" in full_u.lower():
                                        known_urls.insert(0, full_u)
                                    else:
                                        known_urls.append(full_u)

                    update_ui(
                        f"[Fetch {fetch_count}] Mengekstrak & memvalidasi konten artikel...",
                        url,
                        saved=saved_count,
                    )
                    doc = extract_article(html_content, url, min_text_len=min_text_len, require_ihsg=require_ihsg)
                    if doc:
                        corpus_file.write(json.dumps(doc, ensure_ascii=False) + "\n")
                        corpus_file.flush()
                        saved_count += 1
                        update_ui(
                            f"Tersimpan ({saved_count}/{target_docs}): {doc['title']}",
                            f"Mode: {mode_label} | Fetch: {fetch_count} | Antrian: {len(known_urls)} URL | Jeda {crawl_delay}s",
                            saved=saved_count,
                            bar_style="info",
                        )
                    else:
                        update_ui(
                            f"Dilewati (tidak lolos filter panjang/topik): {url}",
                            f"Mode: {mode_label} | Fetch: {fetch_count} | Antrian: {len(known_urls)} URL | Jeda {crawl_delay}s",
                            saved=saved_count,
                        )

                    time.sleep(crawl_delay)
                except Exception as e:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        update_ui(
                            f"Berhenti: {consecutive_errors} error beruntun ({type(e).__name__}).",
                            str(e),
                            saved=saved_count,
                            bar_style="danger",
                        )
                        break
                    update_ui(
                        f"Error {type(e).__name__} \u2014 menunggu jeda {crawl_delay}s...",
                        f"Error: {consecutive_errors}/{max_consecutive_errors} | Antrian: {len(known_urls)} URL",
                        saved=saved_count,
                    )
                    time.sleep(crawl_delay)
    except KeyboardInterrupt:
        interrupted = True
        update_ui(
            "Crawling dijeda pengguna. Menyimpan state URL ke disk...",
            f"Tersimpan sejauh ini: {saved_count}/{target_docs} artikel | Fetch: {fetch_count}",
            saved=saved_count,
            bar_style="warning",
        )

    if not interrupted:
        update_ui(
            "Menyimpan visited_urls.txt, known_urls.txt, dan corpus_urls.txt...",
            f"Fetch sesi ini: {fetch_count}",
            saved=saved_count,
        )

    with open(config.PATH_VISITED_URLS, "w", encoding="utf-8") as f:
        for u in visited_urls:
            f.write(u + "\n")
    with open(config.PATH_KNOWN_URLS, "w", encoding="utf-8") as f:
        for u in known_urls:
            f.write(u + "\n")

    all_corpus_urls = []
    if config.PATH_CORPUS.exists():
        with open(config.PATH_CORPUS, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_corpus_urls.append(json.loads(line)["url"])
    with open(config.PATH_CORPUS_URLS, "w", encoding="utf-8") as f:
        for u in all_corpus_urls:
            f.write(u + "\n")

    if interrupted:
        final_style = "warning"
        final_msg = f"Crawling dijeda pengguna. Total korpus: {len(all_corpus_urls)}/{target_docs} artikel."
    elif len(all_corpus_urls) >= target_docs:
        final_style = "success"
        final_msg = f"Selesai! Korpus mencapai {len(all_corpus_urls)}/{target_docs} artikel."
    else:
        final_style = "warning"
        final_msg = f"Selesai (belum mencapai target): {len(all_corpus_urls)}/{target_docs} artikel."

    update_ui(
        final_msg,
        f"Total fetch sesi ini: {fetch_count} | Sisa antrian: {len(known_urls)} URL",
        saved=min(len(all_corpus_urls), target_docs),
        bar_style=final_style,
    )
