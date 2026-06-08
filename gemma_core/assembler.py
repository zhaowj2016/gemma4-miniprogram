"""Semantic block assembler for WeChat mini-program pages."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
BLOCKS_DIR = BASE_DIR / "blocks"

SPEC_START = "/* BLOCK_SPEC_JSON"
SPEC_END = "END_BLOCK_SPEC_JSON */"


class AssembleError(ValueError):
    """Raised when a block cannot be assembled safely."""


def load_block(name: str) -> dict[str, Any]:
    """Load a semantic block from blocks/<name>/."""
    block_dir = BLOCKS_DIR / name
    if not block_dir.is_dir():
        raise FileNotFoundError(f"Unknown block: {name}")

    js = (block_dir / "fragment.js").read_text(encoding="utf-8", errors="replace")
    spec = _extract_spec(js)
    meta_path = block_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    return {
        "name": name,
        "wxml": (block_dir / "fragment.wxml").read_text(encoding="utf-8", errors="replace").strip(),
        "wxss": (block_dir / "fragment.wxss").read_text(encoding="utf-8", errors="replace").strip(),
        "js": js,
        "data": deepcopy(spec.get("data", {})),
        "methods": deepcopy(spec.get("methods", {})),
        "meta": meta,
    }


def assemble(blocks: list[dict[str, Any] | str]) -> dict[str, str]:
    """Assemble semantic block fragments into a valid pages/index/index page."""
    normalized = [_normalize_block(block) for block in blocks]
    merged_data: dict[str, Any] = {}
    merged_methods: dict[str, str] = {}
    wxml_parts: list[str] = []
    css_blocks: list[str] = []
    seen_css: set[str] = set()

    for index, block in enumerate(normalized):
        name = str(block.get("name") or f"Block{index + 1}")
        prefix = _safe_prefix(name, index)
        wxml = str(block.get("wxml") or "").strip()
        wxss = str(block.get("wxss") or "").strip()
        data = deepcopy(block.get("data") or {})
        methods = deepcopy(block.get("methods") or {})

        data_renames: dict[str, str] = {}
        for key, value in data.items():
            target = key if key not in merged_data else _unique_name(f"{prefix}_{key}", merged_data)
            if target != key:
                data_renames[key] = target
            merged_data[target] = value

        method_renames: dict[str, str] = {}
        for method_name, method_body in methods.items():
            target = (
                method_name
                if method_name not in merged_methods
                else _unique_name(f"{prefix}_{method_name}", merged_methods)
            )
            if target != method_name:
                method_renames[method_name] = target
            merged_methods[target] = str(method_body).strip()

        wxml = _rewrite_data_bindings(wxml, data_renames)
        wxml = _rewrite_event_bindings(wxml, method_renames)
        methods = {
            method_renames.get(name, name): _rewrite_method_data_refs(body, data_renames)
            for name, body in methods.items()
        }
        for method_name, body in methods.items():
            merged_methods[method_name] = body

        wxml_parts.append(_indent(wxml, 2))
        for css in _split_css_blocks(wxss):
            if css not in seen_css:
                seen_css.add(css)
                css_blocks.append(css)

    wxml_out = "<view class=\"assembled-page\">\n" + "\n".join(wxml_parts) + "\n</view>\n"
    wxss_out = _build_wxss(css_blocks)
    js_out = _build_js(merged_data, merged_methods)
    return {"wxml": wxml_out, "wxss": wxss_out, "js": js_out}


def _normalize_block(block: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(block, str):
        return load_block(block)

    if "wxml" not in block or "wxss" not in block:
        name = block.get("name")
        if not name:
            raise AssembleError("Block dict must include name or inline fragments")
        loaded = load_block(str(name))
        loaded.update({k: v for k, v in block.items() if k not in {"wxml", "wxss", "js"}})
        return loaded

    data = deepcopy(block.get("data") or {})
    methods = deepcopy(block.get("methods") or {})
    if (not data and not methods) and block.get("js"):
        spec = _extract_spec(str(block["js"]))
        data = deepcopy(spec.get("data", {}))
        methods = deepcopy(spec.get("methods", {}))

    return {
        "name": block.get("name", "InlineBlock"),
        "wxml": block.get("wxml", ""),
        "wxss": block.get("wxss", ""),
        "js": block.get("js", ""),
        "data": data,
        "methods": methods,
        "meta": block.get("meta", {}),
    }


def _extract_spec(js: str) -> dict[str, Any]:
    pattern = re.escape(SPEC_START) + r"\s*(.*?)\s*" + re.escape(SPEC_END)
    match = re.search(pattern, js, flags=re.DOTALL)
    if not match:
        return {"data": {}, "methods": {}}
    try:
        spec = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise AssembleError(f"Invalid block spec JSON: {exc}") from exc
    spec.setdefault("data", {})
    spec.setdefault("methods", {})
    return spec


def _safe_prefix(name: str, index: int) -> str:
    clean = re.sub(r"\W+", "_", name).strip("_")
    return clean or f"block_{index + 1}"


def _unique_name(base: str, existing: dict[str, Any]) -> str:
    candidate = re.sub(r"\W+", "_", base).strip("_")
    if not candidate:
        candidate = "field"
    original = candidate
    counter = 2
    while candidate in existing:
        candidate = f"{original}_{counter}"
        counter += 1
    return candidate


def _rewrite_data_bindings(wxml: str, renames: dict[str, str]) -> str:
    for old, new in renames.items():
        wxml = re.sub(r"(\{\{\s*)" + re.escape(old) + r"(\s*\}\})", rf"\1{new}\2", wxml)
    return wxml


def _rewrite_event_bindings(wxml: str, renames: dict[str, str]) -> str:
    if not renames:
        return wxml

    event_attr = r"((?:bind|catch)(?:tap|input|change|submit|confirm|blur|focus|scroll)?|bind:\w+)"
    for old, new in renames.items():
        pattern = event_attr + r"(\s*=\s*[\"'])" + re.escape(old) + r"([\"'])"
        wxml = re.sub(pattern, rf"\1\2{new}\3", wxml)
    return wxml


def _rewrite_method_data_refs(method_body: str, renames: dict[str, str]) -> str:
    for old, new in renames.items():
        method_body = re.sub(r"(\{\s*)" + re.escape(old) + r"(\s*:)", rf"\1{new}\2", method_body)
        method_body = re.sub(r"(,\s*)" + re.escape(old) + r"(\s*:)", rf"\1{new}\2", method_body)
        method_body = re.sub(r"(\bthis\.data\.)" + re.escape(old) + r"\b", rf"\1{new}", method_body)
    return method_body


def _split_css_blocks(wxss: str) -> list[str]:
    blocks: list[str] = []
    for match in re.finditer(r"[^{}]+\{[^{}]*\}", wxss, flags=re.DOTALL):
        block = re.sub(r"\s+", " ", match.group(0)).strip()
        if block:
            blocks.append(block)
    return blocks


def _build_wxss(css_blocks: list[str]) -> str:
    base = (
        ".assembled-page {\n"
        "  min-height: 100vh;\n"
        "  padding-bottom: 168rpx;\n"
        "  box-sizing: border-box;\n"
        "  background: #f6f8fc;\n"
        "}\n"
    )
    return base + "\n".join(css_blocks) + "\n"


def _build_js(data: dict[str, Any], methods: dict[str, str]) -> str:
    data_json = json.dumps(data, ensure_ascii=False, indent=4)
    data_json = _indent(data_json, 2)
    method_lines = []
    for name, body in methods.items():
        if not body.startswith("function"):
            raise AssembleError(f"Method {name} must be a function literal")
        method_lines.append(f"  {name}: {body}")

    comma = "," if method_lines else ""
    methods_text = (",\n" + ",\n".join(method_lines)) if method_lines else ""
    return f"Page({{\n  data: {data_json}{comma}{methods_text}\n}});\n"


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.splitlines())


if __name__ == "__main__":
    demo = assemble(["HeroBanner", "ProductList", "SignupForm", "StickyBottomBar"])
    print(json.dumps(demo, ensure_ascii=False, indent=2))
