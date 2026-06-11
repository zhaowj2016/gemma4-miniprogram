#!/usr/bin/env python
"""
Manual AMD vLLM gateway health check.

Run on the AMD terminal (against the local vLLM server) or on your local
machine (against an SSH-tunneled / DSW-proxied URL):

    AMD_VLLM_BASE_URL=http://127.0.0.1:8000 \
    AMD_VLLM_MODEL=gemma31b \
    python scripts/amd/check_amd_health.py

Optional env vars:
    DSW_GATEWAY_COOKIE   - sent as the "Cookie" header (only needed when going
                           through an Aliyun DSW proxy)

Defaults to AMD_VLLM_BASE_URL=http://127.0.0.1:8000 when unset, matching the
AMD terminal's existing fixed startup flow (kept here only as a reference -
do not assume every environment uses this exact path):

    /mnt/workspace/restart_gemma4_vllm.sh
    tail -f /mnt/workspace/vllm_output.log
    curl -s http://127.0.0.1:8000/v1/models
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request


def main() -> int:
    base_url = os.environ.get("AMD_VLLM_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    model = os.environ.get("AMD_VLLM_MODEL", "")
    cookie = os.environ.get("DSW_GATEWAY_COOKIE", "")

    headers = {}
    if cookie:
        headers["Cookie"] = cookie

    url = f"{base_url}/v1/models"
    result = {"ok": False, "status": "error", "latency": None, "model": model or None, "reason": ""}

    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read()
        result["latency"] = round(time.monotonic() - t0, 3)
        # A 200 status alone isn't enough — a stale DSW cookie returns an HTML
        # login/redirect page with HTTP 200, which would otherwise look "online".
        try:
            data = json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            data = None
        if not isinstance(data, dict) or "data" not in data:
            result["status"] = "error"
            result["reason"] = "HTTP 200 but response is not JSON / not an OpenAI /v1/models payload (stale DSW_GATEWAY_COOKIE / wrong proxy path?)"
        else:
            available = [item.get("id") for item in data.get("data", [])]
            result["reason"] = f"models available: {available}"
            result["ok"] = True
            result["status"] = "online"
    except urllib.error.HTTPError as exc:
        result["latency"] = round(time.monotonic() - t0, 3)
        result["status"] = "error"
        result["reason"] = f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:200]}"
    except Exception as exc:
        result["latency"] = round(time.monotonic() - t0, 3)
        result["status"] = "offline"
        result["reason"] = str(exc)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
