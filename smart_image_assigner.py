"""
Layered Image Assignment Strategy for MiniProgram Web Preview.

Three tiers:
  1. exact_match    — industry-relevant local asset from assets/library/
  2. category_fallback — generic but non-conflicting local asset
  3. placeholder    — clean SVG placeholder (never a wrong image)

Metadata tracked per image slot:
  - slot: where in the page (hero, service_card, avatar, review, etc.)
  - requested_category: what we'd ideally want (pet, grooming, salon, etc.)
  - selected_src: the actual source used
  - asset_status: exact_match | category_fallback | placeholder
  - reason: why this selection was made
"""
from __future__ import annotations

import base64
import json
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
LIBRARY_DIR = ROOT / "assets" / "library"
PLACEHOLDER_DIR = ROOT / "assets" / "placeholders"
MANIFEST_PATH = LIBRARY_DIR / "assets_manifest.json"

# ── Industry keyword mapping for business → asset industry ──
# "strictly_forbidden" industries are NEVER used even as fallback
INDUSTRY_MAP = {
    "pet": {
        "exact": ["beauty", "store_service"],
        "fallback": ["fashion"],
        "forbidden": ["coffee", "restaurant", "wedding", "education", "event_signup"],
    },
    "beauty": {
        "exact": ["beauty", "store_service"],
        "fallback": ["fashion"],
        "forbidden": ["coffee", "restaurant", "wedding", "education", "event_signup"],
    },
    "coffee": {
        "exact": ["coffee"],
        "fallback": ["restaurant"],
        "forbidden": ["wedding", "education", "event_signup", "beauty"],
    },
    "restaurant": {
        "exact": ["restaurant"],
        "fallback": ["coffee"],
        "forbidden": ["wedding", "education", "event_signup", "beauty", "fashion"],
    },
    "store": {
        "exact": ["store_service"],
        "fallback": ["beauty", "fashion"],
        "forbidden": ["coffee", "restaurant", "wedding", "education", "event_signup"],
    },
    "education": {
        "exact": ["education"],
        "fallback": ["event_signup"],
        "forbidden": ["coffee", "restaurant", "beauty", "fashion", "wedding"],
    },
    "event": {
        "exact": ["event_signup"],
        "fallback": ["education"],
        "forbidden": ["coffee", "restaurant", "beauty", "fashion", "wedding"],
    },
    "wedding": {
        "exact": ["wedding"],
        "fallback": ["fashion", "event_signup"],
        "forbidden": ["coffee", "restaurant", "education"],
    },
    "fashion": {
        "exact": ["fashion"],
        "fallback": ["beauty", "product_general"],
        "forbidden": ["coffee", "restaurant", "wedding", "education", "event_signup"],
    },
    "product": {
        "exact": ["product_general"],
        "fallback": ["store_service"],
        "forbidden": ["coffee", "restaurant", "wedding", "education", "event_signup"],
    },
    "generic": {
        "exact": ["store_service", "beauty"],
        "fallback": ["fashion", "product_general"],
        "forbidden": ["coffee", "restaurant", "wedding", "education", "event_signup"],
    },
}


@dataclass
class ImageAssignment:
    slot: str
    requested_category: str
    selected_src: str         # url or base64 data URI
    asset_status: str         # exact_match | category_fallback | placeholder
    reason: str
    source_asset_id: str = ""
    source_industry: str = ""


@dataclass
class AssignmentReport:
    assignments: list[ImageAssignment] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.assignments)

    @property
    def exact_count(self) -> int:
        return sum(1 for a in self.assignments if a.asset_status == "exact_match")

    @property
    def fallback_count(self) -> int:
        return sum(1 for a in self.assignments if a.asset_status == "category_fallback")

    @property
    def placeholder_count(self) -> int:
        return sum(1 for a in self.assignments if a.asset_status == "placeholder")

    @property
    def has_forbidden(self) -> bool:
        return any(a.reason.startswith("FORBIDDEN") for a in self.assignments)

    def summary(self) -> str:
        return (
            f"Images: {self.total} total | "
            f"{self.exact_count} exact | "
            f"{self.fallback_count} fallback | "
            f"{self.placeholder_count} placeholder"
        )


# ── Asset catalog ──────────────────────────────────────────────────────────────

def _load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"assets": []}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _get_assets_by_industry(industry: str) -> list[dict]:
    manifest = _load_manifest()
    return [a for a in manifest.get("assets", []) if a.get("industry") == industry]


def _asset_path(asset: dict) -> Path:
    rel = (asset.get("local_path") or "").lstrip("/")
    return ROOT / rel


def _asset_to_base64(asset: dict) -> str:
    fpath = _asset_path(asset)
    if not fpath.is_file():
        return ""
    mime = mimetypes.guess_type(str(fpath))[0] or "image/jpeg"
    b64 = base64.b64encode(fpath.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _placeholder_to_base64(name: str) -> str:
    fpath = PLACEHOLDER_DIR / name
    if not fpath.is_file():
        # ultimate fallback — inline minimal SVG
        return (
            "data:image/svg+xml,"
            "%3Csvg xmlns='http://www.w3.org/2000/svg' width='375' height='250'%3E"
            "%3Crect width='375' height='250' fill='%23e8eaed'/%3E"
            "%3Ctext x='188' y='135' text-anchor='middle' fill='%23888' font-size='14'%3E"
            "Image%3C/text%3E%3C/svg%3E"
        )
    mime = mimetypes.guess_type(str(fpath))[0] or "image/svg+xml"
    b64 = base64.b64encode(fpath.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ── Core assignment engine ─────────────────────────────────────────────────────

def _detect_business_category(prompt: str) -> str:
    """Detect the business type from the user prompt."""
    p = (prompt or "").lower()
    if any(k in p for k in ["宠物", "pet", "猫", "狗", "dog", "cat", "groom", "美容院"]):
        return "pet"
    if any(k in p for k in ["美容", "beauty", "spa", "salon", "美发", "美甲", "护理"]):
        return "beauty"
    if any(k in p for k in ["咖啡", "coffee", "cafe", "手冲", "奶茶", "饮品"]):
        return "coffee"
    if any(k in p for k in ["餐厅", "restaurant", "菜单", "menu", "点餐", "美食", "菜品", "料理"]):
        return "restaurant"
    if any(k in p for k in ["教育", "课程", "education", "course", "培训", "学习"]):
        return "education"
    if any(k in p for k in ["活动", "报名", "event", "signup", "峰会", "沙龙", "赛事"]):
        return "event"
    if any(k in p for k in ["婚礼", "wedding", "婚纱"]):
        return "wedding"
    if any(k in p for k in ["时尚", "fashion", "服装", "穿搭", "精品"]):
        return "fashion"
    if any(k in p for k in ["商品", "product", "商城", "电商", "购物", "详情"]):
        return "product"
    if any(k in p for k in ["门店", "预约", "store", "booking", "服务"]):
        return "store"
    return "generic"


def _select_asset_for_role(
    industry: str,
    role: str,
    exclude_ids: set[str],
) -> Optional[dict]:
    """Select one asset of the given industry+role, not in exclude_ids."""
    candidates = [a for a in _get_assets_by_industry(industry)
                  if a.get("role") == role and a["asset_id"] not in exclude_ids]
    # Also try with broader role matching
    if not candidates:
        candidates = [a for a in _get_assets_by_industry(industry)
                      if a["asset_id"] not in exclude_ids]
    return candidates[0] if candidates else None


def assign_images(
    prompt: str,
    slots: list[tuple[str, str]],  # [(slot_name, desired_role), ...]
) -> AssignmentReport:
    """
    Assign images to each slot using the layered strategy.

    Args:
        prompt: The business description
        slots: List of (slot_name, desired_role) e.g. [("hero", "hero"), ("stylist_1", "staff"), ...]

    Returns:
        AssignmentReport with all assignments and metadata.
    """
    business = _detect_business_category(prompt)
    mapping = INDUSTRY_MAP.get(business, INDUSTRY_MAP["generic"])
    used_ids: set[str] = set()
    report = AssignmentReport()

    for slot_name, desired_role in slots:
        assignment = _assign_single(slot_name, desired_role, business, mapping, used_ids)
        if assignment.source_asset_id:
            used_ids.add(assignment.source_asset_id)
        report.assignments.append(assignment)

    return report


def _assign_single(
    slot_name: str,
    desired_role: str,
    business: str,
    mapping: dict,
    used_ids: set[str],
) -> ImageAssignment:
    """Try exact → fallback → placeholder for a single slot."""

    # ── Tier 1: exact_match ──
    for industry in mapping["exact"]:
        asset = _select_asset_for_role(industry, desired_role, used_ids)
        if asset:
            b64 = _asset_to_base64(asset)
            if b64:
                return ImageAssignment(
                    slot=slot_name,
                    requested_category=f"{business}/{desired_role}",
                    selected_src=b64,
                    asset_status="exact_match",
                    reason=f"Matched industry '{industry}' role '{desired_role}'",
                    source_asset_id=asset["asset_id"],
                    source_industry=industry,
                )
    # Exact match with any role (if specific role not available)
    for industry in mapping["exact"]:
        asset = _select_asset_for_role(industry, desired_role, used_ids)
        # _select_asset_for_role already falls back to any role
        # But we need to try with a fresh approach — just get any asset from this industry
        candidates = [a for a in _get_assets_by_industry(industry)
                      if a["asset_id"] not in used_ids]
        if candidates:
            asset = candidates[0]
            b64 = _asset_to_base64(asset)
            if b64:
                return ImageAssignment(
                    slot=slot_name,
                    requested_category=f"{business}/{desired_role}",
                    selected_src=b64,
                    asset_status="exact_match",
                    reason=f"Exact industry '{industry}' (role '{asset.get('role')}' used for '{desired_role}')",
                    source_asset_id=asset["asset_id"],
                    source_industry=industry,
                )

    # ── Tier 2: category_fallback ──
    for industry in mapping.get("fallback", []):
        candidates = [a for a in _get_assets_by_industry(industry)
                      if a["asset_id"] not in used_ids]
        if candidates:
            asset = candidates[0]
            b64 = _asset_to_base64(asset)
            if b64:
                return ImageAssignment(
                    slot=slot_name,
                    requested_category=f"{business}/{desired_role}",
                    selected_src=b64,
                    asset_status="category_fallback",
                    reason=f"Fallback industry '{industry}' — no exact '{business}' asset for role '{desired_role}'",
                    source_asset_id=asset["asset_id"],
                    source_industry=industry,
                )

    # ── Tier 3: placeholder (never use wrong industry) ──
    placeholder_name = _choose_placeholder(business, desired_role)
    b64 = _placeholder_to_base64(placeholder_name)
    return ImageAssignment(
        slot=slot_name,
        requested_category=f"{business}/{desired_role}",
        selected_src=b64,
        asset_status="placeholder",
        reason=f"No suitable asset for '{business}/{desired_role}' — using placeholder '{placeholder_name}'",
    )


def _choose_placeholder(business: str, desired_role: str) -> str:
    """Map business + role to the best placeholder SVG."""
    if business == "pet" or "pet" in desired_role or "groom" in desired_role:
        return "pet_grooming_placeholder.svg"
    if desired_role in ("staff", "avatar", "stylist"):
        return "avatar_placeholder.svg"
    if desired_role in ("review", "content", "gallery"):
        return "service_placeholder.svg"   # photo-type placeholder, not avatar circle
    if desired_role in ("service", "hero", "space", "store"):
        return "service_placeholder.svg"
    return "service_placeholder.svg"


# ── Pre-assignment: Analyze WXML to discover image slots ───────────────────────

def discover_image_slots_from_html(body_html: str) -> list[tuple[str, str]]:
    """
    Scan RENDERED HTML body for <img> tags and infer slot names + roles.

    This runs AFTER wx:for expansion, so each actual image instance is discovered.
    Returns list of (slot_name, desired_role) tuples.
    """
    import re

    slots: list[tuple[str, str]] = []

    for m in re.finditer(r"<img\b[^>]*>", body_html, re.IGNORECASE | re.DOTALL):
        tag = m.group(0)
        cls_m = re.search(r'class="([^"]*)"', tag)
        classes = (cls_m.group(1) or "").split() if cls_m else []

        # Infer role from class name
        role = "content"
        slot_name = "img"
        for c in classes:
            cl = c.lower()
            if "avatar" in cl:
                role = "staff"
                slot_name = c
                break
            elif "hero" in cl:
                role = "hero"
                slot_name = c
                break
            elif "srv" in cl or "service" in cl:
                role = "service"
                slot_name = c
                break
            elif "review" in cl:
                role = "review"      # use photo-type placeholder, not avatar
                slot_name = c
                break

        # Unique key per slot
        key = f"{slot_name}_{len(slots)}"
        slots.append((key, role))

    return slots


def discover_image_slots(wxml: str) -> list[tuple[str, str]]:
    """
    Fallback: scan pre-expansion WXML. Use discover_image_slots_from_html
    for accurate count after wx:for expansion.
    """
    import re

    slots: list[tuple[str, str]] = []
    seen: set[str] = set()

    for m in re.finditer(r"<image\b[^>]*>", wxml, re.IGNORECASE):
        tag = m.group(0)
        cls_m = re.search(r'class="([^"]*)"', tag)
        classes = (cls_m.group(1) or "").split() if cls_m else []

        role = "content"
        slot_name = "unknown"
        for c in classes:
            cl = c.lower()
            if "avatar" in cl:
                role = "staff"
                slot_name = c
            elif "hero" in cl:
                role = "hero"
                slot_name = c
            elif "product" in cl or "service" in cl or "srv" in cl:
                role = "service"
                slot_name = c
            elif "review" in cl:
                role = "staff"
                slot_name = c

        key = f"{slot_name}_{len([s for s in slots if s[0].startswith(slot_name)])}"
        if key not in seen:
            seen.add(key)
            slots.append((key, role))

    return slots


# ── Apply assignments to HTML body ─────────────────────────────────────────────

def apply_assignments_to_body(body_html: str, report: AssignmentReport) -> str:
    """
    Replace image src attributes in body HTML with assigned images.
    Matches images in order, skipping images that already have data: URIs.
    """
    import re

    assignments = list(report.assignments)
    idx = [0]  # mutable counter

    def replace_src(m):
        i = idx[0]
        if i >= len(assignments):
            return m.group(0)
        # Only replace remote URLs and placeholder patterns, not already-inlined data URIs
        old_src = re.search(r'src="([^"]*)"', m.group(0))
        if old_src and old_src.group(1).startswith("data:"):
            return m.group(0)
        assignment = assignments[i]
        idx[0] += 1
        return re.sub(
            r'src="[^"]*"',
            f'src="{assignment.selected_src}"',
            m.group(0),
        )

    body_html = re.sub(r"<img\b[^>]*>", replace_src, body_html, flags=re.IGNORECASE)
    return body_html
