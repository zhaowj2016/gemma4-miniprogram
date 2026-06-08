from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "assets" / "library" / "assets_manifest.json"

INDUSTRY_KEYWORDS = {
    "coffee": ["coffee", "cafe", "咖啡", "咖啡馆", "手冲", "奶茶", "饮品"],
    "restaurant": ["restaurant", "menu", "餐厅", "菜单", "点餐", "美食", "菜品", "料理"],
    "beauty": ["beauty", "salon", "spa", "美容", "美发", "美甲", "护理", "门店预约"],
    "fashion": ["fashion", "apparel", "服装", "穿搭", "时尚", "女装", "男装", "精品店"],
    "education": ["education", "course", "lesson", "teacher", "教育", "课程", "老师", "学习", "培训"],
    "wedding": ["wedding", "婚礼", "婚纱", "写真", "影像", "摄影"],
    "store_service": ["store", "service", "booking", "门店", "服务", "预约", "到店", "企业"],
    "product_general": ["product", "shop", "mall", "commerce", "商品", "电商", "商城", "购物", "详情"],
    "event_signup": ["event", "signup", "活动", "报名", "会议", "沙龙", "峰会", "赛事"],
}


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"assets": []}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def all_library_assets() -> list[dict]:
    return list(load_manifest().get("assets", []))


def select_image_assets(user_prompt: str, limit: int = 8) -> list[dict]:
    assets = all_library_assets()
    if not assets:
        return []
    prompt = (user_prompt or "").lower()
    scored: list[tuple[int, int, dict]] = []
    for idx, asset in enumerate(assets):
        industry = str(asset.get("industry", ""))
        tags = [str(t).lower() for t in asset.get("tags", [])]
        role = str(asset.get("role", "")).lower()
        score = 0
        for kw in INDUSTRY_KEYWORDS.get(industry, []):
            if kw.lower() in prompt:
                score += 5
        for tag in tags:
            if tag and tag in prompt:
                score += 2
        if role == "hero":
            score += 2
        scored.append((score, -idx, asset))

    selected = [item[2] for item in sorted(scored, reverse=True)[: max(1, limit)]]
    if not any(a.get("role") == "hero" for a in selected):
        hero = next((a for a in assets if a.get("role") == "hero"), None)
        if hero:
            selected = [hero] + selected[:-1]
    return [to_prompt_asset(a) for a in selected[:limit]]


def to_prompt_asset(asset: dict) -> dict:
    path = asset.get("local_path") or asset.get("path") or ""
    return {
        "asset_id": asset.get("asset_id"),
        "path": path,
        "wxml_path": path,
        "usage": "library_image",
        "industry": asset.get("industry"),
        "role": asset.get("role"),
        "style": asset.get("style"),
        "tags": asset.get("tags", []),
        "source": asset.get("source"),
        "source_url": asset.get("source_url"),
        "attribution": asset.get("attribution"),
    }


def find_asset(asset_id: str) -> dict | None:
    return next((a for a in all_library_assets() if a.get("asset_id") == asset_id), None)
