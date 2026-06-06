import urllib.request
import urllib.error
import json
import os
import time
from parser import parse_triple

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


def call_gemma_with_tools(prompt: str) -> dict:
    """
    Call Gemma 4 via Google AI Studio with Native Function Calling.
    Returns {'wxml': str, 'wxss': str, 'js': str}.
    Falls back to triple-marker text parsing if function call is not triggered.
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

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
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
            "temperature": 0.4,
            "maxOutputTokens": 8192
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
                    print("--- gemma_client: Function Call 触发成功 ---")
                    return {
                        "wxml": str(args["wxml"]),
                        "wxss": str(args["wxss"]),
                        "js": str(args["js"]),
                    }
    except (KeyError, IndexError, TypeError):
        pass

    # 2. Fallback: parse triple-marker text response
    print("--- gemma_client: Function Call 未触发，回退到三段标记解析 ---")
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        parsed = parse_triple(text)
        if parsed and "wxml" in parsed and "wxss" in parsed and "js" in parsed:
            return parsed
    except (KeyError, IndexError, TypeError):
        pass

    raise ValueError(
        "Gemma 未返回有效代码（Function Call 未触发，文本解析也失败）。"
        f"响应片段: {str(result)[:300]}"
    )
