#!/usr/bin/env python
"""
Manual AMD vLLM tool-call verification.

Confirms the gateway returns standard OpenAI-format tool_calls for the
create_miniprogram_page function — i.e. that --tool-call-parser is correctly
configured for Gemma 4.

Run on the AMD terminal (against the local vLLM server) or on your local
machine (against an SSH-tunneled / DSW-proxied URL):

    AMD_VLLM_BASE_URL=http://127.0.0.1:8000 \
    AMD_VLLM_MODEL=gemm \
    python scripts/amd/test_tool_call.py

Optional env vars:
    DSW_GATEWAY_COOKIE   - sent as the "Cookie" header (only needed when going
                           through an Aliyun DSW proxy)

Reference - the AMD terminal's existing fixed verification flow (kept here
only as a reference, do not assume every environment uses this exact path):

    curl -s -X POST "http://127.0.0.1:8000/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -d '{ ... model "gemm", create_miniprogram_page tool, tool_choice "auto" ... }'
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_miniprogram_page",
            "description": "创建微信小程序页面代码",
            "parameters": {
                "type": "object",
                "properties": {
                    "wxml": {"type": "string"},
                    "wxss": {"type": "string"},
                    "js": {"type": "string"},
                },
                "required": ["wxml", "wxss", "js"],
            },
        },
    }
]


def main() -> int:
    base_url = os.environ.get("AMD_VLLM_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    model = os.environ.get("AMD_VLLM_MODEL", "gemm")
    cookie = os.environ.get("DSW_GATEWAY_COOKIE", "")

    headers = {"Content-Type": "application/json"}
    if cookie:
        headers["Cookie"] = cookie

    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": "请调用 create_miniprogram_page 工具生成一个极简微信小程序页面。"}
        ],
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.2,
        "max_tokens": 512,
        "stream": False,
    }

    url = f"{base_url}/v1/chat/completions"
    result = {"ok": False, "has_tool_calls": False, "tool_name": None, "raw_response_path": None, "reason": ""}

    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        result["reason"] = f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:300]}"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    except Exception as exc:
        result["reason"] = str(exc)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    out_dir = os.path.join(os.path.dirname(__file__), "_out")
    os.makedirs(out_dir, exist_ok=True)
    raw_path = os.path.join(out_dir, f"tool_call_response_{int(time.time())}.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(raw)
    result["raw_response_path"] = raw_path

    try:
        data = json.loads(raw)
        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            result["has_tool_calls"] = True
            result["tool_name"] = tool_calls[0].get("function", {}).get("name")
            result["ok"] = result["tool_name"] == "create_miniprogram_page"
            result["reason"] = "ok" if result["ok"] else "tool_calls present but unexpected tool name"
        else:
            result["reason"] = "no tool_calls in response (model replied with plain text instead)"
    except Exception as exc:
        result["reason"] = f"failed to parse response: {exc}"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
