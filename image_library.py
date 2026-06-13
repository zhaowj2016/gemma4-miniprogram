from __future__ import annotations

import json
import re
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


SPECIFIC_INDUSTRIES = {
    "coffee",
    "restaurant",
    "beauty",
    "fashion",
    "education",
    "wedding",
    "event_signup",
}

GENERIC_INDUSTRIES = {"product_general", "store_service"}

# 素材库没有覆盖的行业标记词。命中这些词说明 prompt 属于库外行业
# （例如宠物美容里的「美容」会误命中 beauty），此时应走 generic fallback，
# 而不是返回 coffee / beauty 等强语义素材。
OUT_OF_LIBRARY_MARKERS = [
    "宠物", "猫咪", "狗狗", "萌宠", "爱宠", "宠主",
]
OUT_OF_LIBRARY_MARKERS_EN = re.compile(r"\bpets?\b|\bpet[- ]?(shop|store|care|grooming)\b")

RELATED_INDUSTRIES = {
    "coffee": {"restaurant"},
    "restaurant": {"coffee"},
    "beauty": {"store_service"},
    "fashion": {"product_general"},
    "education": {"event_signup"},
    "wedding": {"event_signup"},
    "event_signup": {"education", "store_service"},
}


def _industry_hits(prompt: str, industry: str) -> int:
    hits = 0
    for kw in INDUSTRY_KEYWORDS.get(industry, []):
        if kw.lower() in prompt:
            hits += 1
    return hits


def _is_out_of_library_prompt(prompt: str) -> bool:
    if any(marker in prompt for marker in OUT_OF_LIBRARY_MARKERS):
        return True
    return bool(OUT_OF_LIBRARY_MARKERS_EN.search(prompt))


def select_image_assets(user_prompt: str, limit: int = 8) -> list[dict]:
    assets = all_library_assets()
    if not assets:
        return []
    prompt = (user_prompt or "").lower()

    specific_hits = {
        industry: _industry_hits(prompt, industry)
        for industry in SPECIFIC_INDUSTRIES
    }
    matched_specific = {industry for industry, hits in specific_hits.items() if hits > 0}
    if matched_specific and _is_out_of_library_prompt(prompt):
        # 库外行业（如宠物）的「美容/护理」等词会误命中人类服务行业，
        # 视为未知行业，改走 generic fallback。
        matched_specific = set()

    grounding_status = "industry_match" if matched_specific else "generic_fallback"
    allowed_industries = set()
    if matched_specific:
        allowed_industries |= matched_specific
        for industry in matched_specific:
            allowed_industries |= RELATED_INDUSTRIES.get(industry, set())
    else:
        # 未知行业兜底：限定在中性行业，避免按 manifest 原始顺序
        # 退化出 coffee / beauty 等强语义素材。
        generic_pool = {a.get("industry") for a in assets} & GENERIC_INDUSTRIES
        if generic_pool:
            allowed_industries |= generic_pool

    scored: list[tuple[int, int, dict]] = []
    for idx, asset in enumerate(assets):
        industry = str(asset.get("industry", ""))
        if allowed_industries and industry not in allowed_industries:
            continue
        tags = [str(t).lower() for t in asset.get("tags", [])]
        role = str(asset.get("role", "")).lower()
        score = 0
        if matched_specific:
            if industry in matched_specific:
                score += 100 + specific_hits.get(industry, 0) * 12
            elif industry in GENERIC_INDUSTRIES:
                score -= 25
            else:
                score -= 10
        for kw in INDUSTRY_KEYWORDS.get(industry, []):
            if kw.lower() in prompt:
                score += 5
        for tag in tags:
            if tag and tag in prompt:
                score += 2
        if role == "hero":
            score += 2
        elif role in {"product", "service", "store", "detail", "staff", "venue", "speaker"}:
            score += 1
        scored.append((score, -idx, asset))

    selected = [item[2] for item in sorted(scored, reverse=True)[: max(1, limit)]]
    if not any(a.get("role") == "hero" for a in selected):
        hero_pool = [
            a for a in assets
            if not allowed_industries or a.get("industry") in allowed_industries
        ]
        hero = next((a for a in hero_pool if a.get("role") == "hero"), None)
        if hero:
            selected = [hero] + selected[:-1]
    return [to_prompt_asset(a, grounding_status) for a in selected[:limit]]


def to_prompt_asset(asset: dict, grounding_status: str = "industry_match") -> dict:
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
        "grounding_status": grounding_status,
    }


def find_asset(asset_id: str) -> dict | None:
    return next((a for a in all_library_assets() if a.get("asset_id") == asset_id), None)
