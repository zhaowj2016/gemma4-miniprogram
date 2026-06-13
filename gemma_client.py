import urllib.request
import urllib.error
import json
import os
import re
import time
import logging as _logging
from pathlib import Path as _Path
from parser import parse_triple

_LOG_PATH = _Path(__file__).resolve().parent / "demo_cache" / "gemma.log"
_LOG_PATH.parent.mkdir(exist_ok=True)
_log = _logging.getLogger("gemma_client")
if not _log.handlers:
    _fh = _logging.FileHandler(_LOG_PATH, encoding="utf-8")
    _fh.setFormatter(_logging.Formatter("%(asctime)s  %(message)s"))
    _log.addHandler(_fh)
    _log.setLevel(_logging.INFO)

# Tool declaration for Native Function Calling (BUILD_SPEC §4)
TOOLS = [
    {
        "name": "create_miniprogram_page",
        "description": "生成微信小程序 pages/index/index 页面的三个核心文件",
        "parameters": {
            "type": "object",
            "properties": {
                "wxml": {
                    "type": "string",
                    "description": "页面 WXML 结构代码，只使用合法小程序组件"
                },
                "wxss": {
                    "type": "string",
                    "description": "页面 WXSS 样式代码"
                },
                "js": {
                    "type": "string",
                    "description": "页面 JS 逻辑代码，必须包含 Page({}) 构造，数据用本地 mock"
                }
            },
            "required": ["wxml", "wxss", "js"]
        }
    }
]

# Same tool declaration translated to the OpenAI-compatible schema used by
# the AMD vLLM gateway's /v1/chat/completions endpoint.
_OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": TOOLS[0]["name"],
            "description": TOOLS[0]["description"],
            "parameters": TOOLS[0]["parameters"],
        }
    }
]

_AMD_VLLM_CONFIG_PATH = r"E:\file+desktop\gemma_amd_config.txt"
GOOGLE_AI_STUDIO_MODEL = "gemma-4-31b-it"


def _setting(name: str) -> str | None:
    """st.secrets (if available) > environment variable. Never raises."""
    try:
        import streamlit as st
        if name in st.secrets:
            value = st.secrets[name]
            if value is not None:
                return str(value)
    except Exception:
        pass
    return os.environ.get(name)


def _load_amd_vllm_config() -> dict | None:
    """Resolve the AMD vLLM gateway config (BASE_URL / MODEL / Cookie).

    Priority: env vars / st.secrets (AMD_VLLM_BASE_URL, AMD_VLLM_MODEL,
    DSW_GATEWAY_COOKIE) first, then the local config file
    E:\\file+desktop\\gemma_amd_config.txt as a fallback.

    Returns None when no source provides a usable AMD_VLLM_BASE_URL, so
    callers transparently fall back to the Google AI Studio path.
    """
    if (_setting("ENABLE_AMD_VLLM") or "").strip().lower() in ("0", "false", "no", "off"):
        return None

    base_url = _setting("AMD_VLLM_BASE_URL")
    model = _setting("AMD_VLLM_MODEL")
    cookie = _setting("DSW_GATEWAY_COOKIE")

    if not base_url and os.path.exists(_AMD_VLLM_CONFIG_PATH):
        cfg = {}
        try:
            with open(_AMD_VLLM_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    cfg[key.strip()] = value.strip().strip('"').strip("'")
        except Exception:
            cfg = {}
        base_url = base_url or cfg.get("AMD_VLLM_BASE_URL")
        model = model or cfg.get("AMD_VLLM_MODEL")
        cookie = cookie or cfg.get("DSW_GATEWAY_COOKIE")

    if not base_url:
        return None
    return {
        "base_url": base_url.rstrip("/"),
        "model": model or "gemma31b",
        "cookie": cookie,
    }


def _get_api_key() -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMMA_API_KEY")

    if not api_key and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    for prefix in ("GEMINI_API_KEY=", "GEMMA_API_KEY="):
                        if line.startswith(prefix):
                            api_key = line[len(prefix):].strip().strip('"').strip("'")
                            break
                    if api_key:
                        break
        except Exception:
            pass

    if not api_key:
        desktop_path = r"E:\file+desktop\gemma_key.txt"
        if os.path.exists(desktop_path):
            try:
                with open(desktop_path, "r", encoding="utf-8-sig") as f:
                    content = f.read().strip()
                found = False
                for line in content.split("\n"):
                    line = line.strip()
                    for prefix in ("GEMMA_API_KEY=", "GEMINI_API_KEY="):
                        if line.startswith(prefix):
                            api_key = line[len(prefix):].strip().strip('"').strip("'")
                            found = True
                            break
                    if found:
                        break
                if not api_key and content:
                    api_key = content.split("\n")[0].strip().strip('"').strip("'")
            except Exception:
                pass

    return api_key or None


def _build_parts(
    prompt: str,
    image_data: bytes | None = None,
    image_mime: str = "image/jpeg",
    image_list: list | None = None,
) -> list:
    """Build the 'parts' array for a Gemma API request.

    image_list is a list of (bytes, mime_type) tuples for multi-image upload.
    Single image_data is kept for backward compatibility.
    """
    import base64
    parts = []
    if image_list:
        for img_bytes, mime in image_list:
            parts.append({
                "inlineData": {
                    "mimeType": mime,
                    "data": base64.b64encode(img_bytes).decode(),
                }
            })
    elif image_data:
        parts.append({
            "inlineData": {
                "mimeType": image_mime,
                "data": base64.b64encode(image_data).decode(),
            }
        })
    parts.append({"text": prompt})
    return parts


def _build_openai_messages(
    prompt: str,
    image_data: bytes | None = None,
    image_mime: str = "image/jpeg",
    image_list: list | None = None,
) -> list:
    """Build an OpenAI-compatible 'messages' array, mirroring _build_parts."""
    import base64
    images = image_list if image_list else ([(image_data, image_mime)] if image_data else [])
    if not images:
        return [{"role": "user", "content": prompt}]
    content = [
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{base64.b64encode(img_bytes).decode()}"},
        }
        for img_bytes, mime in images
    ]
    content.append({"type": "text", "text": prompt})
    return [{"role": "user", "content": content}]


def call_gemma_text(
    prompt: str,
    image_data: bytes | None = None,
    image_mime: str = "image/jpeg",
    image_list: list | None = None,
    model: str = "gemma-4-26b-a4b-it",
) -> str:
    """
    Quick text call to Gemma 4 — no function calling, returns raw text.
    Used for the requirement clarification phase.
    """
    import base64

    api_key = _get_api_key()
    if not api_key:
        raise ValueError("未找到 API Key")

    parts = _build_parts(prompt, image_data, image_mime, image_list)

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0.6, "maxOutputTokens": 1024},
    }
    _log.info(f"[clarify] model={model} images={len(image_list) if image_list else (1 if image_data else 0)} prompt_len={len(prompt)}")
    encoded = json.dumps(body).encode("utf-8")

    # Google AI Studio 偶发瞬时 5xx（观测到 0.8s 内快速返回 500，重试即恢复）。
    # 澄清环节没有跨后端兜底，这里对 5xx 做最多 2 次短退避重试，避免一次
    # 抖动就把用户打到通用兜底问题。4xx（如 key 无效、429 配额）不重试。
    last_http_error = None
    for attempt in range(3):
        if attempt:
            time.sleep(1.5 * attempt)
            _log.info(f"[clarify] retry {attempt}/2 model={model}")
        req = urllib.request.Request(
            url, data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            _log.info(f"[clarify] OK response_len={len(text)} preview={text[:120].replace(chr(10),' ')}")
            return text
        except urllib.error.HTTPError as e:
            _log.warning(f"[clarify] HTTP {e.code} model={model} attempt={attempt + 1}")
            if e.code < 500:
                raise
            last_http_error = e
        except (KeyError, IndexError) as e:
            _log.warning(f"[clarify] parse error: {e}")
            return ""
    raise last_http_error


# Gemma's own tool-call token format does not match the OpenAI tool_calls
# schema and leaks through as plain text when vLLM's --tool-call-parser
# doesn't recognise it. Gemma is INCONSISTENT about how it delimits the field
# values, so we handle both observed variants:
#   变体 A（特殊分隔符）: create_miniprogram_page{js:<|"|>...<|"|>,wxml:<|"|>...<|"|>,...}<tool_call|>
#   变体 B（普通双引号）: create_miniprogram_page{js: "...", wxml: "...", wxss: "..."}
# 两个正则都用「非贪婪 + 前瞻锚定到下一个字段名/收尾」的方式定位真正的结束分隔符，
# 因此即使值（JS/CSS 代码）内部含有大量引号也能正确切分。
_GEMMA_NATIVE_TOOLCALL_RE = re.compile(
    r'(wxml|wxss|js):<\|"\|>(.*?)<\|"\|>(?=,(?:wxml|wxss|js):|\}<tool_call|\}\s*$)',
    re.DOTALL,
)
# 变体 B：field: "value"，结束引号后必须紧跟「, 下一字段:」或「}」收尾
_GEMMA_PLAINQUOTE_TOOLCALL_RE = re.compile(
    r'(wxml|wxss|js)\s*:\s*"(.*?)"\s*(?=,\s*(?:wxml|wxss|js)\s*:|\}|<tool_call)',
    re.DOTALL,
)


def _parse_gemma_native_tool_call(text: str) -> dict | None:
    for pattern in (_GEMMA_NATIVE_TOOLCALL_RE, _GEMMA_PLAINQUOTE_TOOLCALL_RE):
        matches = pattern.findall(text)
        if not matches:
            continue
        result = {k: v for k, v in matches}
        if all(k in result and result[k].strip() for k in ("wxml", "wxss", "js")):
            return result
    return None


# Unified response-parsing layer shared by every provider. Tries, in priority
# order: (1) standard OpenAI-format structured tool_calls — what vLLM's
# --tool-call-parser gemma4 and Google's native functionCall both populate when
# they correctly recognise the model's output; (2) Gemma's own <|tool_call>
# envelope when it leaks through as plain text content; (3) plain triple-marker
# text. Always returns {'wxml','wxss','js','parse_method','provider'} or raises.
def parse_llm_message(message: dict, provider: str = "unknown") -> dict:
    tool_calls = message.get("tool_calls") or []
    if tool_calls:
        fn = tool_calls[0].get("function", {})
        name = fn.get("name")
        if name == "create_miniprogram_page":
            args_raw = fn.get("arguments", "{}")
            args = None
            if isinstance(args_raw, str):
                try:
                    args = json.loads(args_raw)
                except json.JSONDecodeError as e:
                    # Surface this clearly instead of silently falling through —
                    # a structured tool_calls response with malformed JSON
                    # arguments points at a real server-side issue worth seeing.
                    _log.warning(
                        f"[parse][{provider}] standard_tool_calls.arguments 不是合法 JSON："
                        f"{e}; raw={args_raw[:200]!r}"
                    )
            else:
                args = args_raw
            if args and all(k in args for k in ("wxml", "wxss", "js")):
                return {
                    "wxml": str(args["wxml"]),
                    "wxss": str(args["wxss"]),
                    "js": str(args["js"]),
                    "parse_method": "standard_tool_calls",
                    "provider": provider,
                }

    content = message.get("content") or ""
    if "<|tool_call>" in content or "call:create_miniprogram_page" in content:
        native = _parse_gemma_native_tool_call(content)
        if native:
            return {
                "wxml": native["wxml"],
                "wxss": native["wxss"],
                "js": native["js"],
                "parse_method": "gemma_raw_tool_call",
                "provider": provider,
            }

    parsed = parse_triple(content)
    if parsed and all(k in parsed for k in ("wxml", "wxss", "js")):
        return {
            "wxml": parsed["wxml"],
            "wxss": parsed["wxss"],
            "js": parsed["js"],
            "parse_method": "plain_text_fallback",
            "provider": provider,
        }

    raise ValueError(
        f"[{provider}] 响应中既没有标准 tool_calls，也没有可识别的 Gemma 信封或文本三件套。"
        f"内容片段: {content[:300]!r}"
    )


def _call_amd_vllm_with_tools(
    prompt: str,
    cfg: dict,
    image_data: bytes | None = None,
    image_mime: str = "image/jpeg",
    image_list: list | None = None,
) -> dict:
    """
    Call the local AMD vLLM Gemma 31B gateway via its OpenAI-compatible
    /v1/chat/completions endpoint. Mirrors call_gemma_with_tools' contract —
    returns {'wxml', 'wxss', 'js'} or raises (caller falls back to Google).

    Streams the response (SSE): the Aliyun DSW gateway's reverse proxy enforces
    an upstream-response timeout (~30-40s) far shorter than the ~1000+ line
    generations this app requires take to complete; a continuous byte stream
    keeps the proxy from observing a "silent" gap and returning 504.
    """
    url = f"{cfg['base_url']}/v1/chat/completions"
    provider_started = time.monotonic()
    body = {
        "model": cfg["model"],
        "messages": _build_openai_messages(prompt, image_data, image_mime, image_list),
        "tools": _OPENAI_TOOLS,
        "tool_choice": {"type": "function", "function": {"name": "create_miniprogram_page"}},
        "temperature": 0.7,
        # 输出预算 vs 上下文权衡（关键）：
        #   实测输入(完整样例 + 图库 asset_list + 约束)约 26-28K token 且有浮动。
        #   - vLLM 64K 上下文：输入+输出须 < 65536，故输出上限只能给到 ~30000（留安全余量，
        #     否则会出现「差几个 token」的 400 → 兜底 Google）。30000 足够模型常规输出。
        #   - 若 vLLM 升到 128K：把这里提到 48000，可稳定容纳 ~2000 行完整输出，不再撞边界。
        "max_tokens": int(_setting("AMD_VLLM_MAX_TOKENS") or "48000"),
        "stream": True,
    }
    encoded = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if cfg.get("cookie"):
        headers["Cookie"] = cfg["cookie"]
    req = urllib.request.Request(
        url,
        data=encoded,
        headers=headers,
        method="POST",
    )

    img_count = len(image_list) if image_list else (1 if image_data else 0)
    _log.info(f"[generate][amd_vllm] === NEW REQUEST (stream) === model={cfg['model']} images={img_count} prompt_len={len(prompt)}")

    text_chunks: list[str] = []
    tool_call_args: dict[int, str] = {}
    tool_call_names: dict[int, str] = {}
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[len("data:"):].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                piece = delta.get("content")
                if piece:
                    text_chunks.append(piece)
                for tc in (delta.get("tool_calls") or []):
                    idx = tc.get("index", 0)
                    fn = tc.get("function", {})
                    if fn.get("name"):
                        tool_call_names[idx] = fn["name"]
                    if fn.get("arguments"):
                        tool_call_args[idx] = tool_call_args.get(idx, "") + fn["arguments"]
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AMD vLLM HTTP {e.code}: {body_text[:300]}")

    text = "".join(text_chunks)
    # Re-assemble accumulated streaming deltas into a single OpenAI-shaped
    # message so both stream=True (here) and stream=False (tests) feed the
    # exact same parse_llm_message contract.
    tool_calls_msg = [
        {"function": {"name": tool_call_names.get(idx, ""), "arguments": tool_call_args.get(idx, "")}}
        for idx in sorted(set(tool_call_names) | set(tool_call_args))
    ]

    try:
        parsed = parse_llm_message({"content": text or None, "tool_calls": tool_calls_msg}, provider="amd")
    except ValueError:
        raise ValueError(f"AMD vLLM 未返回有效代码（标准 tool_calls / 原生信封 / 文本解析均失败）。响应片段: {text[:300]}")

    lines = {k: len(parsed[k].splitlines()) for k in ("wxml", "wxss", "js")}
    _method_tag = {
        "standard_tool_calls": "openai",
        "gemma_raw_tool_call": "gemma_native",
        "plain_text_fallback": "text_parse",
    }[parsed["parse_method"]]
    _log.info(
        f"[generate][amd_vllm] tool_call({_method_tag})=OK lines={lines} "
        f"parse_method={parsed['parse_method']} provider={parsed['provider']}"
    )
    if parsed["parse_method"] == "standard_tool_calls":
        _log.info("[generate][amd_vllm] ✅ AMD vLLM standard tool_calls parsed successfully")
    parsed.update({
        "provider": "amd",
        "actual_provider": "amd",
        "model": cfg["model"],
        "actual_model": cfg["model"],
        "backend": "amd_vllm",
        "provider_latency_ms": int((time.monotonic() - provider_started) * 1000),
        "provider_latency_source": "measured",
    })
    return parsed


def _call_google_ai_studio_with_tools(
    prompt: str,
    image_data: bytes | None = None,
    image_mime: str = "image/jpeg",
    image_list: list | None = None,
) -> dict:
    """
    Google AI Studio gemma-4-31b-it Native Function Calling backend.
    Raises on failure (no internal fallback) — `call_gemma_with_tools` decides
    whether/how to fall back to the other backend.
    Returns {'wxml', 'wxss', 'js', 'parse_method', 'provider': 'google'}.
    """
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "未找到 API Key。请设置环境变量 GEMINI_API_KEY，"
            "或在 E:\\file+desktop\\gemma_key.txt 里写入 key。"
        )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GOOGLE_AI_STUDIO_MODEL}:generateContent?key={api_key}"
    )
    provider_started = time.monotonic()

    parts = _build_parts(prompt, image_data, image_mime, image_list)
    img_count = len(image_list) if image_list else (1 if image_data else 0)
    _log.info(f"[generate] === NEW REQUEST ===")
    _log.info(f"[generate] images={img_count} prompt_len={len(prompt)}")
    _log.info(f"[generate] prompt_preview={prompt[:400].replace(chr(10),' ')}")

    body = {
        "contents": [
            {
                "role": "user",
                "parts": parts,
            }
        ],
        "tools": [
            {
                "functionDeclarations": TOOLS
            }
        ],
        "toolConfig": {
            "functionCallingConfig": {
                "mode": "AUTO"
            }
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 16384
        }
    }

    encoded = json.dumps(body).encode("utf-8")
    max_retries = 3
    base_delay = 3
    result = None
    last_error = None

    for attempt in range(max_retries):
        req = urllib.request.Request(
            url,
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as response:
                result = json.loads(response.read().decode("utf-8"))
            last_error = None
            break
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            last_error = RuntimeError(f"HTTP {e.code}: {error_body[:300]}")
            if e.code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            break
        except Exception as e:
            last_error = RuntimeError(f"请求失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(base_delay)
                continue
            break

    if last_error:
        raise last_error

    # 1. Try Native Function Call result
    try:
        parts = result["candidates"][0]["content"]["parts"]
        for part in parts:
            if "functionCall" in part:
                args = part["functionCall"]["args"]
                if "wxml" in args and "wxss" in args and "js" in args:
                    wxml_l = len(str(args["wxml"]).splitlines())
                    wxss_l = len(str(args["wxss"]).splitlines())
                    js_l   = len(str(args["js"]).splitlines())
                    _log.info(f"[generate] function_call=OK wxml={wxml_l}L wxss={wxss_l}L js={js_l}L total={wxml_l+wxss_l+js_l}L")
                    return {
                        "wxml": str(args["wxml"]),
                        "wxss": str(args["wxss"]),
                        "js": str(args["js"]),
                        "parse_method": "standard_tool_calls",
                        "provider": "google",
                        "actual_provider": "google",
                        "model": GOOGLE_AI_STUDIO_MODEL,
                        "actual_model": GOOGLE_AI_STUDIO_MODEL,
                        "backend": "google_ai_studio",
                        "provider_latency_ms": int((time.monotonic() - provider_started) * 1000),
                        "provider_latency_source": "measured",
                    }
    except (KeyError, IndexError, TypeError):
        pass

    # 2. Fallback: parse triple-marker text response
    _log.info("[generate] function_call=MISSED fallback=text_parse")
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        _log.info(f"[generate] text_response_len={len(text)} preview={text[:200].replace(chr(10),' ')}")
        parsed = parse_triple(text)
        if parsed and "wxml" in parsed and "wxss" in parsed and "js" in parsed:
            wxml_l = len(parsed["wxml"].splitlines())
            wxss_l = len(parsed["wxss"].splitlines())
            js_l   = len(parsed["js"].splitlines())
            _log.info(f"[generate] text_parse=OK wxml={wxml_l}L wxss={wxss_l}L js={js_l}L")
            return {
                "wxml": parsed["wxml"],
                "wxss": parsed["wxss"],
                "js": parsed["js"],
                "parse_method": "plain_text_fallback",
                "provider": "google",
                "actual_provider": "google",
                "model": GOOGLE_AI_STUDIO_MODEL,
                "actual_model": GOOGLE_AI_STUDIO_MODEL,
                "backend": "google_ai_studio",
                "provider_latency_ms": int((time.monotonic() - provider_started) * 1000),
                "provider_latency_source": "measured",
            }
    except (KeyError, IndexError, TypeError):
        pass

    _log.error(f"[generate] FAILED response={str(result)[:300]}")
    raise ValueError(
        "Gemma 未返回有效代码（Function Call 未触发，文本解析也失败）。"
        f"响应片段: {str(result)[:300]}"
    )


def call_gemma_with_tools(
    prompt: str,
    image_data: bytes | None = None,
    image_mime: str = "image/jpeg",
    image_list: list | None = None,
    mode: str = "auto",
) -> dict:
    """
    Generate the final wxml/wxss/js triple via Native Function Calling.

    `mode` selects which backend this request *prefers* (surfaced in the UI as
    "快速 Agent 模式" / "深度生成模式"). All three modes are cross-fallback —
    Google and AMD can stand in for each other — so a demo never hard-fails just
    because the user picked a backend that's temporarily unavailable:
      - "auto"  (default): try the local AMD vLLM Gemma 31B gateway first
        (when E:\\file+desktop\\gemma_amd_config.txt is present and complete),
        then fall back to Google AI Studio gemma-4-31b-it.
      - "agent": prefer Google AI Studio gemma-4-31b-it (快速 Agent 模式 —
        official hosted API, stable Native Function Calling); falls back to the
        AMD vLLM gateway if Google fails and AMD is configured.
      - "deep": prefer the self-hosted AMD vLLM Gemma 31B gateway (深度生成模式 —
        longer context/output); falls back to Google AI Studio if AMD is not
        configured or the request fails.

    Whichever backend actually served the request is reported truthfully via
    `provider` / `parse_method` (as always). When the *requested* mode could not
    be honored and a cross-backend fallback kicked in, the result additionally
    carries `requested_mode`, `fallback_used=True` and `fallback_reason`, so the
    UI can say e.g. "你选择了深度生成模式，但本次实际命中了 Google AI Studio
    （原因：AMD 网关未配置）" — robustness without hiding what really happened.

    Returns {'wxml': str, 'wxss': str, 'js': str, 'provider': str, 'parse_method': str, ...}.
    image_list: list of (bytes, mime_type) for multi-image multimodal input.
    """
    amd_cfg = _load_amd_vllm_config()

    def _amd():
        return _call_amd_vllm_with_tools(prompt, amd_cfg, image_data, image_mime, image_list)

    def _google():
        return _call_google_ai_studio_with_tools(prompt, image_data, image_mime, image_list)

    def _as_fallback(result: dict, reason: str) -> dict:
        result["requested_mode"] = mode
        result["fallback_used"] = True
        result["fallback_reason"] = reason
        return result

    def _as_requested(result: dict) -> dict:
        result.setdefault("requested_mode", mode)
        result.setdefault("fallback_used", False)
        result.setdefault("fallback_reason", "")
        return result

    if mode == "deep":
        if amd_cfg:
            try:
                return _as_requested(_amd())
            except Exception as e:
                _log.warning(f"[generate][amd_vllm] FAILED in deep mode, falling back to Google AI Studio: {e}")
                return _as_fallback(_google(), f"AMD vLLM 自托管网关调用失败：{e}")
        _log.warning("[generate] deep mode requested but no AMD config found — falling back to Google AI Studio")
        return _as_fallback(
            _google(),
            "未检测到 AMD vLLM 网关配置（E:\\file+desktop\\gemma_amd_config.txt）",
        )

    if mode == "agent":
        try:
            return _as_requested(_google())
        except Exception as e:
            if amd_cfg:
                _log.warning(f"[generate][google] FAILED in agent mode, falling back to AMD vLLM: {e}")
                try:
                    return _as_fallback(_amd(), f"Google AI Studio 调用失败：{e}")
                except Exception as amd_e:
                    _log.warning(f"[generate][amd_vllm] cross-fallback also FAILED: {amd_e}")
            raise

    # mode == "auto" (default): system decides — AMD first when configured, else Google
    if amd_cfg:
        try:
            return _as_requested(_amd())
        except Exception as e:
            _log.warning(f"[generate][amd_vllm] FAILED, falling back to Google AI Studio: {e}")
    return _as_requested(_google())
