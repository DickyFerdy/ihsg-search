"""Modul instalasi dependensi proyek dari requirements.txt dengan antarmuka widget ipywidgets."""

import html
import os
import re
import subprocess
import sys
from pathlib import Path

from IPython.display import clear_output, display

try:
    import ipywidgets as widgets
except ModuleNotFoundError:
    print("Memasang ipywidgets terlebih dahulu agar tombol antarmuka dapat ditampilkan...", flush=True)
    _boot_proc = subprocess.Popen(
        [sys.executable, "-m", "pip", "install", "--no-input", "--disable-pip-version-check", "ipywidgets>=8.0.0"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    for _boot_line in iter(_boot_proc.stdout.readline, ""):
        _msg = _boot_line.strip()
        if _msg:
            clear_output(wait=True)
            print(f"Memasang ipywidgets: {_msg}", flush=True)
    if _boot_proc.wait() != 0:
        raise RuntimeError("Gagal memasang ipywidgets secara otomatis.")
    clear_output(wait=True)
    import ipywidgets as widgets


def _set_status(status_label, text: str):
    """Menampilkan status tepat satu baris pada widget HTML."""
    safe_text = html.escape(text)
    status_label.value = (
        '<div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; '
        'font-family: monospace; font-size: 12px; color: inherit;">'
        f"{safe_text}</div>"
    )


def _parse_pip_status(line: str, req_pkgs: list[str], seen_pkgs: set[str]) -> tuple[str | None, int | None]:
    """Mengubah baris output pip menjadi status 1 baris dan estimasi progres."""
    if line.startswith("Requirement already satisfied:"):
        pkg = line.split(":", 1)[1].split(" in ", 1)[0].strip()
        norm = re.split(r"[<>=!~;\[\s]", pkg, maxsplit=1)[0].lower().replace("_", "-")
        if norm in req_pkgs:
            seen_pkgs.add(norm)
        return f"Memeriksa (sudah terpasang): {pkg}", int(5 + 75 * len(seen_pkgs) / max(len(req_pkgs), 1))
    if line.startswith("Collecting "):
        pkg = line[len("Collecting "):].strip()
        norm = re.split(r"[<>=!~;\[\s]", pkg, maxsplit=1)[0].lower().replace("_", "-")
        if norm in req_pkgs:
            seen_pkgs.add(norm)
        return f"Mengumpulkan paket: {pkg}", int(5 + 75 * len(seen_pkgs) / max(len(req_pkgs), 1))
    if line.startswith("Downloading "):
        return f"Mengunduh: {line[len('Downloading '):].strip()}", None
    if line.startswith("Using cached "):
        return f"Menggunakan cache: {line[len('Using cached '):].strip()}", None
    if line.startswith("Installing collected packages:"):
        pkgs = line.split(":", 1)[1].strip()
        return f"Menginstal paket: {pkgs}", 85
    if line.startswith("Successfully installed"):
        return "Berhasil menginstal paket dependensi.", 95
    if line.startswith(("Preparing metadata", "Getting requirements", "Building wheel")):
        return f"Memproses: {line}", None
    if line.startswith("Note:"):
        return None, None
    return line, None


def show_install_ui():
    """Menampilkan antarmuka tombol instalasi dependensi dengan progress bar."""
    btn_install = widgets.Button(
        description="Mulai / Jalankan Instalasi",
        button_style="primary",
        icon="play",
        layout=widgets.Layout(width="auto", min_width="230px"),
    )
    progress_bar = widgets.IntProgress(
        value=0, min=0, max=100,
        description="Proses:",
        bar_style="info",
        layout=widgets.Layout(width="420px"),
    )
    status_label = widgets.HTML(
        value="",
        layout=widgets.Layout(width="100%", overflow="hidden"),
    )
    progress_box = widgets.VBox(
        [progress_bar, status_label],
        layout=widgets.Layout(display="none", margin="8px 0 0 0"),
    )

    def _on_install_clicked(_):
        btn_install.disabled = True
        btn_install.description = "Menginstal..."
        progress_box.layout.display = "flex"
        progress_bar.bar_style = "info"
        progress_bar.value = 5
        _set_status(status_label, "Mempersiapkan instalasi dependensi dari requirements.txt...")

        req_file = Path("requirements.txt")
        req_pkgs = []
        if req_file.exists():
            for raw in req_file.read_text(encoding="utf-8").splitlines():
                item = raw.strip()
                if item and not item.startswith("#"):
                    name = re.split(r"[<>=!~;\[\s]", item, maxsplit=1)[0].lower().replace("_", "-")
                    if name:
                        req_pkgs.append(name)

        seen_pkgs = set()
        last_line = ""
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        try:
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install", "--no-input", "--disable-pip-version-check", "-r", "requirements.txt"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
            )
            for raw_line in iter(proc.stdout.readline, ""):
                clean_line = raw_line.strip()
                if not clean_line:
                    continue
                last_line = clean_line
                status_msg, next_val = _parse_pip_status(clean_line, req_pkgs, seen_pkgs)
                if status_msg:
                    _set_status(status_label, status_msg)
                if next_val is not None and next_val > progress_bar.value:
                    progress_bar.value = min(next_val, 95)

            return_code = proc.wait()
            if return_code == 0:
                progress_bar.value = 100
                progress_bar.bar_style = "success"
                _set_status(status_label, f"Selesai! Semua dependensi ({max(len(req_pkgs), 1)} paket) siap digunakan.")
            else:
                progress_bar.bar_style = "danger"
                _set_status(status_label, f"Gagal (kode {return_code}): {last_line}")
        except Exception as exc:
            progress_bar.bar_style = "danger"
            _set_status(status_label, f"Terjadi error saat instalasi: {exc}")
        finally:
            btn_install.disabled = False
            btn_install.description = "Mulai / Jalankan Instalasi"

    btn_install.on_click(_on_install_clicked)
    display(widgets.VBox([btn_install, progress_box]))
