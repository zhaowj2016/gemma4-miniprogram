"""Prompt construction helpers for the mini-program generator."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
GOLDEN_DIR = BASE_DIR / "golden_examples"

CONSTRAINT_CHECKLIST = """
你是微信小程序 pages/index/index 页面代码生成器。请严格输出一个 JSON 对象, 只包含 wxml、wxss、js 三个键, 不要输出解释文字。

约束清单:
- 只用基础组件: view, text, image, button, input, textarea, form, scroll-view, swiper, swiper-item, block。
- 禁用 HTML 标签, 包括 div、span、p、a、img、ul、li 等。
- 禁止在 {{}} 里调用函数或表达式方法; 需要格式化的数据必须先在 JS data 中准备好。
- swiper 必须使用 current 属性, 禁止使用 current-index。
- 禁止调用真实能力 API: wx.login、wx.request、wx.requestPayment、wx.getLocation、wx.cloud。
- 数据必须使用本地 mock, 写在 JS 的 data 中。
- 必须全量输出三个文件内容, 分别对应 pages/index/index.wxml、pages/index/index.wxss、pages/index/index.js。
""".strip()

_STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "page",
    "mini",
    "program",
    "wechat",
    "index",
    "pages",
    "生成",
    "一个",
    "页面",
    "微信",
    "小程序",
}


def build_prompt(user_prompt: str) -> str:
    """Build a few-shot prompt from golden_examples and the user request."""
    examples = _load_examples()
    selected = _select_examples(user_prompt, examples, limit=2)

    parts = [CONSTRAINT_CHECKLIST]
    if selected:
        parts.append("参考样例(few-shot):")
        for example in selected:
            parts.append(_format_example(example))

    parts.append("用户需求:")
    parts.append(user_prompt.strip())
    return "\n\n".join(parts).strip() + "\n"


def build_repair_prompt(
    user_prompt: str, page_files: dict[str, str], errors: list[str] | tuple[str, ...]
) -> str:
    """Build a repair prompt that feeds validator errors back to the model."""
    normalized_files = _normalize_page_files(page_files)
    error_lines = "\n".join(f"- {err}" for err in errors) or "- 未提供具体错误"

    return f"""{CONSTRAINT_CHECKLIST}

你刚才生成的代码没有通过 validators.validate_project 校验。请只修复下面列出的校验错误, 不要扩展新功能, 不要改变原始需求的范围。
必须全量重新输出 JSON, 且只输出 wxml、wxss、js 三个键。

原始用户需求:
{user_prompt.strip()}

当前代码:
{json.dumps(normalized_files, ensure_ascii=False, indent=2)}

校验错误:
{error_lines}
""".strip() + "\n"


def _load_examples() -> list[dict[str, Any]]:
    index = _load_json(GOLDEN_DIR / "corpus_index.json")
    index_entries = _coerce_index_entries(index)

    examples: list[dict[str, Any]] = []
    if not GOLDEN_DIR.exists():
        return examples

    for sample_dir in sorted(p for p in GOLDEN_DIR.iterdir() if p.is_dir()):
        files = _read_example_files(sample_dir)
        if not all(files.values()):
            continue

        meta = index_entries.get(sample_dir.name, {})
        keywords = _keywords_from_meta(meta) or _tokens(sample_dir.name)
        title = str(meta.get("title") or meta.get("name") or sample_dir.name)
        prompt = str(meta.get("prompt") or meta.get("description") or title)

        examples.append(
            {
                "id": sample_dir.name,
                "title": title,
                "prompt": prompt,
                "keywords": sorted(keywords),
                "files": files,
            }
        )

    return examples


def _read_example_files(sample_dir: Path) -> dict[str, str]:
    return {
        "wxml": _read_first(sample_dir, ("index.wxml", "wxml.txt")),
        "wxss": _read_first(sample_dir, ("index.wxss", "wxss.txt")),
        "js": _read_first(sample_dir, ("index.js", "js.txt")),
    }


def _read_first(sample_dir: Path, names: tuple[str, ...]) -> str:
    for name in names:
        path = sample_dir / name
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace").strip()
    return ""


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _coerce_index_entries(index: Any) -> dict[str, dict[str, Any]]:
    if isinstance(index, dict):
        if isinstance(index.get("examples"), list):
            return {
                str(item.get("id") or item.get("name") or item.get("scenario")): item
                for item in index["examples"]
                if isinstance(item, dict)
            }
        return {str(key): value for key, value in index.items() if isinstance(value, dict)}

    if isinstance(index, list):
        return {
            str(item.get("id") or item.get("name") or item.get("scenario")): item
            for item in index
            if isinstance(item, dict)
        }

    return {}


def _keywords_from_meta(meta: dict[str, Any]) -> set[str]:
    values: list[str] = []
    for key in ("keywords", "tags"):
        raw = meta.get(key)
        if isinstance(raw, list):
            values.extend(str(item) for item in raw)
        elif isinstance(raw, str):
            values.append(raw)
    for key in ("id", "name", "title", "prompt", "description", "scenario"):
        if meta.get(key):
            values.append(str(meta[key]))
    return set().union(*(_tokens(value) for value in values)) if values else set()


def _select_examples(
    user_prompt: str, examples: list[dict[str, Any]], limit: int = 2
) -> list[dict[str, Any]]:
    if not examples:
        return []

    query_tokens = _tokens(user_prompt)
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for example in examples:
        keywords = set(example.get("keywords") or ())
        text_tokens = _tokens(
            " ".join([example["id"], example.get("title", ""), example.get("prompt", "")])
        )
        score = len(query_tokens & (keywords | text_tokens))
        scored.append((score, example["id"], example))

    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = [item[2] for item in scored if item[0] > 0][:limit]
    if selected:
        return selected
    return [item[2] for item in scored[: min(limit, len(scored))]]


def _tokens(text: str) -> set[str]:
    raw = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    tokens: set[str] = set()
    for item in raw:
        if item in _STOP_WORDS:
            continue
        tokens.add(item)
        tokens.update(part for part in item.split("_") if part and part not in _STOP_WORDS)
    return tokens


def _format_example(example: dict[str, Any]) -> str:
    payload = {
        "wxml": example["files"]["wxml"],
        "wxss": example["files"]["wxss"],
        "js": example["files"]["js"],
    }
    return "\n".join(
        [
            f"样例: {example['id']} - {example.get('title', example['id'])}",
            f"需求: {example.get('prompt', example['id'])}",
            "输出:",
            json.dumps(payload, ensure_ascii=False, indent=2),
        ]
    )


def _normalize_page_files(page_files: dict[str, str]) -> dict[str, str]:
    return {
        "wxml": page_files.get("wxml")
        or page_files.get("pages/index/index.wxml")
        or page_files.get("index.wxml")
        or "",
        "wxss": page_files.get("wxss")
        or page_files.get("pages/index/index.wxss")
        or page_files.get("index.wxss")
        or "",
        "js": page_files.get("js")
        or page_files.get("pages/index/index.js")
        or page_files.get("index.js")
        or "",
    }
