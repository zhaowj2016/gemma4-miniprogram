"""Offline semantic-block orchestrator for mini-program page generation."""

from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable


BASE_DIR = Path(__file__).resolve().parent
BLOCKS_DIR = BASE_DIR / "blocks"

sys.dont_write_bytecode = True
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from assembler import assemble, load_block
from validators import validate_project


PlanFn = Callable[[str, list[dict[str, Any]]], list[str] | str]
GenFn = Callable[..., dict[str, Any]]

_STOP_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "with",
    "page",
    "mini",
    "program",
    "wechat",
    "生成",
    "一个",
    "页面",
    "微信",
    "小程序",
    "包含",
}


def plan_page(user_prompt: str, plan_fn: PlanFn | None = None) -> list[str]:
    """Plan which semantic blocks are needed for a user prompt."""
    metas = _load_block_metas()
    valid_names = {meta["name"] for meta in metas}

    if plan_fn is not None:
        planned = _coerce_plan(plan_fn(user_prompt, metas), valid_names)
        if planned:
            return planned

    explicit = _explicit_plan(user_prompt, valid_names)
    prompt_tokens = _tokens(user_prompt)
    scored: list[tuple[int, str]] = []
    for meta in metas:
        haystack = set()
        haystack.update(_tokens(meta.get("name", "")))
        haystack.update(_tokens(meta.get("description", "")))
        for keyword in meta.get("keywords", []):
            haystack.update(_tokens(str(keyword)))
        score = len(prompt_tokens & haystack)
        scored.append((score, meta["name"]))

    min_score = 2 if explicit else 1
    selected = explicit + [name for score, name in scored if score >= min_score]
    if selected:
        return _sort_by_page_order(_dedupe(selected))[:6]

    return ["HeroBanner", "ProductList", "SignupForm", "StickyBottomBar"]


def fill_blocks(
    blocks: list[str], user_prompt: str, gen_fn: GenFn | None = None
) -> list[dict[str, Any]]:
    """Fill planned blocks with mock data; gen_fn can override per-block data."""
    filled: list[dict[str, Any]] = []
    for block_name in blocks:
        block = load_block(block_name)
        meta = block.get("meta", {})
        data = deepcopy(meta.get("defaultData") or block.get("data") or {})

        if gen_fn is not None:
            generated = _call_gen_fn(gen_fn, block_name, user_prompt, meta)
            if generated:
                if "data" in generated:
                    data.update(generated.get("data") or {})
                else:
                    data.update(generated)

        block["data"] = data
        filled.append(block)
    return filled


def generate_page(
    user_prompt: str, plan_fn: PlanFn | None = None, gen_fn: GenFn | None = None
) -> dict[str, Any]:
    """Run plan -> fill -> assemble -> validate -> limited self-heal."""
    planned = plan_page(user_prompt, plan_fn=plan_fn)
    filled = fill_blocks(planned, user_prompt, gen_fn=gen_fn)
    page = assemble(filled)
    result = _validate_page(page)

    attempts = 0
    while not result.ok and attempts < 2:
        attempts += 1
        bad_names = _locate_bad_blocks(filled)
        if not bad_names:
            break

        repaired: list[dict[str, Any]] = []
        for block in filled:
            if block["name"] in bad_names:
                repaired.extend(fill_blocks([block["name"]], user_prompt, gen_fn=gen_fn))
            else:
                repaired.append(block)
        filled = repaired
        page = assemble(filled)
        result = _validate_page(page)

    return {
        "blocks": [block["name"] for block in filled],
        "page": page,
        "validation": result,
        "attempts": attempts,
    }


def _load_block_metas() -> list[dict[str, Any]]:
    metas: list[dict[str, Any]] = []
    if not BLOCKS_DIR.exists():
        return metas
    for block_dir in sorted(path for path in BLOCKS_DIR.iterdir() if path.is_dir()):
        meta_path = block_dir / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.setdefault("name", block_dir.name)
        metas.append(meta)
    return metas


def _coerce_plan(raw: list[str] | str, valid_names: set[str]) -> list[str]:
    if isinstance(raw, str):
        try:
            decoded = json.loads(raw)
            if isinstance(decoded, list):
                raw = decoded
            else:
                raw = re.findall(r"[A-Za-z][A-Za-z0-9_]+", raw)
        except json.JSONDecodeError:
            raw = re.findall(r"[A-Za-z][A-Za-z0-9_]+", raw)

    if not isinstance(raw, list):
        return []

    return _dedupe([str(name) for name in raw if str(name) in valid_names])


def _explicit_plan(user_prompt: str, valid_names: set[str]) -> list[str]:
    prompt = user_prompt.lower()
    rules = [
        ("HeroBanner", ["hero", "banner", "carousel", "swiper", "首页", "横幅", "轮播"]),
        ("ProductInfo", ["product detail", "detail", "sku", "详情", "产品详情", "商品详情"]),
        ("ProductList", ["product list", "catalog", "grid", "列表", "商品列表", "产品列表"]),
        ("SignupForm", ["signup", "form", "booking", "reserve", "报名", "表单", "预约"]),
        ("StickyBottomBar", ["sticky", "bottom", "action bar", "底栏", "底部", "操作栏"]),
        ("TabSwitcher", ["tab", "switch", "segment", "切换", "标签"]),
        ("ArticleList", ["article", "news", "feed", "文章", "新闻", "资讯"]),
        ("StoreInfo", ["store", "shop", "address", "门店", "店铺", "地址"]),
        ("CouponCard", ["coupon", "discount", "offer", "优惠券", "折扣", "领取"]),
        ("EmptyState", ["empty", "blank", "no result", "空状态", "暂无"]),
    ]
    selected = []
    for name, keywords in rules:
        if name in valid_names and any(keyword in prompt for keyword in keywords):
            selected.append(name)
    return selected


def _sort_by_page_order(names: list[str]) -> list[str]:
    order = {
        "HeroBanner": 0,
        "ProductInfo": 1,
        "TabSwitcher": 2,
        "CouponCard": 3,
        "ProductList": 4,
        "ArticleList": 5,
        "StoreInfo": 6,
        "SignupForm": 7,
        "EmptyState": 8,
        "StickyBottomBar": 9,
    }
    return sorted(names, key=lambda name: (order.get(name, 50), name))


def _call_gen_fn(gen_fn: GenFn, block_name: str, user_prompt: str, meta: dict[str, Any]) -> dict[str, Any]:
    try:
        return gen_fn(block_name, user_prompt, meta)
    except TypeError:
        try:
            return gen_fn(block_name, user_prompt)
        except TypeError:
            return gen_fn(block_name)


def _validate_page(page: dict[str, str]):
    return validate_project(_validator_files(page), full_project=False)


def _validator_files(page: dict[str, str]) -> dict[str, str]:
    return {
        "pages/index/index.wxml": page["wxml"],
        "pages/index/index.wxss": page["wxss"],
        "pages/index/index.js": page["js"],
    }


def _locate_bad_blocks(blocks: list[dict[str, Any]]) -> list[str]:
    bad: list[str] = []
    for block in blocks:
        page = assemble([block])
        result = _validate_page(page)
        if not result.ok:
            bad.append(block["name"])
    return bad


def _tokens(text: str) -> set[str]:
    tokens = set()
    for token in re.findall(r"[\w\u4e00-\u9fff]+", text.lower()):
        if token in _STOP_WORDS:
            continue
        tokens.add(token)
        tokens.update(part for part in token.split("_") if part and part not in _STOP_WORDS)
    return tokens


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def main() -> None:
    prompt = "Build a mini-program page with a carousel hero, product list, signup form, and sticky bottom action bar."
    output = generate_page(prompt)
    validation = output["validation"]

    print("Planned blocks:", " + ".join(output["blocks"]))
    print("Validation:", "PASS" if validation.ok else "FAIL")
    print("hard_errors:", len(validation.hard_errors))
    print("attempts:", output["attempts"])
    print("\nAssembled WXML:\n")
    print(output["page"]["wxml"])
    print("Assembled WXSS bytes:", len(output["page"]["wxss"].encode("utf-8")))
    print("Assembled JS bytes:", len(output["page"]["js"].encode("utf-8")))


if __name__ == "__main__":
    main()
