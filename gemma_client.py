import urllib.request
import urllib.error
import json
import os
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


def call_gemma_text(
    prompt: str,
    image_data: bytes | None = None,
    image_mime: str = "image/jpeg",
    image_list: list | None = None,
    model: str = "gemma-4-27b-it",
) -> str:
    """
    Quick text call to Gemma 4 — no function calling, returns raw text.
    Used for the requirement clarification phase.
    Falls back to gemma-4-31b-it if 27b is unavailable.
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
        _log.warning(f"[clarify] HTTP {e.code} model={model}")
        if e.code in (404, 400) and model != "gemma-4-31b-it":
            return call_gemma_text(prompt, image_data, image_mime, image_list, model="gemma-4-31b-it")
        raise
    except (KeyError, IndexError) as e:
        _log.warning(f"[clarify] parse error: {e}")
        return ""


def call_gemma_with_tools(
    prompt: str,
    image_data: bytes | None = None,
    image_mime: str = "image/jpeg",
    image_list: list | None = None,
) -> dict:
    """
    Call Gemma 4 via Google AI Studio with Native Function Calling.
    Returns {'wxml': str, 'wxss': str, 'js': str}.
    Falls back to triple-marker text parsing if function call is not triggered.
    image_list: list of (bytes, mime_type) for multi-image multimodal input.
    """
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "未找到 API Key。请设置环境变量 GEMINI_API_KEY，"
            "或在 E:\\file+desktop\\gemma_key.txt 里写入 key。"
        )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemma-4-31b-it:generateContent?key={api_key}"
    )

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
            return parsed
    except (KeyError, IndexError, TypeError):
        pass

    _log.error(f"[generate] FAILED response={str(result)[:300]}")
    raise ValueError(
        "Gemma 未返回有效代码（Function Call 未触发，文本解析也失败）。"
        f"响应片段: {str(result)[:300]}"
    )
