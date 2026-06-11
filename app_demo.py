from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components


ROOT = Path(__file__).resolve().parent
GEMMA_CORE = ROOT / "gemma_core"
# `streamlit run app_demo.py` pre-populates sys.path with ROOT (the script's
# own directory) *before* this module runs its own setup. The old `not in
# sys.path` guards then saw ROOT already present and skipped re-inserting it,
# leaving GEMMA_CORE ahead of ROOT — so `from validators import ...` resolved
# to the stale gemma_core/validators.py (whose ALLOWED_SUFFIXES lacks image
# suffixes) instead of the root validators.py. Removing both first guarantees
# ROOT ends up before GEMMA_CORE regardless of what the runner pre-populated.
for _p in (str(GEMMA_CORE), str(ROOT)):
    if _p in sys.path:
        sys.path.remove(_p)
sys.path.insert(0, str(GEMMA_CORE))
sys.path.insert(0, str(ROOT))

from gemma_client import call_gemma_with_tools, call_gemma_text  # noqa: E402
from golden_examples import get_golden_example  # noqa: E402
from prompt_builder import (  # noqa: E402
    build_prompt,
    build_repair_prompt,
    build_enriched_prompt,
    CLARIFY_TEMPLATE,
    parse_clarify_questions,
)
from render_wxml import render_phone_html  # noqa: E402
from scaffold import APP_WXSS  # noqa: E402
from validators import ValidationResult, validate_project  # noqa: E402
from zip_exporter import export_zip  # noqa: E402
from agent_trace import TraceRecorder  # noqa: E402
from generation_report import build_generation_report, normalize_validator_result, sanitize  # noqa: E402
from miniprogram_assets import assets_to_preview_images, attach_assets_and_fallback, validation_asset_files  # noqa: E402
from miniprogram_assets import prepare_uploaded_assets  # noqa: E402
from miniprogram_assets import preprocess_uploaded_image  # noqa: E402
from image_library import select_image_assets  # noqa: E402
from provider_health import check_amd_health, check_google_health, check_replay_health  # noqa: E402


SHOWCASE_URL = "http://localhost:8504"
DEMO_URL = "http://localhost:8505"
PRODUCT_NAME = "MiniPilot Agent"
PRODUCT_FULL_NAME = "MiniPilot Agent｜小程序 MVP 生成智能体"
PRODUCT_TAGLINE = "一句生意需求，生成小程序 MVP。"
POWERED_BY = "Powered by Gemma 4."
BENCHMARK_PATH = GEMMA_CORE / "benchmark_prompts.json"
GOLDEN_DIR = GEMMA_CORE / "golden_examples"
LOG_PATH = ROOT / "demo_cache" / "gemma.log"
AMD_CONFIG_PATH = Path(r"E:\file+desktop\gemma_amd_config.txt")
LIVE_SESSION_DIR = ROOT / "demo_cache" / "live_sessions"
LIVE_SESSION_DIR.mkdir(parents=True, exist_ok=True)
LIVE_SESSION_INDEX_PATH = LIVE_SESSION_DIR / "index.json"

DEFAULT_EXAMPLES = [
    ("咖啡店点单页", "生成一个咖啡店点单小程序页面，包含门店封面、分类 Tab、商品列表、购物车和底部结算栏。"),
    ("门店预约页", "生成一个美业门店预约小程序页面，包含门店介绍、服务项目、营业时间、预约表单和底部预约按钮。"),
    ("商品详情页", "生成一个商品详情小程序页面，包含商品大图、价格、优惠信息、商品介绍、规格选择和底部购买按钮。"),
    ("餐厅菜单页", "生成一个餐厅菜单小程序页面，包含菜品分类、推荐菜、价格、购物车和下单按钮。"),
]


def _safe_get(obj, key, default=None):
    return obj.get(key, default) if isinstance(obj, dict) else default


def _safe_session_id(value: str | None) -> str:
    text = (value or "").strip()
    return text if re.fullmatch(r"[A-Za-z0-9_-]{8,80}", text) else ""


def _session_path(session_id: str) -> Path:
    return LIVE_SESSION_DIR / f"{_safe_session_id(session_id)}.json"


def _load_session_index() -> list[dict]:
    if not LIVE_SESSION_INDEX_PATH.exists():
        return []
    try:
        data = json.loads(LIVE_SESSION_INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _write_session_index(items: list[dict]) -> None:
    LIVE_SESSION_INDEX_PATH.write_text(json.dumps(items[:30], ensure_ascii=False, indent=2), encoding="utf-8")


def _validation_to_dict(validation: ValidationResult | None) -> dict:
    validation = validation or _blank_validation()
    return {
        "ok": bool(validation.ok),
        "hard_errors": list(validation.hard_errors),
        "warnings": list(validation.warnings),
    }


def _validation_from_dict(payload: dict | None, page_files: dict | None) -> ValidationResult:
    if isinstance(payload, dict):
        return ValidationResult(
            hard_errors=list(payload.get("hard_errors") or []),
            warnings=list(payload.get("warnings") or []),
        )
    return validate_project(_validator_files(page_files or {}), full_project=False) if page_files else _blank_validation()


def _session_label(item: dict) -> str:
    prompt = str(item.get("prompt") or "").strip().replace("\n", " ")
    prompt = prompt[:34] + ("..." if len(prompt) > 34 else "")
    return f"{item.get('saved_at', '')} · {prompt or item.get('session_id', '')}"


def _new_session_id() -> str:
    return f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"


def _save_live_session(
    page_files: dict | None,
    prompt: str = "",
    trace_data: list | None = None,
    raw_debug: dict | None = None,
    validation: ValidationResult | None = None,
    session_id: str | None = None,
    generation_report: dict | None = None,
    agent_trace_steps: list | None = None,
    tool_calls: dict | None = None,
) -> str | None:
    if not page_files:
        return None
    session_id = _safe_session_id(session_id) or _new_session_id()
    saved_at = time.strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "version": 2,
        "session_id": session_id,
        "saved_at": saved_at,
        "prompt": prompt,
        "natural_language_input": prompt,
        "files": page_files,
        "code": {
            "wxml": _safe_get(page_files, "wxml", ""),
            "wxss": _safe_get(page_files, "wxss", ""),
            "js": _safe_get(page_files, "js", ""),
        },
        "trace_data": trace_data or [],
        "raw_debug": raw_debug or {},
        "validation": _validation_to_dict(validation),
        "generation_report": generation_report or {},
        "agent_trace_steps": agent_trace_steps or [],
        "tool_calls": tool_calls or {},
        "phone_preview": {
            "kind": "rendered_from_saved_wxml_wxss_js_and_assets",
            "renderer": "render_wxml.render_phone_html",
        },
    }
    payload = sanitize(payload)
    _session_path(session_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    index = [item for item in _load_session_index() if item.get("session_id") != session_id]
    index.insert(
        0,
        {
            "session_id": session_id,
            "saved_at": saved_at,
            "prompt": prompt,
            "provider": _safe_get(page_files, "provider"),
            "parse_method": _safe_get(page_files, "parse_method"),
            "line_count": sum(_line_count(_safe_get(page_files, key, "")) for key in ("wxml", "wxss", "js")),
        },
    )
    _write_session_index(index)
    return session_id


def _load_live_session(session_id: str | None) -> dict | None:
    session_id = _safe_session_id(session_id)
    if not session_id:
        return None
    path = _session_path(session_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _line_count(text: str) -> int:
    return len((text or "").splitlines())


def _validator_files(page_files: dict[str, str]) -> dict[str, str]:
    files = {
        "pages/index/index.wxml": _safe_get(page_files, "wxml", ""),
        "pages/index/index.wxss": _safe_get(page_files, "wxss", ""),
        "pages/index/index.js": _safe_get(page_files, "js", ""),
    }
    files.update(validation_asset_files(page_files))
    return files


def _golden_count() -> int:
    if not GOLDEN_DIR.exists():
        return 0
    return sum(1 for path in GOLDEN_DIR.iterdir() if path.is_dir())


def _benchmark_examples() -> list[tuple[str, str]]:
    if not BENCHMARK_PATH.exists():
        return []
    try:
        data = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    items = data if isinstance(data, list) else data.get("cases", [])
    result = []
    for item in items[:4]:
        if isinstance(item, dict) and item.get("prompt"):
            result.append((str(item.get("scenario") or "Benchmark"), str(item["prompt"])))
        elif isinstance(item, str):
            result.append(("Benchmark", item))
    return result


def _example_prompts() -> list[tuple[str, str]]:
    return DEFAULT_EXAMPLES


def _set_prompt(value: str) -> None:
    st.session_state.input_prompt = value
    st.session_state.trace_data = _empty_trace(value)


def _clear_prompt() -> None:
    st.session_state.input_prompt = ""
    st.session_state.page_files = None
    st.session_state.validation = _blank_validation()
    st.session_state.trace_data = _empty_trace("")
    st.session_state.raw_debug = {}
    st.session_state.image_list = None
    st.session_state.used_fallback = False
    st.session_state.current_session_id = ""
    st.session_state.generation_report = None
    st.session_state.agent_trace_steps = []
    st.session_state["_show_deploy"] = False
    try:
        st.query_params.clear()
    except Exception:
        pass


_MODE_OPTIONS = {
    "agent": "⚡ 快速 Agent 模式（Google AI Studio · 主链路）",
    "deep":  "🔬 深度生成模式（AMD vLLM Gemma 31B 自托管 · 长上下文）",
}
_MODE_DISPLAY = {
    "agent": "快速 Agent 模式（Google AI Studio）",
    "deep": "深度生成模式（AMD vLLM Gemma 31B）",
}
_PROVIDER_DISPLAY = {
    "amd": "AMD vLLM Gemma 31B（自托管 · 深度生成模式）",
    "google": "Google AI Studio Gemma 4（快速 Agent 模式）",
}
_PARSE_METHOD_DISPLAY = {
    "standard_tool_calls": "标准 tool_calls（原生结构化输出）",
    "gemma_raw_tool_call": "Gemma 原生信封解析（自定义适配层）",
    "plain_text_fallback": "纯文本兜底解析",
}
_MODEL_DISPLAY = {
    "google": "gemma-4-26b-a4b-it",
    "amd": "gemma-31b（vLLM 自托管）",
}
GENERATION_RECORDS_LIMIT = 30  # _write_session_index already caps at this; kept here for reference


def _configured_backends_label() -> str:
    """Static view of which backends are *configured* (not which one actually served the last request)."""
    parts = []
    if AMD_CONFIG_PATH.exists():
        parts.append("AMD vLLM Gemma 31B")
    if (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GEMMA_API_KEY")
        or (ROOT / ".env").exists()
        or Path(r"E:\file+desktop\gemma_key.txt").exists()
    ):
        parts.append("Google AI Studio")
    return " + ".join(parts) if parts else "Unknown"


@st.cache_data(ttl=15, show_spinner=False)
def _cached_amd_health() -> dict:
    """check_amd_health() result, cached for 15s so the 3-5s probe doesn't
    run on every Streamlit rerun (every widget interaction reruns the script)."""
    return check_amd_health()


_PROVIDER_STATUS_LABELS = {
    "replay": {"online": "✅ Available", "missing_config": "⚪ Missing", "error": "🔴 Error"},
    "google": {"online": "✅ Available", "missing_config": "⚪ Missing API Key", "error": "🔴 Error"},
    "amd_vllm": {"online": "🟢 Online", "offline": "🔴 Offline", "missing_config": "⚪ Missing Config", "error": "🔴 Error"},
}


def _render_provider_status() -> None:
    """Provider Status panel — Replay / Google Stable Agent Mode / AMD Deep
    Generation Mode. Read-only; never blocks more than the cached AMD probe."""
    replay = check_replay_health()
    google = check_google_health()
    amd = _cached_amd_health()

    def _label(health: dict) -> str:
        return _PROVIDER_STATUS_LABELS.get(health["provider"], {}).get(health["status"], health["status"])

    cols = st.columns(3)
    cols[0].caption(f"**Replay**: {_label(replay)}")
    cols[1].caption(f"**Google Stable Agent Mode**: {_label(google)}")
    amd_caption = f"**AMD Deep Generation Mode**: {_label(amd)}"
    if amd["status"] not in ("online",):
        amd_caption += f"  \n_{amd['reason']}_"
    cols[2].caption(amd_caption)


def _block_if_amd_unavailable(mode: str) -> bool:
    """If the user forced 深度生成模式 (deep) but AMD is unavailable, show an
    error and return True so the caller skips generation entirely — no
    spinner, no hung request."""
    if mode != "deep":
        return False
    health = check_amd_health()
    if health.get("ok"):
        return False
    st.error(f"🔬 AMD Deep Generation Mode is offline ({health['reason']}). Please use Google Stable Agent Mode or Replay Demo.")
    return True


def _actual_provider_label(page_files: dict | None) -> str:
    """Truthful label for which backend actually served the last request — read from the
    real result returned by call_gemma_with_tools, never guessed from static config."""
    provider = _safe_get(page_files, "provider")
    if provider:
        return _PROVIDER_DISPLAY.get(provider, provider)
    if page_files:
        return "黄金样例兜底（模型调用未成功）"
    return _configured_backends_label()


def _blank_validation() -> ValidationResult:
    return ValidationResult()


def _empty_trace(prompt: str = "") -> list[dict]:
    return [
        {"status": "skipped", "title": "Requirement Understanding", "summary": _summarize_requirement(prompt) if prompt else "Waiting for input", "metrics": {}},
        {"status": "skipped", "title": "Context Assembly", "summary": "Prompt context not assembled yet", "metrics": {}},
        {"status": "skipped", "title": "Function Calling", "summary": "create_miniprogram_page", "metrics": {}},
        {"status": "skipped", "title": "Code Parsing", "summary": "No generated code yet", "metrics": {}},
        {"status": "skipped", "title": "Static Validator", "summary": "Waiting for WXML / WXSS / JS", "metrics": {}},
        {"status": "skipped", "title": "Repair Loop", "summary": "No repair needed / Not triggered", "metrics": {}},
        {"status": "skipped", "title": "Preview / Export", "summary": "Generate a mini program to preview here.", "metrics": {}},
    ]


def _summarize_requirement(prompt: str) -> str:
    text = (prompt or "").strip()
    if not text:
        return "unknown"
    if "咖啡" in text:
        return "咖啡店点单页 / 目标：商品选择与购物车"
    if "餐厅" in text or "菜单" in text:
        return "餐厅菜单页 / 目标：分类浏览与下单"
    if "预约" in text:
        return "门店预约页 / 目标：服务选择与表单提交"
    if "商品" in text:
        return "商品详情页 / 目标：展示信息与购买转化"
    return text[:42] + ("..." if len(text) > 42 else "")


def _trace_after_generation(
    prompt: str,
    built_prompt: str,
    page_files: dict[str, str] | None,
    validation: ValidationResult | None,
    repair_status: str,
    repair_summary: str,
    elapsed: float | None,
    error: str | None = None,
    img_count: int = 0,
) -> list[dict]:
    page_files = page_files or {}
    validation = validation or _blank_validation()
    wxml = _safe_get(page_files, "wxml", "")
    wxss = _safe_get(page_files, "wxss", "")
    js = _safe_get(page_files, "js", "")
    has_code = bool(wxml and wxss and js)
    total_lines = _line_count(wxml) + _line_count(wxss) + _line_count(js)
    validator_status = "success" if validation.ok else ("warning" if validation.hard_errors or validation.warnings else "skipped")
    function_status = "error" if error else ("success" if has_code else "skipped")

    fc_metrics = {"provider": _actual_provider_label(page_files), "elapsed sec": f"{elapsed:.1f}" if elapsed else "unknown"}
    if page_files.get("parse_method"):
        fc_metrics["parse method"] = _PARSE_METHOD_DISPLAY.get(page_files["parse_method"], page_files["parse_method"])
    if page_files.get("fallback_used"):
        fc_metrics["requested mode"] = _MODE_DISPLAY.get(page_files.get("requested_mode"), page_files.get("requested_mode"))
        fc_metrics["fallback"] = page_files.get("fallback_reason", "原链路暂不可用")

    req_metrics = {"prompt chars": len(prompt or "")}
    if img_count:
        req_metrics["reference images"] = img_count

    return [
        {
            "status": "success" if prompt else "skipped",
            "title": "Requirement Understanding",
            "summary": _summarize_requirement(prompt),
            "metrics": req_metrics,
        },
        {
            "status": "success",
            "title": "Context Assembly",
            "summary": "Prompt assembled with existing gemma_core prompt builder",
            "metrics": {
                "prompt tokens": max(1, len(built_prompt) // 2) if built_prompt else "unknown",
                "examples": _golden_count() or "unknown",
                "verified images": "from prompt library",
            },
        },
        {
            "status": function_status,
            "title": "Function Calling",
            "summary": (error or "create_miniprogram_page") if not page_files.get("fallback_used") else "create_miniprogram_page · 已自动切换后端兜底",
            "metrics": fc_metrics,
        },
        {
            "status": "success" if has_code else "skipped",
            "title": "Code Parsing",
            "summary": "WXML / WXSS / JS extracted" if has_code else "No generated code",
            "metrics": {
                "WXML lines": _line_count(wxml),
                "WXSS lines": _line_count(wxss),
                "JS lines": _line_count(js),
                "total lines": total_lines if has_code else "—",
            },
        },
        {
            "status": validator_status,
            "title": "Static Validator",
            "summary": "Passed hard checks" if validation.ok else "Validator reported issues",
            "metrics": {"errors": len(validation.hard_errors), "warnings": len(validation.warnings)},
        },
        {
            "status": repair_status,
            "title": "Repair Loop",
            "summary": repair_summary,
            "metrics": {},
        },
        {
            "status": "success" if has_code else "warning",
            "title": "Preview / Export",
            "summary": "preview rendered; code available" if has_code else "preview unavailable",
            "metrics": {"preview": "ready" if has_code else "empty"},
        },
    ]


def render_agent_trace(trace_data: list[dict]) -> None:
    icons = {
        "success": "OK",
        "warning": "WARN",
        "running": "RUN",
        "skipped": "SKIP",
        "error": "ERR",
    }
    html = ['<div class="trace-list">']
    for idx, item in enumerate(trace_data or [], start=1):
        status = str(_safe_get(item, "status", "skipped"))
        title = str(_safe_get(item, "title", "Untitled"))
        summary = str(_safe_get(item, "summary", ""))
        metrics = _safe_get(item, "metrics", {}) or {}
        metric_html = "".join(f"<span><b>{key}</b>{value}</span>" for key, value in metrics.items())
        html.append(
            f'<div class="trace-item trace-{status}">'
            f'<div class="trace-badge">{icons.get(status, status.upper())}</div>'
            f'<div><h4><span class="trace-step">STEP {idx:02d}</span>{title}</h4>'
            f'<p>{summary}</p><div class="trace-metrics">{metric_html}</div></div>'
            f"</div>"
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


_TRACE_STEP_ICON = {
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
    "running": "🔄",
    "skipped": "⏭️",
    "pending": "⏳",
}


def _render_detailed_trace(steps: list[dict] | None) -> None:
    """Renders the 12-step Agent Trace evidence (agent_trace.TraceRecorder output)."""
    if not steps:
        return
    try:
        with st.expander("🔬 Agent Trace · 详细证据链（12 步）", expanded=False):
            for step in steps:
                icon = _TRACE_STEP_ICON.get(str(step.get("status", "skipped")), "•")
                title = step.get("title") or step.get("step_id") or "Step"
                message = step.get("message") or ""
                duration = step.get("duration_ms", 0)
                st.markdown(f"{icon} **{title}** — {message}  `{duration} ms`")
                meta = step.get("metadata") or {}
                if meta:
                    st.caption(" · ".join(f"{k}: {v}" for k, v in meta.items()))
    except Exception as exc:
        st.caption(f"Agent Trace 渲染失败（不影响主流程）：{exc}")


def _fmt_duration(ms) -> str:
    """Render a millisecond duration as a human-friendly seconds/minutes string."""
    try:
        seconds = float(ms) / 1000
    except (TypeError, ValueError):
        return "0.0s"
    return f"{seconds / 60:.1f} min" if seconds >= 60 else f"{seconds:.1f}s"


def _render_generation_report(report: dict | None) -> None:
    """Renders the Generation Report panel. Missing fields show as 'unknown' /
    0 / empty rather than raising, per the evidence-without-crashing requirement."""
    if not report:
        st.info("生成一次（或加载一条 Replay 记录）后，这里会显示 Generation Report。")
        return
    try:
        tool = report.get("tool") or {}
        validator = report.get("validator") or {}
        repair = report.get("repair_loop") or {}
        assets = report.get("assets") or {}
        preview = report.get("preview") or {}
        export = report.get("export") or {}
        durations = report.get("durations") or {}

        c1, c2, c3 = st.columns(3)
        c1.metric("Provider", report.get("provider", "unknown"))
        c2.metric("Model", report.get("model", "unknown"))
        c3.metric("Backend Mode", report.get("backend_mode", "unknown"))

        st.markdown(
            f"- **Tool**: `{tool.get('name', 'unknown')}` · "
            f"Tool Call Detected: {'✅' if tool.get('tool_call_detected') else '❌'} · "
            f"Parse Method: `{tool.get('parse_method', 'unknown')}`"
        )
        st.markdown(
            f"- **Validator**: `{validator.get('status', 'unknown')}` · "
            f"Hard Errors: {validator.get('hard_errors_count', 0)} · "
            f"Warnings: {validator.get('warnings_count', 0)}"
        )
        if repair.get("attempted"):
            repair_label = "✅ repaired, now passes" if repair.get("success") else "⚠️ attempted, issues remain"
        else:
            repair_label = "skipped / not triggered"
        st.markdown(
            f"- **Repair Loop**: {repair_label} · rounds={repair.get('rounds', 0)} · "
            f"{repair.get('before_errors_count', 0)} → {repair.get('after_errors_count', 0)} hard errors"
        )
        st.markdown(
            f"- **Assets Grounding**: `{assets.get('grounding_status', 'unknown')}` · "
            f"{len(assets.get('assets_used') or [])} asset(s) used · "
            f"{len(assets.get('invalid_assets') or [])} invalid"
        )
        st.markdown(
            f"- **Preview**: {'✅ ready' if preview.get('preview_ready') else '⚠️ not ready'} "
            f"(`{preview.get('preview_type', 'unknown')}`)"
        )
        export_label = "✅ ready" if export.get("zip_ready") else "⚠️ not ready"
        if export.get("zip_path"):
            export_label += f" · `{export['zip_path']}`"
        st.markdown(f"- **ZIP Export**: {export_label}")
        st.markdown(
            f"- **Durations**: total={_fmt_duration(durations.get('total_ms', 0))} · "
            f"model_call={_fmt_duration(durations.get('model_call_ms', 0))} · "
            f"validation={durations.get('validation_ms', 0)} ms · "
            f"repair={_fmt_duration(durations.get('repair_ms', 0))}"
        )

        if validator.get("hard_errors") or validator.get("warnings"):
            with st.expander("Validator details", expanded=False):
                st.write({"hard_errors": validator.get("hard_errors", []), "warnings": validator.get("warnings", [])})

        with st.expander("Raw Generation Report (JSON)", expanded=False):
            st.json(report)
    except Exception as exc:
        st.warning(f"Generation Report 渲染失败（不影响主流程）：{exc}")


def _render_phone(page_files: dict[str, str] | None) -> None:
    if not page_files:
        placeholder = """
            <div style="width:375px;height:680px;margin:0 auto;background:#171717;border-radius:46px;padding:12px 8px;box-shadow:0 20px 55px rgba(0,0,0,.22);box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Helvetica Neue','Segoe UI','Microsoft YaHei UI',sans-serif;">
              <div style="height:26px;color:#fff;font:600 11px -apple-system;display:flex;justify-content:space-between;align-items:center;padding:0 18px;">
                <span>9:41</span><span style="width:78px;height:13px;background:#050505;border-radius:8px;"></span><span>LTE</span>
              </div>
              <div style="height:628px;border-radius:36px;background:linear-gradient(180deg,#fbfaf6 0%,#f3f0e8 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:34px;box-sizing:border-box;color:#9b9a91;">
                <div style="width:54px;height:54px;border-radius:16px;background:#fff;display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 8px 22px rgba(20,20,20,.07);margin-bottom:18px;">📱</div>
                <div style="font-size:15px;font-weight:600;color:#5b5a52;margin-bottom:6px;">小程序预览将在这里呈现</div>
                <div style="font-size:12.5px;line-height:1.6;color:#a4a399;">在左侧描述需求并生成后<br/>真实页面会实时渲染于此</div>
              </div>
            </div>
            """
        b64 = base64.b64encode(placeholder.encode("utf-8")).decode("ascii")
        st.iframe(f"data:text/html;base64,{b64}", height=710)
        return
    try:
        html = render_phone_html(
            _safe_get(page_files, "wxml", ""),
            _safe_get(page_files, "wxss", ""),
            _safe_get(page_files, "js", ""),
            app_wxss=APP_WXSS,
            user_images=assets_to_preview_images(_safe_get(page_files, "assets", [])),
        )
        components.html(html, height=720, scrolling=True)
    except Exception as exc:
        st.error(f"Preview render failed: {exc}")


def _result_line_summary(page_files: dict | None) -> str:
    wxml_l = _line_count(_safe_get(page_files, "wxml", ""))
    wxss_l = _line_count(_safe_get(page_files, "wxss", ""))
    js_l = _line_count(_safe_get(page_files, "js", ""))
    return f"WXML {wxml_l} 行 · WXSS {wxss_l} 行 · JS {js_l} 行 · 共 {wxml_l + wxss_l + js_l} 行"


def _has_core_page_files(page_files: dict | None) -> bool:
    return bool(
        _safe_get(page_files, "wxml", "").strip()
        and _safe_get(page_files, "wxss", "").strip()
        and _safe_get(page_files, "js", "").strip()
    )


def _run_generation(
    prompt: str,
    mode: str = "agent",
    image_list: list | None = None,
    qa_pairs: list | None = None,
) -> None:
    img_list = image_list or []
    img_count = len(img_list)
    session_id = _new_session_id()
    recorder = TraceRecorder()
    recorder.add_step(
        "01_receive_requirement", "Receive Requirement", status="success",
        message=f"User requirement received ({len(prompt)} chars).",
        metadata={"prompt_length": len(prompt), "reference_images": img_count},
    )

    recorder.start("02_build_prompt", "Build Prompt Context")
    uploaded_assets = prepare_uploaded_assets(img_list)
    library_assets = select_image_assets(prompt, limit=8)
    if qa_pairs:
        built_prompt = build_enriched_prompt(
            prompt,
            qa_pairs,
            image_count=img_count,
            asset_list=uploaded_assets,
        )
    else:
        built_prompt = build_prompt(prompt, asset_list=uploaded_assets)
        if img_count == 1:
            built_prompt += "\n\n【多模态输入】用户上传了 1 张参考图片，请分析图片内容、配色和风格，在生成的代码中自然融入。"
        elif img_count > 1:
            built_prompt += f"\n\n【多模态输入】用户上传了 {img_count} 张参考图片，请逐一分析并自主决定每张的用途和放置位置。"
    recorder.end(
        "02_build_prompt", status="success",
        message="Prompt assembled with gemma_core prompt builder.",
        metadata={"prompt_chars": len(built_prompt), "library_assets": len(library_assets), "uploaded_assets": len(uploaded_assets)},
    )

    started = time.time()
    page_files = None
    validation = None
    repair_status = "skipped"
    repair_summary = "No repair needed / Not triggered"
    repair_before_count = 0
    used_fallback = False
    error = None
    exception_occurred = False
    mode_label = _MODE_DISPLAY.get(mode, mode)

    try:
        with st.status("🧠 Gemma 4 正在生成小程序页面...", expanded=True) as status:
            st.write(f"📡 正在以 **{mode_label}** 调用 `create_miniprogram_page`（预计 1-3 分钟，复杂页面可能更久）...")
            if img_count:
                st.write(f"🖼️ 已附加 {img_count} 张参考图片（多模态输入）")

            recorder.start("03_call_provider", "Call Gemma Provider", metadata={"requested_mode": mode})
            page_files = call_gemma_with_tools(built_prompt, image_list=img_list or None, mode=mode)
            recorder.end(
                "03_call_provider", status="success",
                message=f"Provider returned: {_actual_provider_label(page_files)}.",
                metadata={"provider": page_files.get("provider"), "fallback_used": bool(page_files.get("fallback_used"))},
            )
            page_files["assets"] = uploaded_assets
            page_files["library_assets"] = library_assets
            page_files = attach_assets_and_fallback(page_files, uploaded_assets, library_assets)

            parse_method = page_files.get("parse_method")
            tool_call_detected = parse_method in ("standard_tool_calls", "gemma_raw_tool_call")
            recorder.add_step(
                "04_parse_tool_call", "Parse Tool Call",
                status="success" if tool_call_detected else "warning",
                message=f"parse_method={parse_method or 'unknown'}",
                metadata={"parse_method": parse_method or "unknown", "tool_call_detected": tool_call_detected},
            )

            if page_files.get("fallback_used"):
                actual_label = _PROVIDER_DISPLAY.get(page_files.get("provider"), page_files.get("provider"))
                st.write(
                    f"🔁 你选择了「{mode_label}」，但本次自动切换到了 **{actual_label}** 兜底"
                    f"（原因：{page_files.get('fallback_reason', '原链路暂不可用')}）— 双后端互为主备，确保生成不中断"
                )
            st.write(f"✅ 模型返回成功 · {_result_line_summary(page_files)}")

            recorder.add_step(
                "05_generate_files", "Generate WXML / WXSS / JS",
                status="success" if _has_core_page_files(page_files) else "warning",
                message="WXML / WXSS / JS extracted." if _has_core_page_files(page_files) else "Some files are missing.",
                metadata={
                    "wxml_lines": _line_count(_safe_get(page_files, "wxml", "")),
                    "wxss_lines": _line_count(_safe_get(page_files, "wxss", "")),
                    "js_lines": _line_count(_safe_get(page_files, "js", "")),
                },
            )

            st.write("🔍 正在校验代码质量...")
            recorder.start("06_run_validator", "Run Static Validator")
            validation = validate_project(_validator_files(page_files), full_project=False)
            recorder.end(
                "06_run_validator",
                status="success" if validation.ok else "warning",
                message="Validator passed." if validation.ok else f"{len(validation.hard_errors)} hard error(s), {len(validation.warnings)} warning(s).",
                metadata={"hard_errors": len(validation.hard_errors), "warnings": len(validation.warnings)},
            )

            if validation.ok:
                st.write("✅ 代码通过静态校验")
                recorder.add_step("07_self_correction", "Self-Correction", status="skipped",
                                   message="No repair needed / Not triggered.")
            else:
                repair_status = "running"
                repair_summary = "Validator hard errors were sent back to Gemma for one repair pass"
                repair_before_count = len(validation.hard_errors)
                st.write(f"⚠️ 发现 {len(validation.hard_errors)} 个问题：{' · '.join(validation.hard_errors[:2])}{'...' if len(validation.hard_errors) > 2 else ''}")
                st.write("🔧 启动自愈，重新调用模型修复...")
                recorder.start("07_self_correction", "Self-Correction", metadata={"before_errors_count": repair_before_count})
                original_page_files = page_files
                original_validation = validation
                try:
                    repair_prompt = build_repair_prompt(prompt, page_files, validation.hard_errors)
                    repaired = call_gemma_with_tools(repair_prompt, mode=mode)
                    repaired["assets"] = uploaded_assets
                    repaired["library_assets"] = library_assets
                    repaired = attach_assets_and_fallback(repaired, uploaded_assets, library_assets)
                    repaired_validation = validate_project(_validator_files(repaired), full_project=False)
                    if repaired_validation.ok:
                        page_files = repaired
                        validation = repaired_validation
                        repair_status = "success"
                        repair_summary = "Repaired validator hard errors - code now passes"
                        st.write(f"✅ 自愈成功，代码通过校验 · {_result_line_summary(page_files)}")
                        recorder.end(
                            "07_self_correction", status="success", message=repair_summary,
                            metadata={"rounds": 1, "before_errors_count": repair_before_count, "after_errors_count": 0},
                        )
                    else:
                        repair_status = "warning"
                        if len(repaired_validation.hard_errors) <= len(original_validation.hard_errors):
                            page_files = repaired
                            validation = repaired_validation
                            kept = "repaired model output"
                        else:
                            page_files = original_page_files
                            validation = original_validation
                            kept = "original model output"
                        repair_summary = f"Repair attempted; still has validator issues - keeping {kept} instead of template fallback"
                        st.write("⚠️ 自愈后仍有问题，但已保留模型生成结果，避免回退成固定模板。")
                        recorder.end(
                            "07_self_correction", status="warning", message=repair_summary,
                            metadata={"rounds": 1, "before_errors_count": repair_before_count, "after_errors_count": len(validation.hard_errors)},
                        )
                except Exception:
                    repair_status = "warning"
                    repair_summary = "Repair call failed - keeping original model output instead of template fallback"
                    page_files = original_page_files
                    validation = original_validation
                    st.write("⚠️ 自愈调用失败，但已保留模型生成结果，避免回退成固定模板。")
                    recorder.end(
                        "07_self_correction", status="error", message=repair_summary,
                        metadata={"rounds": 1, "before_errors_count": repair_before_count, "after_errors_count": len(validation.hard_errors)},
                    )

            status.update(label="✅ 生成完成", state="complete")
    except Exception as exc:
        error = str(exc)
        exception_occurred = True
        repair_status = "skipped"
        repair_summary = "Main generation failed before repair — fell back to nearest golden example"
        st.warning(f"调用失败（{error}），已自动回退到最相近的黄金样例，确保演示链路不中断。")
        page_files = get_golden_example(prompt)
        page_files["assets"] = uploaded_assets
        page_files["library_assets"] = library_assets
        page_files = attach_assets_and_fallback(page_files, uploaded_assets, library_assets)
        validation = validate_project(_validator_files(page_files), full_project=False)
        used_fallback = True
        # Fill in any pipeline steps that never ran because the exception
        # happened before they were reached, so the trace always has 11 steps.
        for step_id, title in [
            ("03_call_provider", "Call Gemma Provider"),
            ("04_parse_tool_call", "Parse Tool Call"),
            ("05_generate_files", "Generate WXML / WXSS / JS"),
            ("06_run_validator", "Run Static Validator"),
            ("07_self_correction", "Self-Correction"),
        ]:
            if step_id not in [s["step_id"] for s in recorder.to_list()]:
                recorder.add_step(step_id, title, status="error", message=f"Skipped: {error}")
        error = None

    elapsed = time.time() - started
    if page_files:
        page_files = attach_assets_and_fallback(page_files, uploaded_assets, library_assets)
        validation = validate_project(_validator_files(page_files), full_project=False)
        st.session_state.page_files = page_files
        st.session_state.validation = validation or _blank_validation()
    st.session_state.used_fallback = used_fallback
    st.session_state.trace_data = _trace_after_generation(
        prompt=prompt,
        built_prompt=built_prompt,
        page_files=page_files,
        validation=validation,
        repair_status=repair_status,
        repair_summary=repair_summary,
        elapsed=elapsed,
        error=error,
        img_count=img_count,
    )
    st.session_state.last_prompt = prompt
    st.session_state.raw_debug = {
        "prompt_chars": len(prompt),
        "built_prompt_chars": len(built_prompt),
        "requested_mode": mode,
        "provider": _safe_get(page_files, "provider"),
        "parse_method": _safe_get(page_files, "parse_method"),
        "fallback_used": bool(_safe_get(page_files, "fallback_used") or used_fallback),
        "reference_images": img_count,
        "error": error,
        "validation": {
            "ok": bool(validation.ok) if validation else False,
            "hard_errors": getattr(validation, "hard_errors", []),
            "warnings": getattr(validation, "warnings", []),
        },
    }

    # ── 08: Asset grounding evidence ────────────────────────────────────────
    assets_used = []
    for asset in (page_files.get("assets") or []) + (page_files.get("library_assets") or []):
        assets_used.append(asset.get("wxml_path") or asset.get("path") or asset.get("name") or "unknown")
    grounding_status = "passed" if assets_used else "no_assets_used"
    recorder.add_step(
        "08_asset_grounding", "Asset Grounding / Image Library",
        status="success" if assets_used else "skipped",
        message=f"{len(assets_used)} asset(s) grounded." if assets_used else "No assets used in this generation.",
        metadata={"assets_used_count": len(assets_used), "grounding_status": grounding_status},
    )

    # ── 09: Web preview readiness ───────────────────────────────────────────
    has_code = _has_core_page_files(page_files)
    recorder.add_step(
        "09_render_preview", "Render Web Low-Fidelity Preview",
        status="success" if has_code else "warning",
        message="Preview ready." if has_code else "Preview unavailable (missing WXML/WXSS/JS).",
        metadata={"preview_type": "web_low_fidelity"},
    )

    # ── 10: ZIP export evidence (best-effort, never fails the main flow) ───
    zip_ready, zip_path, zip_error = False, "", ""
    try:
        zip_bytes = export_zip(page_files) if page_files else b""
        if zip_bytes:
            zip_file = LIVE_SESSION_DIR / f"{session_id}.zip"
            zip_file.write_bytes(zip_bytes)
            zip_ready = True
            zip_path = str(zip_file.relative_to(ROOT)).replace("\\", "/")
    except Exception as exc:
        zip_error = str(exc)
    recorder.add_step(
        "10_export_zip", "Export ZIP",
        status="success" if zip_ready else ("error" if zip_error else "skipped"),
        message="ZIP exported." if zip_ready else (zip_error or "ZIP not generated."),
        metadata={"zip_path": zip_path},
    )

    # ── 11: Generation Report assembly ──────────────────────────────────────
    provider = _safe_get(page_files, "provider")
    parse_method = _safe_get(page_files, "parse_method")
    durations = {"total_ms": int(elapsed * 1000), "model_call_ms": 0, "validation_ms": 0, "repair_ms": 0}
    for step in recorder.to_list():
        if step["step_id"] == "03_call_provider":
            durations["model_call_ms"] = step["duration_ms"]
        elif step["step_id"] == "06_run_validator":
            durations["validation_ms"] = step["duration_ms"]
        elif step["step_id"] == "07_self_correction":
            durations["repair_ms"] = step["duration_ms"]

    generation_report = build_generation_report(
        job_id=session_id,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        user_prompt=prompt,
        provider=provider,
        model=_MODEL_DISPLAY.get(provider, "unknown"),
        generation_mode="live",
        backend_mode=mode,
        tool_call_detected=parse_method in ("standard_tool_calls", "gemma_raw_tool_call"),
        parse_method=parse_method,
        files_generated={
            "wxml": bool(_safe_get(page_files, "wxml", "").strip()),
            "wxss": bool(_safe_get(page_files, "wxss", "").strip()),
            "js": bool(_safe_get(page_files, "js", "").strip()),
        },
        validator_result=normalize_validator_result(validation),
        repair_loop={
            "attempted": repair_status != "skipped",
            "success": (repair_status == "success") if repair_status != "skipped" else None,
            "rounds": 0 if repair_status == "skipped" else 1,
            "before_errors_count": repair_before_count,
            "after_errors_count": len(validation.hard_errors) if validation else 0,
        },
        assets={"assets_used": assets_used, "invalid_assets": [], "grounding_status": grounding_status},
        preview={"preview_ready": has_code, "preview_type": "web_low_fidelity"},
        export={"zip_ready": zip_ready, "zip_path": zip_path, **({"error": zip_error} if zip_error else {})},
        durations=durations,
        raw_status={"success": not exception_occurred, "error_message": error or ""},
    )
    recorder.add_step(
        "11_generation_report", "Generate Generation Report", status="success",
        message="Generation report assembled.", metadata={"job_id": session_id},
    )
    st.session_state.generation_report = generation_report
    st.session_state.agent_trace_steps = recorder.to_list()

    saved_session_id = _save_live_session(
        st.session_state.page_files,
        prompt=prompt,
        trace_data=st.session_state.trace_data,
        raw_debug=st.session_state.raw_debug,
        validation=st.session_state.validation,
        session_id=session_id,
        generation_report=generation_report,
        agent_trace_steps=st.session_state.agent_trace_steps,
        tool_calls={
            "name": "create_miniprogram_page",
            "tool_call_detected": parse_method in ("standard_tool_calls", "gemma_raw_tool_call"),
            "parse_method": parse_method or "unknown",
            "provider": provider or "unknown",
        },
    )
    if saved_session_id:
        st.session_state.current_session_id = saved_session_id
        st.session_state.raw_debug["saved_session_id"] = saved_session_id


st.set_page_config(page_title="MiniPilot Agent Live Demo", page_icon="MP", layout="wide")

st.markdown(
    """
<style>
  /* ====================== Design tokens ====================== */
  :root {
    --paper:#f6f5f1; --surface:#ffffff; --surface-soft:#fbfaf6;
    --ink:#15171a; --ink-soft:#4d525a; --muted:#888c92;
    --line:#e7e2d6; --line-soft:#f1eee5;
    --accent:#b8632f; --accent-strong:#8c4622; --accent-soft:#f8ede1;
    --green:#2f7d68; --green-soft:#e6f1ec;
    --red:#c23b54; --red-soft:#f8e9ec;
    --amber:#b08a2e; --amber-soft:#f5f0e1;
    /* Module-specific identity colours — each panel gets its own quiet hue,
       so the three-zone workspace reads as composed rather than monotone. */
    --zone-trace:#2c4a6e; --zone-trace-soft:#e8eef4; --zone-trace-strong:#1c3552;
    --zone-preview:#7c6a9c; --zone-preview-soft:#efecf4; --zone-preview-strong:#5e4f7a;
    --shadow-xs:0 1px 3px rgba(21,23,26,.045);
    --shadow-sm:0 6px 20px rgba(21,23,26,.055);
    --shadow-md:0 16px 44px rgba(21,23,26,.09);
    --shadow-lg:0 32px 88px rgba(21,23,26,.16);
    --r-sm:10px; --r-md:16px; --r-lg:24px;
    --ease:cubic-bezier(.22,.8,.25,1);
    --font:-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Helvetica Neue","Segoe UI","Microsoft YaHei UI","Microsoft YaHei",sans-serif;
  }

  /* ====================== Base canvas & type ====================== */
  html, body, .stApp { background:var(--paper) !important; color:var(--ink); }
  .stApp, .stApp * { font-family:var(--font); }
  [data-testid="stIconMaterial"], [data-testid^="stIcon"] { font-family:"Material Symbols Rounded" !important; }
  .block-container { max-width:1480px; padding:2.1rem 3rem 4rem; }
  [data-testid="stHeader"] { background:transparent; }
  [data-testid="stDivider"] hr, hr { border-color:var(--line) !important; margin:34px 0 !important; }
  h1,h2,h3,h4,h5,h6 { letter-spacing:-.012em; color:var(--ink); }
  ::selection { background:var(--accent-soft); color:var(--accent-strong); }
  ::-webkit-scrollbar { width:9px; height:9px; }
  ::-webkit-scrollbar-track { background:transparent; }
  ::-webkit-scrollbar-thumb { background:#dad5c8; border-radius:99px; }
  ::-webkit-scrollbar-thumb:hover { background:#c8c2b1; }

  /* ====================== Replace Streamlit's stock red/orange accent everywhere ====================== */
  a, a:visited, [data-testid="stMarkdownContainer"] a { color:var(--accent) !important; }
  a:hover { color:var(--accent-strong) !important; }
  label[data-baseweb="radio"]:has(input:checked) > div:first-child,
  label[data-baseweb="checkbox"]:has(input:checked) > div:first-child { background:var(--accent) !important; }
  label[data-baseweb="radio"] > div:first-child, label[data-baseweb="checkbox"] > div:first-child { background:#cdc8ba; }
  [data-testid="stSlider"] [role="slider"] { background:var(--accent) !important; border-color:var(--accent) !important; }
  [data-testid="stSlider"] > div > div > div > div { background:var(--accent) !important; }
  [data-baseweb="tab-highlight"] { background:var(--accent) !important; }
  [data-baseweb="tab-border"] { background:var(--line) !important; }
  button[data-baseweb="tab"] { color:var(--muted); font-weight:600; }
  button[data-baseweb="tab"][aria-selected="true"] { color:var(--ink); }
  [data-testid="stProgress"] > div > div > div { background:var(--accent) !important; }
  [data-testid="stSpinner"] svg { color:var(--accent) !important; }
  *:focus-visible { outline-color:var(--accent) !important; }
  .stTextArea textarea:focus, .stTextInput input:focus, .stNumberInput input:focus {
    border-color:var(--accent) !important; box-shadow:0 0 0 3px var(--accent-soft) !important;
  }
  [data-testid="stTextAreaRootElement"], [data-testid="stTextInputRootElement"] { border-color:var(--accent) !important; }
  [data-testid="stTextAreaRootElement"]:has(textarea:focus), [data-testid="stTextInputRootElement"]:has(input:focus) {
    box-shadow:0 0 0 3px var(--accent-soft) !important;
  }
  [data-testid="stFileUploaderDropzone"] { background:var(--surface-soft); border:1.5px dashed var(--line); border-radius:var(--r-md); }
  [data-testid="stFileUploaderDropzone"]:hover { border-color:var(--accent); }

  /* Alert boxes (st.info/warning/success/error) — replace stock yellow/blue/green/red with design tokens */
  [data-testid="stAlertContainer"] { border-radius:var(--r-md) !important; border:1px solid transparent !important; box-shadow:var(--shadow-xs); }
  [data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) { background:var(--accent-soft) !important; }
  [data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) * { color:var(--accent-strong) !important; fill:var(--accent-strong) !important; }
  [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) { background:var(--amber-soft) !important; }
  [data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) * { color:var(--amber) !important; fill:var(--amber) !important; }
  [data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) { background:var(--green-soft) !important; }
  [data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) * { color:var(--green) !important; fill:var(--green) !important; }
  [data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) { background:var(--red-soft) !important; }
  [data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) * { color:var(--red) !important; fill:var(--red) !important; }

  /* ====================== Buttons ====================== */
  div[data-testid="stButton"] > button, div[data-testid="stDownloadButton"] > button {
    border-radius:var(--r-sm); min-height:44px; font-weight:600; letter-spacing:.005em;
    border:1px solid var(--line); background:var(--surface); color:var(--ink-soft);
    transition:all .18s var(--ease);
  }
  div[data-testid="stButton"] > button:hover, div[data-testid="stDownloadButton"] > button:hover {
    border-color:var(--accent); color:var(--accent-strong); transform:translateY(-1px); box-shadow:var(--shadow-sm);
  }
  div[data-testid="stButton"] > button:active, div[data-testid="stDownloadButton"] > button:active { transform:translateY(0); }
  div[data-testid="stButton"] > button[kind="primary"], div[data-testid="stDownloadButton"] > button[kind="primary"] {
    background:var(--accent); border-color:var(--accent); color:#fff; box-shadow:0 8px 22px rgba(44,74,110,.28);
  }
  div[data-testid="stButton"] > button[kind="primary"]:hover, div[data-testid="stDownloadButton"] > button[kind="primary"]:hover {
    background:var(--accent-strong); border-color:var(--accent-strong); color:#fff;
    box-shadow:0 12px 30px rgba(44,74,110,.36); transform:translateY(-1px);
  }
  div[data-testid="stButton"] > button:disabled { opacity:.45; transform:none; box-shadow:none; }

  /* ====================== Header ====================== */
  .topbar { display:flex; justify-content:space-between; gap:26px; align-items:flex-end; border-bottom:1px solid var(--line); padding-bottom:30px; margin-bottom:38px; }
  .eyebrow { margin:0 0 14px; font-size:11.5px; font-weight:800; letter-spacing:.26em; text-transform:uppercase; color:var(--accent); }
  .title h1 { font-size:64px; font-weight:800; margin:0 0 16px; letter-spacing:-.035em; line-height:1.04; }
  .title h1 .accent-word { color:var(--accent); padding:0 .03em; }
  .title p { margin:0; color:var(--ink-soft); line-height:1.7; max-width:640px; font-size:15.5px; }
  .status-pills { display:flex; gap:9px; flex-wrap:wrap; justify-content:flex-end; }
  .pill { border:1px solid var(--line); border-radius:999px; padding:8px 14px; font-size:12px; font-weight:600; background:var(--surface); color:var(--ink-soft); box-shadow:var(--shadow-xs); }
  .pill b { color:var(--ink); font-weight:700; }
  .backlink { color:var(--accent) !important; text-decoration:none; font-weight:700; }
  .backlink:hover { color:var(--accent-strong) !important; }

  /* ====================== Panel headers ====================== */
  .panel-title { margin:0 0 16px; font-size:12.5px; font-weight:800; color:var(--ink); text-transform:uppercase; letter-spacing:.14em; display:flex; align-items:center; gap:9px; }
  .panel-title::before { content:""; width:7px; height:7px; border-radius:99px; background:var(--accent); display:inline-block; }
  .panel-title.zone-trace::before { background:var(--zone-trace); }
  .panel-title.zone-trace { color:var(--zone-trace-strong); }
  .panel-title.zone-preview::before { background:var(--zone-preview); }
  .panel-title.zone-preview { color:var(--zone-preview-strong); }

  /* ====================== Empty-state hero stage ====================== */
  .accent-word { color:var(--accent); }
  /* Compact example-prompt chips — quiet quick-fill suggestions, not a wall of buttons */
  .st-key-example_chips { gap:9px !important; margin:2px 0 22px; }
  .st-key-example_chips > div { width:auto !important; flex:0 0 auto !important; }
  .st-key-example_chips button {
    background:var(--surface) !important; border:1px solid var(--line) !important;
    border-radius:999px !important; padding:7px 20px !important; min-height:0 !important;
    font-size:13px !important; font-weight:600 !important; color:var(--ink-soft) !important;
    box-shadow:none !important; transition:border-color .15s ease, color .15s ease, background .15s ease;
  }
  .st-key-example_chips button:hover {
    border-color:var(--accent) !important; color:var(--accent-strong) !important; background:var(--accent-soft) !important;
  }
  .chip-label { font-size:12px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); margin:0 0 11px; }

  /* ====================== Step flow — vertical stepper (clarify journey) ====================== */
  .flow-steps { display:flex; flex-direction:column; gap:0; margin:6px 2px 18px; }
  .flow-step { display:flex; align-items:flex-start; gap:11px; padding:7px 0; position:relative; }
  .flow-step::before { content:""; position:absolute; left:11px; top:30px; width:1.5px; height:22px; background:var(--line); }
  .flow-step:last-child::before { display:none; }
  .flow-step b {
    flex:none; display:inline-flex; align-items:center; justify-content:center; width:23px; height:23px;
    border-radius:99px; background:var(--surface); border:1.5px solid var(--line); color:var(--muted);
    font-size:11px; font-weight:800; z-index:1;
  }
  .flow-step span { font-size:13px; font-weight:600; color:var(--muted); padding-top:2px; }
  .flow-step.is-active b { background:var(--accent); border-color:var(--accent); color:#fff; box-shadow:0 0 0 4px var(--accent-soft); }
  .flow-step.is-active span { color:var(--accent-strong); font-weight:700; }
  .flow-step.is-done b { background:var(--green); border-color:var(--green); color:#fff; font-size:12px; }
  .flow-step.is-done span { color:var(--ink-soft); }
  .flow-step.is-done::before { background:var(--green-soft); }

  /* ====================== Trace items — read like a running log, not a static list ====================== */
  .trace-list { position:relative; display:grid; gap:10px; padding-left:5px; }
  .trace-list::before {
    content:""; position:absolute; left:27px; top:24px; bottom:24px; width:2px;
    background:linear-gradient(180deg, var(--zone-trace-soft), var(--line) 85%); z-index:0;
  }
  .trace-item { position:relative; z-index:1; display:grid; grid-template-columns:46px minmax(0,1fr); gap:13px; background:var(--surface); border:1px solid var(--line); border-radius:var(--r-md); padding:14px 16px; box-shadow:var(--shadow-xs); transition:box-shadow .2s var(--ease), transform .2s var(--ease); }
  .trace-item:hover { box-shadow:var(--shadow-sm); transform:translateY(-1px); }
  .trace-badge { position:relative; z-index:1; height:28px; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#fff; font-size:10px; font-weight:800; letter-spacing:.04em; background:#9a9da3; box-shadow:0 0 0 4px var(--surface); }
  .trace-success .trace-badge { background:var(--green); }
  .trace-warning .trace-badge { background:var(--amber); }
  .trace-error .trace-badge { background:var(--red); }
  .trace-running .trace-badge { background:var(--zone-trace); animation:trace-pulse 1.6s ease-in-out infinite; }
  .trace-skipped .trace-badge { background:#b6b2a6; }
  @keyframes trace-pulse { 0%,100% { box-shadow:0 0 0 4px var(--surface); } 50% { box-shadow:0 0 0 4px var(--zone-trace-soft); } }
  .trace-item h4 { margin:0 0 4px; font-size:14.5px; font-weight:700; }
  .trace-item .trace-step { font-size:10.5px; font-weight:800; letter-spacing:.1em; color:var(--zone-trace); margin-right:7px; }
  .trace-item p { margin:0; color:var(--muted); font-size:13px; line-height:1.55; }
  .trace-metrics { display:flex; gap:6px; flex-wrap:wrap; margin-top:9px; }
  .trace-metrics span { border:1px solid var(--line-soft); border-radius:999px; padding:4px 9px; color:var(--ink-soft); font-size:11px; background:var(--surface-soft); font-weight:500; }
  .trace-metrics b { color:var(--ink); margin-right:4px; font-weight:700; }

  /* Phone preview gets a quiet plum-tinted stage so it reads as its own zone, not a bare iframe */
  .st-key-phone_frame {
    background:linear-gradient(165deg, var(--zone-preview-soft) 0%, var(--surface) 46%);
    border:1px solid var(--zone-preview-soft); border-radius:var(--r-lg);
    padding:22px 18px 16px; box-shadow:0 16px 40px -22px var(--zone-preview);
  }
  .st-key-phone_frame iframe { border-radius:30px; }

  /* ====================== Form controls & containers ====================== */
  .stTextArea textarea { border-radius:var(--r-sm); border-color:var(--line); background:var(--surface); font-size:14.5px; line-height:1.6; padding:14px 16px; }
  .stTextArea textarea::placeholder { color:#aba791; }
  [data-testid="stCaptionContainer"] { color:var(--muted) !important; }
  [data-testid="stExpander"] { border:1px solid var(--line); border-radius:var(--r-md); background:var(--surface); overflow:hidden; box-shadow:var(--shadow-xs); }
  [data-testid="stExpander"] summary { font-weight:600; }
  [data-testid="stTabs"] [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid var(--line); }
  button[data-baseweb="tab"] { padding:10px 18px; border-radius:8px 8px 0 0; }
  .stCodeBlock, pre { border-radius:var(--r-sm) !important; border:1px solid var(--line); }

  /* ====================== Clarify quiz card ====================== */
  .st-key-quiz_card { background:var(--surface) !important; border:1px solid var(--line); border-radius:var(--r-lg) !important; padding:22px 24px; box-shadow:var(--shadow-md); margin:6px 0 16px; }
  .quiz-head { font-size:14px; font-weight:700; color:var(--ink); margin:0 0 4px; }
  .quiz-sub { font-size:12.5px; color:var(--muted); margin:0 0 14px; }
  .quiz-q { font-size:14px; font-weight:700; color:var(--ink); margin:14px 0 6px; }

  @media (max-width: 1000px) {
    .topbar { display:block; }
    .status-pills { justify-content:flex-start; margin-top:14px; }
    .title h1 { font-size:30px; }
  }
</style>
""",
    unsafe_allow_html=True,
)

query_prompt = st.query_params.get("prompt", "")
if isinstance(query_prompt, list):
    query_prompt = query_prompt[0] if query_prompt else ""
query_prompt = unquote(query_prompt or "")

for _key, _default in [
    ("input_prompt", query_prompt),
    ("page_files", None),
    ("validation", None),  # filled lazily below (needs _blank_validation())
    ("trace_data", None),  # filled lazily below (needs input_prompt)
    ("raw_debug", {}),
    ("gen_mode", "agent"),        # agent | deep
    ("image_list", None),         # list of (bytes, mime_type) for multimodal input
    ("used_fallback", False),
    ("current_session_id", ""),
    ("_show_deploy", False),
    ("clarify_active", False),    # whether the AI 需求分析 quiz is currently shown
    ("clarify_questions", []),    # list of {q,a,b,c} dicts from CLARIFY_TEMPLATE
    ("clarify_ai_ok", True),      # whether the clarify call itself succeeded
    ("clarify_err", ""),
    ("_upload_cache_ids", None),  # tuple of uploaded file_ids already processed (avoids redundant reprocessing on rerun)
    ("_upload_cache_imgs", None), # cached (bytes, mime, name, size_mb) tuples for the above
    ("generation_report", None),  # structured evidence dict, see generation_report.py
    ("agent_trace_steps", []),    # 12-step pipeline trace, see agent_trace.py
    ("gen_source_mode", "live"),  # "live" | "replay"
    ("replay_loaded", False),     # True once a replay record has been loaded into session_state
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default
if st.session_state.validation is None:
    st.session_state.validation = _blank_validation()
if st.session_state.trace_data is None:
    st.session_state.trace_data = _empty_trace(st.session_state.input_prompt)


def _restore_session_payload(session_id: str, payload: dict) -> None:
    """Populate session_state from a saved live-session record (used by the
    Replay Verified Demo picker)."""
    st.session_state.page_files = payload.get("files")
    st.session_state.input_prompt = str(payload.get("prompt") or "")
    st.session_state.trace_data = (
        payload.get("trace_data")
        if isinstance(payload.get("trace_data"), list)
        else _empty_trace(st.session_state.input_prompt)
    )
    st.session_state.raw_debug = dict(payload.get("raw_debug") or {})
    st.session_state.validation = _validation_from_dict(
        payload.get("validation"),
        st.session_state.page_files,
    )
    st.session_state.generation_report = payload.get("generation_report") or None
    st.session_state.agent_trace_steps = (
        payload.get("agent_trace_steps") if isinstance(payload.get("agent_trace_steps"), list) else []
    )
    st.session_state.used_fallback = bool(st.session_state.raw_debug.get("fallback_used"))
    st.session_state.current_session_id = session_id
    st.session_state.raw_debug["restored_session"] = session_id


st.markdown(
    f"""
<div class="topbar">
  <div class="title">
    <p class="eyebrow">MiniPilot Agent · Live MVP Generator</p>
    <h1>从<span class="accent-word">一句生意需求</span>到小程序 MVP</h1>
    <p>{PRODUCT_TAGLINE} {POWERED_BY} 描述你的商家需求，Gemma 4 会先与你确认关键细节，再生成可预览、可下载的小程序页面代码。</p>
  </div>
  <div class="status-pills">
    <span class="pill">Backends&nbsp;<b>{_configured_backends_label()}</b></span>
    <span class="pill">●&nbsp;Live Generation</span>
    <span class="pill"><a class="backlink" href="{SHOWCASE_URL}" target="_self">← Back to Showcase</a></span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


def _render_mode_selector() -> None:
    """Live Mode (calls the real Gemma provider) vs Replay Verified Demo
    (loads a previously saved real run, no model call)."""
    choice = st.radio(
        "Generation Mode",
        options=["live", "replay"],
        format_func=lambda v: "⚡ Live Mode（调用真实 Gemma Provider）" if v == "live" else "🔁 Replay Verified Demo（加载已保存的真实生成记录）",
        index=["live", "replay"].index(st.session_state.gen_source_mode),
        horizontal=True,
        key="_gen_source_mode_radio",
    )
    if choice != st.session_state.gen_source_mode:
        st.session_state.gen_source_mode = choice
        if choice == "live":
            st.session_state.replay_loaded = False

    if st.session_state.gen_source_mode != "replay":
        return

    sessions = _load_session_index()
    if not sessions:
        st.info("还没有保存过任何真实生成记录。请先在 Live Mode 下生成一次，再回到 Replay Verified Demo。")
        return

    options = [str(item.get("session_id")) for item in sessions if item.get("session_id")]
    pick_col, btn_col = st.columns([3, 1])
    with pick_col:
        selected = st.selectbox(
            "选择一条已保存的真实生成记录",
            options,
            format_func=lambda value: _session_label(
                next((item for item in sessions if item.get("session_id") == value), {"session_id": value})
            ),
            label_visibility="collapsed",
            key="_replay_picker",
        )
    with btn_col:
        load_clicked = st.button("▶️ 加载 Replay 记录", type="primary", use_container_width=True, key="_load_replay_btn")

    if load_clicked:
        payload = _load_live_session(selected)
        if isinstance(payload, dict) and isinstance(payload.get("files"), dict):
            _restore_session_payload(selected, payload)
            st.session_state.replay_loaded = True
            st.rerun()
        else:
            st.warning(f"该记录已损坏或缺失，已跳过：{selected}")

    if st.session_state.replay_loaded:
        st.success(
            "🔁 **Replay Verified Demo** — Loaded from a previously generated real run. "
            "No model call is executed in this mode."
        )


_render_provider_status()
_render_mode_selector()


def _render_input_panel(*, spacious: bool = False) -> None:
    prompt = st.text_area(
        "自然语言需求",
        key="input_prompt",
        height=240 if spacious else 170,
        placeholder="例如：生成一个咖啡店点单小程序页面，包含门店封面、分类 Tab、商品列表、购物车和底部结算栏。",
    )
    st.markdown('<p class="chip-label">没有思路？试试这些</p>', unsafe_allow_html=True)
    chip_row = st.container(key="example_chips", horizontal=True, gap="small")
    for idx, (label, ex_prompt) in enumerate(_example_prompts()):
        chip_row.button(
            label,
            key=f"example_{idx}",
            on_click=_set_prompt,
            args=(ex_prompt,),
        )

    st.caption("⚙️ 生成模式")
    _mode_keys = list(_MODE_OPTIONS.keys())
    _amd_health = _cached_amd_health()
    if not _amd_health.get("ok") and "deep" in _mode_keys:
        _mode_keys.remove("deep")
        if st.session_state.gen_mode == "deep":
            st.session_state.gen_mode = "agent"
    _mode_choice = st.radio(
        "选择本次生成使用的后端",
        options=_mode_keys,
        format_func=lambda k: _MODE_OPTIONS[k],
        index=_mode_keys.index(st.session_state.gen_mode),
        horizontal=True,
        label_visibility="collapsed",
        key="_gen_mode_radio",
    )
    st.session_state.gen_mode = _mode_choice
    if _mode_choice == "agent":
        st.caption("优先使用 Google 官方托管的 Gemma 4；若暂不可用会自动切换到 AMD vLLM 兜底，并在结果中如实标注。")
    else:
        st.caption("优先使用自托管的 Gemma 31B（更长上下文、更长输出）；若网关暂不可用会自动切换到 Google AI Studio 兜底，并在结果中如实标注。")
    if not _amd_health.get("ok"):
        st.caption(f"🔬 AMD Deep Generation Mode is offline ({_amd_health['reason']}). Please use Google Stable Agent Mode or Replay Demo.")

    with st.expander("🖼️ 上传参考图片（可选 · 多模态）", expanded=False):
        st.caption("上传设计稿、产品图、竞品截图等，Gemma 4 多模态自动决策用途")
        MAX_IMGS, MAX_MB = 20, 8.0
        uploaded_files = st.file_uploader(
            f"支持 JPG / PNG / WebP / GIF / BMP（最多 {MAX_IMGS} 张，每张 ≤ {int(MAX_MB)} MB）",
            type=["jpg", "jpeg", "png", "webp", "gif", "bmp"],
            accept_multiple_files=True,
            key="multi_img_upload",
            label_visibility="collapsed",
        )
        if uploaded_files:
            # Pixel-level crop detection in preprocess_uploaded_image is expensive (full
            # width*height Python loops per image). Streamlit reruns this whole script on
            # every widget interaction — e.g. each clarify-quiz click — so without caching,
            # uploading a few photos made the page reprocess them from scratch on every
            # click and froze the UI long enough to look like a crash ("白屏").
            _upload_ids = tuple(uf.file_id for uf in uploaded_files[:MAX_IMGS])
            if st.session_state.get("_upload_cache_ids") != _upload_ids:
                valid_imgs = []
                for uf in uploaded_files[:MAX_IMGS]:
                    raw = uf.getvalue()
                    size_mb = len(raw) / 1024 / 1024
                    if size_mb > MAX_MB:
                        st.warning(f"⚠️ {uf.name} ({size_mb:.1f} MB) 超过 {int(MAX_MB)} MB，已跳过")
                    else:
                        mime = uf.type or "image/jpeg"
                        raw, mime, _meta = preprocess_uploaded_image(raw, mime)
                        valid_imgs.append((raw, mime, uf.name, size_mb))
                st.session_state._upload_cache_ids = _upload_ids
                st.session_state._upload_cache_imgs = valid_imgs
                if valid_imgs:
                    st.session_state.image_list = [(d, m) for d, m, _, _ in valid_imgs]
            valid_imgs = st.session_state.get("_upload_cache_imgs") or []
            if valid_imgs:
                cols = st.columns(min(len(valid_imgs), 4))
                for col, (raw, mime, name, size_mb) in zip(cols, valid_imgs[:4]):
                    col.image(raw, caption=f"{name[:12]}\n{size_mb:.1f} MB", use_container_width=True)
                if len(valid_imgs) > 4:
                    st.caption(f"+ {len(valid_imgs) - 4} 张（共 {len(valid_imgs)} 张）")
                st.caption(f"✅ 已加载 {len(valid_imgs)} 张参考图片，Gemma 4 将分析每张图片并自主决定使用位置")
        elif st.session_state.get("image_list"):
            n = len(st.session_state.image_list)
            st.info(f"已有 {n} 张参考图片（本次已清除，重新上传可替换）")
            st.session_state.image_list = None

    _has_prompt = bool(prompt.strip())
    _quiz_open = st.session_state.clarify_active and st.session_state.clarify_questions
    _s1_cls, _s1_badge = ("is-done", "✓") if _has_prompt else ("is-active", "1")
    if not _has_prompt:
        _s2_cls, _s2_badge = "", "2"
    elif _quiz_open:
        _s2_cls, _s2_badge = "is-active", "2"
    else:
        _s2_cls, _s2_badge = "", "2"
    _s3_cls, _s3_badge = ("is-active", "3") if (_quiz_open or (_has_prompt and not _quiz_open)) else ("", "3")
    st.markdown(
        f"""
        <div class="flow-steps">
          <div class="flow-step {_s1_cls}"><b>{_s1_badge}</b><span>描述你的小程序需求</span></div>
          <div class="flow-step {_s2_cls}"><b>{_s2_badge}</b><span>AI 澄清确认（可选，更精准）</span></div>
          <div class="flow-step {_s3_cls}"><b>{_s3_badge}</b><span>生成小程序代码并预览</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _is_replay_mode = st.session_state.gen_source_mode == "replay"

    c1, c2, c3 = st.columns([1.3, 1, 0.7])
    analyze_clicked = c1.button(
        "🔍 AI 需求分析",
        use_container_width=True,
        disabled=not prompt.strip() or _is_replay_mode,
        help="Gemma 4（26B，轻量快速）先理解需求、提几个关键问题，帮你生成更精准的代码",
    )
    generate_clicked = c2.button(
        "⚡ 快速生成",
        type="primary",
        use_container_width=True,
        disabled=not prompt.strip() or _is_replay_mode,
    )
    c3.button("Clear", use_container_width=True, on_click=_clear_prompt)
    if _is_replay_mode:
        st.caption("🔁 Replay Verified Demo 模式下不会调用模型，请切换到 Live Mode 以重新生成。")

    if analyze_clicked:
        with st.spinner("Gemma 4 正在理解您的需求..."):
            try:
                clarify_prompt = CLARIFY_TEMPLATE.format(user_input=prompt.strip())
                img_list_for_clarify = st.session_state.get("image_list") or []
                first_img = img_list_for_clarify[0] if img_list_for_clarify else None
                raw = call_gemma_text(
                    clarify_prompt,
                    image_data=first_img[0] if first_img else None,
                    image_mime=first_img[1] if first_img else "image/jpeg",
                )
                st.session_state.clarify_questions = parse_clarify_questions(raw)
                st.session_state.clarify_ai_ok = True
            except Exception as e:
                from prompt_builder import _DEFAULT_CLARIFY_QUESTIONS
                st.session_state.clarify_questions = [q.copy() for q in _DEFAULT_CLARIFY_QUESTIONS]
                st.session_state.clarify_ai_ok = False
                st.session_state.clarify_err = str(e)
        st.session_state.clarify_active = True
        st.rerun()

    if generate_clicked:
        st.session_state.clarify_active = False
        if not _block_if_amd_unavailable(st.session_state.gen_mode):
            _run_generation(prompt.strip(), mode=st.session_state.gen_mode, image_list=st.session_state.get("image_list"))
            st.rerun()

    if st.session_state.clarify_active and st.session_state.clarify_questions:
        quiz_box = st.container(key="quiz_card")
        with quiz_box:
            st.markdown('<p class="quiz-head">🤔 Gemma 4 需求澄清</p>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="quiz-sub">基于「{prompt.strip()[:42]}」生成的关键问题 —— 选择最贴近你想法的选项，'
                f'答案会自动并入生成提示词，让结果更贴合你的真实需求。</p>',
                unsafe_allow_html=True,
            )
            if not st.session_state.clarify_ai_ok:
                st.warning(f"⚠️ AI 分析暂时不可用（{st.session_state.clarify_err}），以下为通用参考问题，可直接点「生成代码」。")

            qa_pairs = []
            for i, q_data in enumerate(st.session_state.clarify_questions):
                st.markdown(f'<p class="quiz-q">Q{i+1}. {q_data["q"]}</p>', unsafe_allow_html=True)
                options = [f"A  {q_data['a']}", f"B  {q_data['b']}", f"C  {q_data['c']}", "D  其他（自定义输入）"]
                choice = st.radio(
                    label=f"demo_q{i}", options=options, key=f"demo_q{i}_radio",
                    horizontal=True, label_visibility="collapsed", index=None,
                )
                answer_text = ""
                if choice is not None:
                    if choice.startswith("A"):
                        answer_text = q_data["a"]
                    elif choice.startswith("B"):
                        answer_text = q_data["b"]
                    elif choice.startswith("C"):
                        answer_text = q_data["c"]
                    elif choice.startswith("D"):
                        answer_text = st.text_input(
                            "自定义内容", key=f"demo_q{i}_custom",
                            placeholder="描述你的具体要求...", label_visibility="collapsed",
                        )
                qa_pairs.append((q_data["q"], answer_text))

            answered_count = sum(1 for _, a in qa_pairs if a)
            qa_col1, qa_col2 = st.columns(2)
            confirm_clicked = qa_col1.button(
                f"🚀 生成代码{f'（已选 {answered_count}/{len(qa_pairs)} 题）' if answered_count else ''}",
                type="primary", use_container_width=True, key="_qa_confirm_btn",
            )
            cancel_clicked = qa_col2.button("← 取消分析", use_container_width=True, key="_qa_cancel_btn")
        if cancel_clicked:
            st.session_state.clarify_active = False
            st.rerun()
        if confirm_clicked:
            st.session_state.clarify_active = False
            if not _block_if_amd_unavailable(st.session_state.gen_mode):
                _run_generation(
                    prompt.strip(), mode=st.session_state.gen_mode,
                    image_list=st.session_state.get("image_list"), qa_pairs=qa_pairs,
                )
                st.rerun()

_has_results = bool(st.session_state.page_files)

if not _has_results:
    # Empty state: the prompt is the only thing that matters — give it the whole stage,
    # centered and generously spaced, instead of crowding it next to two empty placeholder panels.
    _, hero_col, _ = st.columns([0.16, 1, 0.16])
    with hero_col:
        _render_input_panel(spacious=True)
else:
    # Result state: the brief has done its job — let it recede into a narrow rail,
    # and give the work it produced (trace + live preview) the visual weight instead.
    left, middle, right = st.columns([0.74, 1.13, 1.13], gap="large")
    with left:
        st.markdown('<h3 class="panel-title">Brief</h3>', unsafe_allow_html=True)
        _render_input_panel()
    with middle:
        st.markdown('<h3 class="panel-title zone-trace">Gemma Agent Trace</h3>', unsafe_allow_html=True)
        render_agent_trace(st.session_state.trace_data)
        _render_detailed_trace(st.session_state.agent_trace_steps)
    with right:
        st.markdown('<h3 class="panel-title zone-preview">Phone Preview</h3>', unsafe_allow_html=True)
        with st.container(key="phone_frame"):
            _render_phone(st.session_state.page_files)

st.divider()

page_files = st.session_state.page_files or {}
validation = st.session_state.validation or _blank_validation()

st.markdown('<h3 class="panel-title">Generated Source</h3>', unsafe_allow_html=True)
tabs = st.tabs(["Source Code", "Validator", "Debug", "Generation Report"])
with tabs[0]:
    # st.tabs renders every tab's content into the DOM at once (only visibility
    # toggles client-side) — with generations now running ~1000-1800 lines,
    # syntax-highlighting three such blocks simultaneously was heavy enough to
    # freeze/crash the browser tab. A single radio-driven view renders exactly
    # one code block per rerun instead of three.
    _src_lang = {"WXML": "html", "WXSS": "css", "JS": "javascript"}
    _src_key = {"WXML": "wxml", "WXSS": "wxss", "JS": "js"}
    _src_choice = st.radio(
        "选择查看的文件", list(_src_lang.keys()),
        horizontal=True, label_visibility="collapsed", key="_src_file_choice",
    )
    _src_text = _safe_get(page_files, _src_key[_src_choice], "")
    st.caption(f"{_src_choice} · {_line_count(_src_text)} 行")
    st.code(_src_text, language=_src_lang[_src_choice], height=520)
with tabs[1]:
    if page_files:
        if validation.ok:
            st.success("Validator passed: no hard errors.")
        else:
            st.warning("Validator reported issues.")
        st.write({"hard_errors": validation.hard_errors, "warnings": validation.warnings})
    else:
        st.info("Generate once to see validator results.")
with tabs[2]:
    with st.expander("Trace data", expanded=True):
        st.json(st.session_state.trace_data)
    with st.expander("Parse / provider info", expanded=False):
        st.json(st.session_state.raw_debug)
    with st.expander("Recent gemma.log", expanded=False):
        if LOG_PATH.exists():
            lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
            st.code("\n".join(lines[-80:]), language="text")
        else:
            st.caption("No demo_cache/gemma.log yet.")
with tabs[3]:
    _render_generation_report(st.session_state.generation_report)

if page_files:
    st.caption(f"📊 代码量：{_result_line_summary(page_files)}")
    _session_id = _safe_session_id(st.session_state.get("current_session_id"))
    if _session_id:
        st.caption(f"🔖 Session: `{_session_id}` · 可在 Replay Verified Demo 中重新加载此记录")

    _provider = page_files.get("provider")
    _parse_method = page_files.get("parse_method")
    if _provider or _parse_method:
        _method_label = _PARSE_METHOD_DISPLAY.get(_parse_method, _parse_method)
        _fallback_note = ""
        if page_files.get("fallback_used"):
            _requested_label = _MODE_DISPLAY.get(page_files.get("requested_mode"), page_files.get("requested_mode"))
            _fallback_note = (
                f" · ⚠️ 你选择的是「{_requested_label}」，本次自动切换到了上述后端兜底"
                f"（{page_files.get('fallback_reason', '原链路暂不可用')}）"
            )
        st.caption(f"🔌 Provider: {_actual_provider_label(page_files)} · Parse Method: {_method_label}{_fallback_note}")
    elif st.session_state.get("used_fallback"):
        st.caption("🔌 Provider: 黄金样例兜底（模型调用未成功，已自动展示最接近的预置范例以保障演示连续性）")

    zip_bytes = export_zip(page_files)
    dl_col, deploy_col = st.columns(2)
    with dl_col:
        st.download_button(
            label="📦 下载小程序 ZIP",
            data=zip_bytes,
            file_name="gemma_match_miniprogram.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )
    with deploy_col:
        if st.button("📱 上传到微信预览", use_container_width=True, help="需要 AppID + 私钥"):
            st.session_state["_show_deploy"] = True

    # WeChat CI deploy — shown when user clicks the button above
    if st.session_state.get("_show_deploy"):
        st.subheader("📱 上传到微信预览")
        from ci_deployer import deploy_to_wechat, load_deploy_config, save_deploy_config, clear_deploy_config, get_local_preview_summary
        _saved_cfg = load_deploy_config()
        _preview_summary = get_local_preview_summary()
        st.caption(
            f"本机今天看起来成功生成的预览二维码：{_preview_summary['successful_qr_files']} 个 "
            f"(全部 preview.jpg：{_preview_summary['all_qr_files']} 个)。日志目录：`{_preview_summary['log_dir']}`"
        )
        _robot = st.number_input(
            "微信 CI robot",
            min_value=1,
            max_value=30,
            value=1,
            step=1,
            help="miniprogram-ci 支持 1-30 号 robot。若遇到频率/次数限制，可换一个 robot 试一次；如果 AppID 总限额满了，换 robot 也不会恢复。",
            key="_demo_deploy_robot",
        )

        if _saved_cfg:
            st.info(f"已保存凭证 · AppID: `{_saved_cfg['appid']}`")
            _col_deploy, _col_clear = st.columns([4, 1])
            with _col_deploy:
                _do_deploy = st.button("🔳 一键生成微信预览二维码", type="primary", use_container_width=True, key="_demo_deploy_btn")
            with _col_clear:
                if st.button("清除凭证", use_container_width=True, key="_demo_clear_cfg_btn"):
                    clear_deploy_config()
                    st.rerun()
            if _do_deploy:
                with st.spinner("正在上传到微信服务器..."):
                    try:
                        qr_path = deploy_to_wechat(page_files, _saved_cfg["appid"], _saved_cfg["private_key"], robot=int(_robot))
                        st.success("✅ 预览二维码生成成功！用微信扫码即可在手机上预览。")
                        st.image(qr_path, width=240)
                    except Exception as e:
                        st.error(str(e))
        else:
            wechat_appid = st.text_input("AppID", placeholder="wxxxxxxxxxxxxxxxe", key="_demo_deploy_appid")
            wechat_key = st.text_area(
                "私钥内容（粘贴 private.xxx.key 文件内容）",
                height=120,
                placeholder="-----BEGIN RSA PRIVATE KEY-----\n...",
                key="_demo_deploy_key",
            )
            _remember = st.checkbox("记住凭证（下次一键部署，凭证保存在本地，不会上传）", value=True, key="_demo_deploy_remember")
            if st.button("🔳 生成微信预览二维码", type="primary", use_container_width=True, key="_demo_deploy_submit"):
                if not wechat_appid.strip():
                    st.error("请填写 AppID")
                elif not wechat_key.strip():
                    st.error("请粘贴私钥内容")
                else:
                    with st.spinner("正在上传到微信服务器..."):
                        try:
                            qr_path = deploy_to_wechat(page_files, wechat_appid.strip(), wechat_key.strip(), robot=int(_robot))
                            if _remember:
                                save_deploy_config(wechat_appid.strip(), wechat_key.strip())
                                st.success("✅ 预览二维码生成成功！凭证已保存，下次一键部署。")
                            else:
                                st.success("✅ 预览二维码生成成功！用微信扫码即可在手机上预览。")
                            st.image(qr_path, width=240)
                        except Exception as e:
                            st.error(str(e))

st.caption(f"{PRODUCT_FULL_NAME}  /  Live Demo: {DEMO_URL}  /  Showcase: {SHOWCASE_URL}")
