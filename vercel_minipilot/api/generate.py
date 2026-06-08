from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from render_wxml import render_phone_html
from scaffold import APP_WXSS


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "library" / "assets_manifest.json"

TOOLS = [
    {
        "name": "create_miniprogram_page",
        "description": "生成微信小程序 pages/index/index 页面的三个核心文件",
        "parameters": {
            "type": "object",
            "properties": {
                "wxml": {"type": "string", "description": "页面 WXML 结构代码"},
                "wxss": {"type": "string", "description": "页面 WXSS 样式代码"},
                "js": {"type": "string", "description": "页面 JS 逻辑代码，必须包含 Page({})"},
            },
            "required": ["wxml", "wxss", "js"],
        },
    }
]

INDUSTRY_KEYWORDS = {
    "coffee": ["coffee", "cafe", "咖啡", "咖啡店", "手冲", "奶茶", "饮品", "点单"],
    "restaurant": ["restaurant", "menu", "餐厅", "菜单", "点餐", "美食", "菜品", "料理"],
    "beauty": ["beauty", "salon", "spa", "美容", "美发", "美甲", "护理", "门店预约"],
    "fashion": ["fashion", "apparel", "服装", "穿搭", "时尚", "女装", "男装", "精品店"],
    "education": ["education", "course", "教育", "课程", "老师", "学习", "培训"],
    "wedding": ["wedding", "婚礼", "婚纱", "写真", "影像", "摄影"],
    "event_signup": ["event", "signup", "活动", "报名", "会议", "沙龙", "峰会"],
}

RELATED = {
    "coffee": {"restaurant"},
    "restaurant": {"coffee"},
    "beauty": {"event_signup"},
    "fashion": {"event_signup"},
    "education": {"event_signup"},
    "wedding": {"event_signup"},
    "event_signup": {"education"},
}


def _assets() -> list[dict]:
    if not MANIFEST.exists():
        return []
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8")).get("assets", [])
    except Exception:
        return []


def _select_assets(prompt: str, limit: int = 8) -> list[dict]:
    text = (prompt or "").lower()
    assets = _assets()
    hits = {
        industry: sum(1 for kw in kws if kw.lower() in text)
        for industry, kws in INDUSTRY_KEYWORDS.items()
    }
    matched = {industry for industry, count in hits.items() if count}
    allowed = set(matched)
    for industry in matched:
        allowed |= RELATED.get(industry, set())
    scored = []
    for idx, asset in enumerate(assets):
        industry = str(asset.get("industry") or "")
        if allowed and industry not in allowed:
            continue
        role = str(asset.get("role") or "")
        score = hits.get(industry, 0) * 20
        if industry in matched:
            score += 100
        if role == "hero":
            score += 2
        elif role in {"product", "store", "service", "detail"}:
            score += 1
        scored.append((score, -idx, asset))
    selected = [a for _, _, a in sorted(scored, reverse=True)[:limit]]
    return [
        {
            "asset_id": a.get("asset_id"),
            "path": a.get("local_path") or a.get("path"),
            "usage": "library_image",
            "industry": a.get("industry"),
            "role": a.get("role"),
            "style": a.get("style"),
            "tags": a.get("tags", []),
        }
        for a in selected
        if a.get("local_path") or a.get("path")
    ]


def _prompt(user_prompt: str, images: list[dict]) -> str:
    assets = _select_assets(user_prompt, 8)
    uploaded_assets = [
        {
            "asset_id": f"user_upload_{i + 1:03d}",
            "path": f"/assets/uploads/user_upload_{i + 1:03d}.jpg",
            "usage": "user_content_image",
            "role": "hero" if i == 0 else "content",
        }
        for i, _ in enumerate(images[:6])
    ]
    asset_list = uploaded_assets + assets
    return f"""
你是微信小程序 pages/index/index 页面代码生成器。必须通过 create_miniprogram_page 工具返回页面代码。

约束清单:
- 只用基础组件: view, text, image, button, input, textarea, form, scroll-view, swiper, swiper-item, block。
- 禁用 HTML 标签, 包括 div、span、p、a、img、ul、li。
- 禁止在 {{{{}}}} 里调用函数或表达式方法; 需要格式化的数据必须先在 JS data 中准备好。
- swiper 必须使用 current 属性, 禁止使用 current-index。
- 禁止调用真实能力 API: wx.login、wx.request、wx.requestPayment、wx.getLocation、wx.cloud。
- 数据必须使用本地 mock, 写在 JS 的 data 中。
- 输出必须包含完整 wxml、wxss、js。

代码完整度要求:
- WXML 覆盖顶部 Banner/轮播、分类筛选 Tab、主内容列表或网格、推荐/统计区、底部固定操作栏。
- WXSS 覆盖卡片样式、圆角、阴影、active 状态、按钮、底部栏。
- JS data 至少 4 个数组/对象组合，包含真实感 mock 数据；实现 tab 切换、数量增减、加入购物车或预约提交。
- 设计要像真实可演示的小程序 MVP，不要像说明文档。

本地图片 asset_list（唯一允许使用的图片来源）:
{json.dumps(asset_list, ensure_ascii=False, indent=2)}

图片硬规则:
- WXML / JS data 的 image src 只能使用 asset_list 中给定的 path。
- 禁止创造新的图片 URL，禁止 Unsplash/Picsum/远程 http(s)、localhost、blob、base64、tmp、streamlit。
- 如果存在 usage=user_content_image 的图片，必须优先放在顶部 hero/banner。
- 不要把同一张图片连续重复铺满列表；同一个 path 最多复用 2 次。
- 图片少于商品数量时，优先保证 hero、门店图、重点商品有图，次要项可以用文字、标签、纯色图片区承载。

用户需求:
{user_prompt.strip()}
""".strip()


def _parts(prompt: str, images: list[dict]) -> list[dict]:
    parts = []
    for image in images[:6]:
        data = str(image.get("data") or "")
        mime = str(image.get("mime") or "image/jpeg")
        if "," in data:
            data = data.split(",", 1)[1]
        if data:
            parts.append({"inlineData": {"mimeType": mime, "data": data}})
    parts.append({"text": prompt})
    return parts


def _call_google(prompt: str, images: list[dict]) -> dict:
    key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMMA_API_KEY") or "").strip().lstrip("\ufeff")
    if not key:
        raise RuntimeError("Vercel 环境变量 GEMINI_API_KEY 未配置")
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent?key=" + urllib.parse.quote(key)
    body = {
        "contents": [{"role": "user", "parts": _parts(prompt, images)}],
        "tools": [{"functionDeclarations": TOOLS}],
        "toolConfig": {"functionCallingConfig": {"mode": "AUTO"}},
        "generationConfig": {"temperature": 0.65, "maxOutputTokens": 8192},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    parts = result["candidates"][0]["content"]["parts"]
    for part in parts:
        if "functionCall" in part:
            args = part["functionCall"].get("args") or {}
            if all(k in args for k in ("wxml", "wxss", "js")):
                return {
                    "wxml": str(args["wxml"]),
                    "wxss": str(args["wxss"]),
                    "js": str(args["js"]),
                    "provider": "google",
                    "parse_method": "standard_tool_calls",
                }
    text = parts[0].get("text", "")
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        parsed = json.loads(match.group(0))
        if all(k in parsed for k in ("wxml", "wxss", "js")):
            parsed["provider"] = "google"
            parsed["parse_method"] = "plain_text_json"
            return parsed
    raise RuntimeError("Gemma 未返回有效 wxml/wxss/js")


def _check(files: dict) -> dict:
    text = "\n".join(str(files.get(k, "")) for k in ("wxml", "js"))
    bad = [
        token
        for token in ("blob:", "localhost", "127.0.0.1", "/tmp", "data:image", "streamlit", "unsplash.com", "picsum.photos")
        if token.lower() in text.lower()
    ]
    return {"ok": not bad, "hard_errors": [f"路径污染: {b}" for b in bad], "warnings": []}


def _handle_generate(body: dict) -> tuple[int, dict]:
    started = time.time()
    try:
        user_prompt = str(body.get("prompt") or "").strip()
        if not user_prompt:
            return 400, {"ok": False, "error": "请输入自然语言需求"}
        images = body.get("images") or []
        built = _prompt(user_prompt, images)
        files = _call_google(built, images)
        phone_html = render_phone_html(files["wxml"], files["wxss"], files["js"], app_wxss=APP_WXSS)
        line_counts = {k: len(str(files.get(k, "")).splitlines()) for k in ("wxml", "wxss", "js")}
        return 200, {
            "ok": True,
            "files": files,
            "phoneHtml": phone_html,
            "validation": _check(files),
            "trace": {
                "elapsed": round(time.time() - started, 1),
                "prompt_chars": len(user_prompt),
                "built_prompt_chars": len(built),
                "line_counts": line_counts,
                "images": len(images),
            },
        }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        return 502, {"ok": False, "error": f"Google AI Studio HTTP {exc.code}: {detail}"}
    except Exception as exc:
        return 500, {"ok": False, "error": str(exc)}


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send_json(200, {"ok": True})

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("content-length") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            body = json.loads(raw or "{}")
        except Exception:
            self._send_json(400, {"ok": False, "error": "请求体不是合法 JSON"})
            return
        status, payload = _handle_generate(body)
        self._send_json(status, payload)

    def do_GET(self) -> None:
        self._send_json(405, {"ok": False, "error": "POST only"})
