from __future__ import annotations

import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path


CASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = CASE_DIR.parents[1]
REPLAY_PROMPT = "高级美学造型沙龙门店预约页，可选服务、造型师、日期、时段"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from render_wxml import render_phone_html  # noqa: E402
from validators import validate_project  # noqa: E402
from zip_exporter import export_zip  # noqa: E402

try:
    from scaffold import APP_WXSS  # noqa: E402
except Exception:
    APP_WXSS = ""


def _read(name: str) -> str:
    return (CASE_DIR / name).read_text(encoding="utf-8")


def _line_count(text: str) -> int:
    return len(text.splitlines())


def main() -> int:
    wxml = _read("index.wxml")
    wxss = _read("index.wxss")
    js = _read("index.js")

    files = {
        "pages/index/index.wxml": wxml,
        "pages/index/index.wxss": wxss,
        "pages/index/index.js": js,
    }
    validation = validate_project(files, full_project=False)

    preview_ok = False
    preview_error = ""
    try:
        html = render_phone_html(wxml, wxss, js, app_wxss=APP_WXSS, prompt=REPLAY_PROMPT)
        (CASE_DIR / "preview.html").write_text(html, encoding="utf-8")
        preview_ok = True
    except Exception as exc:
        preview_error = str(exc)

    zip_ok = False
    zip_error = ""
    zip_entries: list[str] = []
    try:
        zip_bytes = export_zip({"wxml": wxml, "wxss": wxss, "js": js})
        zip_path = CASE_DIR / "minipilot_export.zip"
        zip_path.write_bytes(zip_bytes)
        with zipfile.ZipFile(zip_path) as zf:
            zip_entries = zf.namelist()
        zip_ok = bool(zip_entries)
    except Exception as exc:
        zip_error = str(exc)

    report = {
        "case_id": "005_golden_store_booking",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "calls_gemma": False,
        "uses_live_generation": False,
        "line_counts": {
            "wxml": _line_count(wxml),
            "wxss": _line_count(wxss),
            "js": _line_count(js),
            "total": _line_count(wxml) + _line_count(wxss) + _line_count(js),
        },
        "validator": {
            "ok": validation.ok,
            "hard_errors": validation.hard_errors,
            "warnings": validation.warnings,
        },
        "preview": {
            "ok": preview_ok,
            "path": str(CASE_DIR / "preview.html") if preview_ok else "",
            "error": preview_error,
        },
        "zip": {
            "ok": zip_ok,
            "path": str(CASE_DIR / "minipilot_export.zip") if zip_ok else "",
            "error": zip_error,
            "entries": zip_entries,
        },
    }
    (CASE_DIR / "replay_test_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if preview_ok and zip_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
