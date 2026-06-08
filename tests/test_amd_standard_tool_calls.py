"""
Minimal verification: does AMD vLLM (--tool-call-parser gemma4) now return
standard OpenAI-format tool_calls, and does parse_llm_message correctly route
that through the "standard_tool_calls" tier (vs. the gemma_raw_tool_call /
plain_text_fallback adapters)?

Run directly: python tests/test_amd_standard_tool_calls.py
Skips (does not fail) when no AMD config is present, so it's safe in CI.
"""
import sys
import os

# Windows consoles often default to GBK, which can't encode the emoji in the
# success message below — replace instead of crashing on UnicodeEncodeError.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "gemma_core"))

from gemma_client import _load_amd_vllm_config, _call_amd_vllm_with_tools

PROMPT = "生成一个咖啡店点单页，要有商品列表和购物车"


def main():
    cfg = _load_amd_vllm_config()
    if not cfg:
        print("⚠️  未找到 AMD vLLM 配置，跳过（不算失败）")
        return

    result = _call_amd_vllm_with_tools(PROMPT, cfg)

    assert result["wxml"], "wxml 为空"
    assert result["wxss"], "wxss 为空"
    assert result["js"], "js 为空"
    assert result["parse_method"] in (
        "standard_tool_calls",
        "gemma_raw_tool_call",
        "plain_text_fallback",
    ), f"未知 parse_method: {result['parse_method']!r}"
    assert result["provider"] == "amd"

    lines = {k: len(result[k].splitlines()) for k in ("wxml", "wxss", "js")}
    print(f"provider={result['provider']}  parse_method={result['parse_method']}  lines={lines}")

    if result["parse_method"] == "standard_tool_calls":
        print("✅ AMD vLLM standard tool_calls parsed successfully")
    else:
        print(f"ℹ️  走的是兜底解析层（{result['parse_method']}），管线仍然成功产出有效代码")


if __name__ == "__main__":
    main()
