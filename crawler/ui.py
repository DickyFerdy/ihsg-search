"""Modul antarmuka widget ipywidgets untuk crawler CNBC Indonesia.

Menyediakan panel konfigurasi parameter crawler interaktif dan monitor progres real-time.
"""

import html as html_lib

import ipywidgets as widgets
from IPython.display import display

import config
from crawler.crawler import run_crawler, _count_existing_corpus


def _build_crawler_monitor(target_docs: int):
    """Membuat widget loading bar dan status display 1 baris untuk crawler."""
    safe_max = max(int(target_docs), 1)
    progress_bar = widgets.IntProgress(
        value=0, min=0, max=safe_max,
        description="Korpus:",
        bar_style="info",
        style={"description_width": "65px"},
        layout=widgets.Layout(flex="1 1 auto", width="auto"),
    )
    pct_label = widgets.HTML(
        value=f"<b>0/{safe_max} (0.0%)</b>",
        layout=widgets.Layout(min_width="150px", margin="0 0 0 10px"),
    )
    status_label = widgets.HTML(
        value='<div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; '
              'font-family: monospace; font-size: 12px;">Menunggu mulai...</div>',
        layout=widgets.Layout(width="100%", overflow="hidden"),
    )
    detail_label = widgets.HTML(
        value='<div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; '
              'font-size: 12px; opacity: 0.75;">Siap menjalankan crawler.</div>',
        layout=widgets.Layout(width="100%", overflow="hidden"),
    )
    monitor_box = widgets.VBox(
        [widgets.HBox([progress_bar, pct_label]), status_label, detail_label],
        layout=widgets.Layout(width="100%", gap="4px"),
    )

    def _update(
        status_msg: str,
        detail_msg: str = "",
        saved: int | None = None,
        bar_style: str | None = None,
        new_max: int | None = None,
    ):
        if new_max is not None:
            progress_bar.max = max(int(new_max), 1)
        cur_target = max(int(progress_bar.max), 1)
        if saved is not None:
            progress_bar.value = min(max(int(saved), 0), cur_target)
            pct = (saved / cur_target * 100.0) if cur_target > 0 else 100.0
            pct_label.value = f"<b>{saved}/{cur_target} ({pct:.1f}%)</b>"
        if bar_style is not None:
            progress_bar.bar_style = bar_style
        safe_status = html_lib.escape(status_msg)
        status_label.value = (
            '<div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; '
            'font-family: monospace; font-size: 12px; color: inherit;">'
            f"{safe_status}</div>"
        )
        if detail_msg:
            safe_detail = html_lib.escape(detail_msg)
            detail_label.value = (
                '<div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; '
                'font-size: 12px; opacity: 0.75;">'
                f"{safe_detail}</div>"
            )

    return monitor_box, _update


def show_crawler_launcher():
    """Menampilkan tombol konfirmasi -> panel konfigurasi parameter crawler -> monitor progres."""
    default_email = config.CONTACT_EMAIL
    default_target = config.TARGET_DOCS
    default_delay = config.CRAWL_DELAY
    default_max_fetch = config.MAX_FETCHES

    # Tahap 1: Tombol konfirmasi menjalankan sel
    btn_open_config = widgets.Button(
        description="Mulai / Jalankan Sel",
        button_style="primary",
        icon="sliders",
        layout=widgets.Layout(width="auto", min_width="220px"),
    )
    confirm_info = widgets.HTML(
        value=f"<span style='opacity:0.8'>Korpus lokal saat ini: <b>{_count_existing_corpus()}</b> artikel. "
              "Klik untuk membuka pengaturan crawler.</span>",
        layout=widgets.Layout(margin="4px 0 0 10px"),
    )
    confirm_box = widgets.HBox([btn_open_config, confirm_info])

    # Tahap 2: Form parameter crawler
    field_style = {"description_width": "185px"}
    field_layout = widgets.Layout(width="470px")

    email_input = widgets.Text(
        value=str(default_email), placeholder="nama@email.com",
        description="contact_email:", style=field_style, layout=field_layout,
    )
    target_input = widgets.BoundedIntText(
        value=int(default_target), min=1, max=100000, step=50,
        description="target_docs (jumlah):", style=field_style, layout=field_layout,
    )
    delay_input = widgets.BoundedFloatText(
        value=float(default_delay), min=0.0, max=60.0, step=0.5,
        description="crawl_delay (detik):", style=field_style, layout=field_layout,
    )
    max_fetch_input = widgets.BoundedIntText(
        value=int(default_max_fetch), min=1, max=100000, step=100,
        description="max_fetches:", style=field_style, layout=field_layout,
    )
    timeout_input = widgets.BoundedIntText(
        value=10, min=3, max=60, step=1,
        description="request_timeout (detik):", style=field_style, layout=field_layout,
    )
    max_err_input = widgets.BoundedIntText(
        value=8, min=1, max=50, step=1,
        description="maks_error_beruntun:", style=field_style, layout=field_layout,
    )
    min_len_input = widgets.BoundedIntText(
        value=300, min=50, max=5000, step=50,
        description="min_panjang_teks (karakter):", style=field_style, layout=field_layout,
    )
    repro_checkbox = widgets.Checkbox(
        value=True,
        description="Gunakan corpus_urls.txt jika tersedia (Mode Reproduksi)",
        indent=False,
    )
    ihsg_checkbox = widgets.Checkbox(
        value=True,
        description="Wajib mengandung kata kunci IHSG / Indeks Harga Saham Gabungan",
        indent=False,
    )

    btn_start_crawl = widgets.Button(
        description="Mulai Crawling", button_style="success", icon="play",
        layout=widgets.Layout(width="165px"),
    )
    btn_reset = widgets.Button(
        description="Reset Default", button_style="", icon="refresh",
        layout=widgets.Layout(width="135px"),
    )
    btn_close = widgets.Button(
        description="Tutup", button_style="", icon="times",
        layout=widgets.Layout(width="100px"),
    )
    validation_msg = widgets.HTML(value="")
    config_header = widgets.HTML(value="")

    config_box = widgets.VBox(
        [
            config_header,
            email_input, target_input, delay_input, max_fetch_input,
            timeout_input, max_err_input, min_len_input,
            repro_checkbox, ihsg_checkbox,
            widgets.HBox(
                [btn_start_crawl, btn_reset, btn_close],
                layout=widgets.Layout(gap="8px", margin="6px 0 0 0"),
            ),
            validation_msg,
        ],
        layout=widgets.Layout(display="none", gap="5px"),
    )

    # Tahap 3: Monitor loading bar & status display 1 baris
    monitor_box, update_ui = _build_crawler_monitor(int(default_target))
    monitor_box.layout.display = "none"

    root_box = widgets.VBox(
        [confirm_box, config_box, monitor_box],
        layout=widgets.Layout(
            border="1px solid #ddd", padding="12px",
            border_radius="6px", width="100%", gap="10px",
        ),
    )

    def _refresh_header():
        config_header.value = (
            "<b>Pengaturan Parameter Crawler</b> "
            f"<span style='opacity:0.75'>(Korpus lokal saat ini: {_count_existing_corpus()} artikel)</span>"
        )

    def _on_open_config(_):
        _refresh_header()
        validation_msg.value = ""
        confirm_box.layout.display = "none"
        config_box.layout.display = "flex"

    def _on_reset(_):
        email_input.value = str(config.CONTACT_EMAIL)
        target_input.value = int(config.TARGET_DOCS)
        delay_input.value = float(config.CRAWL_DELAY)
        max_fetch_input.value = int(config.MAX_FETCHES)
        timeout_input.value = 10
        max_err_input.value = 8
        min_len_input.value = 300
        repro_checkbox.value = True
        ihsg_checkbox.value = True
        validation_msg.value = "<span style='opacity:0.75'>Parameter dikembalikan ke nilai default.</span>"

    def _on_close(_):
        config_box.layout.display = "none"
        confirm_info.value = (
            f"<span style='opacity:0.8'>Korpus lokal saat ini: <b>{_count_existing_corpus()}</b> artikel. "
            "Klik untuk membuka pengaturan crawler.</span>"
        )
        confirm_box.layout.display = "flex"

    def _set_controls_disabled(disabled: bool):
        for w in (
            email_input, target_input, delay_input, max_fetch_input,
            timeout_input, max_err_input, min_len_input,
            repro_checkbox, ihsg_checkbox,
            btn_start_crawl, btn_reset, btn_close,
        ):
            w.disabled = disabled

    def _on_start_crawl(_):
        email_val = email_input.value.strip()
        if not email_val:
            validation_msg.value = (
                "<span style='color:#c62828'><b>Error:</b> contact_email wajib diisi "
                "sebelum memulai crawling.</span>"
            )
            return

        validation_msg.value = ""
        config.CONTACT_EMAIL = email_val
        config.TARGET_DOCS = int(target_input.value)
        config.CRAWL_DELAY = float(delay_input.value)
        config.MAX_FETCHES = int(max_fetch_input.value)

        monitor_box.layout.display = "flex"
        _set_controls_disabled(True)
        btn_start_crawl.description = "Crawling..."
        try:
            run_crawler(
                target_docs=config.TARGET_DOCS,
                crawl_delay=config.CRAWL_DELAY,
                max_fetches=config.MAX_FETCHES,
                contact_email=config.CONTACT_EMAIL,
                use_corpus_urls=bool(repro_checkbox.value),
                request_timeout=int(timeout_input.value),
                max_consecutive_errors=int(max_err_input.value),
                min_text_len=int(min_len_input.value),
                require_ihsg=bool(ihsg_checkbox.value),
                ui_updater=update_ui,
            )
        except Exception as exc:
            update_ui(
                f"Terjadi kesalahan: {exc}",
                "Periksa parameter atau koneksi internet lalu coba lagi.",
                bar_style="danger",
            )
        finally:
            btn_start_crawl.description = "Mulai Crawling"
            _set_controls_disabled(False)
            _refresh_header()

    btn_open_config.on_click(_on_open_config)
    btn_reset.on_click(_on_reset)
    btn_close.on_click(_on_close)
    btn_start_crawl.on_click(_on_start_crawl)
    display(root_box)
    return root_box
