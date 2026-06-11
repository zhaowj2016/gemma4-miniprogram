"""
Lightweight, side-effect-free health checks for the three Generation Providers
(Replay / Google AI Studio / AMD vLLM self-hosted).

Each check_*_health() returns a small dict:
    {"ok": bool, "provider": str, "status": "online"|"offline"|"missing_config"|"error",
     "reason": str, "latency": float | None}

Design notes:
  - No network call ever blocks more than a few seconds (AMD health uses a
    3-5s timeout; Google/Replay checks are local-only, no network call).
  - Config is read from st.secrets (if available) first, then environment
    variables, then (for AMD) gemma_client's existing local config file —
    so this stays consistent with whatever call_gemma_with_tools() actually
    uses at generation time.
  - Never raises. A missing/invalid config or a network failure is reported
    as a normal status value, not an exception.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _get_setting(name: str, default: str | None = None) -> str | None:
    """st.secrets (if present) > environment variable > default."""
    try:
        import streamlit as st
        if name in st.secrets:
            value = st.secrets[name]
            if value is not None:
                return str(value)
    except Exception:
        pass
    return os.environ.get(name, default)


def _is_falsy_flag(value: str | None) -> bool:
    return (value or "").strip().lower() in ("0", "false", "no", "off")


def check_replay_health() -> dict:
    """Replay Verified Demo is "online" when at least one saved live session exists."""
    if _is_falsy_flag(_get_setting("ENABLE_REPLAY_MODE")):
        return {"ok": False, "provider": "replay", "status": "missing_config",
                "reason": "ENABLE_REPLAY_MODE is disabled", "latency": None}

    index_path = ROOT / "demo_cache" / "live_sessions" / "index.json"
    if not index_path.exists():
        return {"ok": False, "provider": "replay", "status": "missing_config",
                "reason": "No saved replay records found", "latency": None}
    try:
        records = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "provider": "replay", "status": "error",
                "reason": f"index.json unreadable: {exc}", "latency": None}

    if isinstance(records, list) and records:
        return {"ok": True, "provider": "replay", "status": "online",
                "reason": f"{len(records)} saved record(s)", "latency": None}
    return {"ok": False, "provider": "replay", "status": "missing_config",
            "reason": "No saved replay records found", "latency": None}


def check_google_health() -> dict:
    """Google AI Studio is "online" when an API key is configured.

    No network call is made — this only checks whether the key the rest of
    the app would actually use (gemma_client._get_api_key) is present.
    """
    if _is_falsy_flag(_get_setting("ENABLE_LIVE_GENERATION")):
        return {"ok": False, "provider": "google", "status": "missing_config",
                "reason": "ENABLE_LIVE_GENERATION is disabled", "latency": None}

    api_key = (
        _get_setting("GOOGLE_API_KEY")
        or _get_setting("GEMINI_API_KEY")
        or _get_setting("GEMMA_API_KEY")
    )
    if not api_key:
        try:
            from gemma_client import _get_api_key
            api_key = _get_api_key()
        except Exception:
            api_key = None

    if api_key:
        return {"ok": True, "provider": "google", "status": "online",
                "reason": "API key configured", "latency": None}
    return {"ok": False, "provider": "google", "status": "missing_config",
            "reason": "No GOOGLE_API_KEY / GEMINI_API_KEY configured", "latency": None}


def _resolve_amd_config() -> dict | None:
    """env / st.secrets first, falling back to gemma_client's local config file
    so the health check reflects the same config the generation path uses."""
    base_url = _get_setting("AMD_VLLM_BASE_URL")
    model = _get_setting("AMD_VLLM_MODEL")
    cookie = _get_setting("DSW_GATEWAY_COOKIE")

    if not base_url:
        try:
            from gemma_client import _load_amd_vllm_config
            file_cfg = _load_amd_vllm_config()
        except Exception:
            file_cfg = None
        if file_cfg:
            base_url = base_url or file_cfg.get("base_url")
            model = model or file_cfg.get("model")
            cookie = cookie or file_cfg.get("cookie")

    if not base_url:
        return None
    return {
        "base_url": base_url.rstrip("/"),
        "model": model or "unknown",
        "cookie": cookie,
    }


def check_amd_health(timeout: float = 4.0) -> dict:
    """GET {AMD_VLLM_BASE_URL}/v1/models with a short timeout. Never raises."""
    if _is_falsy_flag(_get_setting("ENABLE_AMD_VLLM")):
        return {"ok": False, "provider": "amd_vllm", "status": "missing_config",
                "reason": "ENABLE_AMD_VLLM is disabled", "latency": None}

    cfg = _resolve_amd_config()
    if not cfg:
        return {"ok": False, "provider": "amd_vllm", "status": "missing_config",
                "reason": "AMD_VLLM_BASE_URL not configured", "latency": None}

    url = f"{cfg['base_url']}/v1/models"
    headers = {"Cookie": cfg["cookie"]} if cfg.get("cookie") else {}

    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        latency = round(time.monotonic() - t0, 3)
        # A 200 status alone isn't enough — a stale DSW cookie returns an HTML
        # login/redirect page with HTTP 200, which would otherwise look "online".
        try:
            data = json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            return {"ok": False, "provider": "amd_vllm", "status": "error",
                    "reason": "HTTP 200 but response is not JSON (stale DSW_GATEWAY_COOKIE / wrong proxy path?)",
                    "latency": latency}
        if not isinstance(data, dict) or "data" not in data:
            return {"ok": False, "provider": "amd_vllm", "status": "error",
                    "reason": "HTTP 200 but response is not an OpenAI /v1/models payload",
                    "latency": latency}
        return {"ok": True, "provider": "amd_vllm", "status": "online",
                "reason": f"model={cfg['model']}", "latency": latency}
    except urllib.error.HTTPError as exc:
        latency = round(time.monotonic() - t0, 3)
        return {"ok": False, "provider": "amd_vllm", "status": "error",
                "reason": f"HTTP {exc.code}", "latency": latency}
    except Exception as exc:
        latency = round(time.monotonic() - t0, 3)
        return {"ok": False, "provider": "amd_vllm", "status": "offline",
                "reason": str(exc), "latency": latency}
