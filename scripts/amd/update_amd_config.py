#!/usr/bin/env python
"""
Interactive helper to refresh the local AMD vLLM config after a ModelScope /
Aliyun PAI-DSW instance restart.

Usage:
    python scripts/amd/update_amd_config.py

Workflow:
  1. Prompts for the new DSW instance ID (e.g. "dsw-1968466" or just
     "1968466"). This is the only thing that changes most of the time.
  2. Rewrites AMD_VLLM_BASE_URL with the new instance ID, keeping the
     existing Cookie, and runs a health check.
  3. If that already comes back online, you're done - the existing Cookie
     is an Aliyun login-session cookie and is NOT tied to a specific
     instance ID, so it often survives instance restarts.
  4. Only if the health check still fails does it ask you to paste a fresh
     Cookie (copied from the browser Network panel: open the "lab" document
     request for the DSW page, Headers -> Request Headers -> "cookie" ->
     copy the whole value), then retries.

The config file path comes from gemma_client._AMD_VLLM_CONFIG_PATH (kept
out of source control). Nothing here is sent anywhere except to your own
AMD vLLM gateway (for the health check).
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gemma_client import _AMD_VLLM_CONFIG_PATH, _load_amd_vllm_config  # noqa: E402
from provider_health import check_amd_health  # noqa: E402

GATEWAY_TEMPLATE = "https://dsw-gateway-cn-hangzhou.data.aliyun.com/{instance}/proxy/8000"


def _normalize_instance_id(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        raise ValueError("instance id is empty")
    if not raw.startswith("dsw-"):
        raw = f"dsw-{raw}"
    if not re.fullmatch(r"dsw-[0-9a-zA-Z]+", raw):
        raise ValueError(f"unexpected instance id format: {raw!r}")
    return raw


def _write_config(base_url: str, model: str, cookie: str | None) -> None:
    lines = [f"AMD_VLLM_BASE_URL={base_url}", f"AMD_VLLM_MODEL={model}"]
    if cookie:
        lines.append(f"DSW_GATEWAY_COOKIE={cookie}")
    with open(_AMD_VLLM_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    print("=== AMD vLLM (DSW) config refresh ===")

    instance_raw = input("New DSW instance id (e.g. dsw-1968466 or 1968466): ")
    instance_id = _normalize_instance_id(instance_raw)
    base_url = GATEWAY_TEMPLATE.format(instance=instance_id)

    existing = _load_amd_vllm_config() or {}
    model = existing.get("model") or "gemm"
    cookie = existing.get("cookie")

    print()
    print(f"Trying {base_url} with the existing Cookie...")
    _write_config(base_url, model, cookie)
    result = check_amd_health()
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result.get("ok"):
        print()
        print("Existing Cookie didn't work (likely expired). Need a fresh one:")
        print("  Open the DSW JupyterLab page -> DevTools (F12) -> Network ->")
        print("  Doc filter -> click the 'lab' request -> Headers -> Request")
        print("  Headers -> copy the full 'cookie' value.")
        print()
        cookie = input("Paste the full Cookie value: ").strip()
        if not cookie:
            print("Cookie is empty, aborting.", file=sys.stderr)
            return 1
        _write_config(base_url, model, cookie)
        print()
        print("Retrying health check...")
        result = check_amd_health()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    print()
    print(f"Wrote {_AMD_VLLM_CONFIG_PATH}")
    print(f"  AMD_VLLM_BASE_URL={base_url}")
    print(f"  AMD_VLLM_MODEL={model}")
    print("  DSW_GATEWAY_COOKIE=<hidden>")

    if result.get("ok"):
        print()
        print("OK - AMD vLLM is online. The Streamlit Provider Status panel")
        print("will pick this up within ~15 seconds (cache TTL), or on the")
        print("next page reload.")
        return 0

    print()
    print("AMD vLLM is still NOT online. Common causes:")
    print("  - The Cookie was copied incomplete or from the wrong request")
    print("  - The vLLM server isn't running on this instance yet")
    print("    (re-run /mnt/workspace/restart_gemma4_vllm.sh on the AMD terminal)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
