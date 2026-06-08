from __future__ import annotations

import base64
import io
import mimetypes
import re
from typing import Iterable


UPLOAD_DIR = "assets/uploads"
DEFAULT_HERO_CLASS = "hero-image"

_MIME_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
}


def _ext_from_mime(mime: str | None) -> str:
    mime = (mime or "").lower().split(";")[0].strip()
    if mime in _MIME_EXT:
        return _MIME_EXT[mime]
    guessed = mimetypes.guess_extension(mime or "")
    if guessed in (".jpe", ".jpeg"):
        return ".jpg"
    return guessed or ".jpg"


def preprocess_uploaded_image(raw: bytes, mime: str | None) -> tuple[bytes, str, dict]:
    """Trim obvious screenshot padding before assets are written to the mini-program."""
    mime = (mime or "image/jpeg").lower().split(";")[0].strip()
    if not raw or mime == "image/gif":
        return raw, mime, {"crop_applied": False}

    try:
        from PIL import Image
    except Exception:
        return raw, mime, {"crop_applied": False, "reason": "pillow_unavailable"}

    try:
        with Image.open(io.BytesIO(raw)) as img:
            original_size = img.size
            rgba = img.convert("RGBA")
            box = _find_content_bbox(rgba)
            if not box:
                return raw, mime, {"crop_applied": False, "original_size": original_size}

            left, top, right, bottom = box
            width, height = original_size
            if left <= 1 and top <= 1 and right >= width - 1 and bottom >= height - 1:
                return raw, mime, {"crop_applied": False, "original_size": original_size}

            cropped = img.crop(box)
            out = io.BytesIO()
            fmt = _pil_format_for_mime(mime, img.format)
            if fmt == "JPEG" and cropped.mode in ("RGBA", "LA", "P"):
                bg = Image.new("RGB", cropped.size, (255, 255, 255))
                bg.paste(cropped.convert("RGBA"), mask=cropped.convert("RGBA").getchannel("A"))
                cropped = bg
            save_kwargs = {"quality": 94} if fmt in ("JPEG", "WEBP") else {}
            cropped.save(out, format=fmt, **save_kwargs)
            processed = out.getvalue()
            return (
                processed,
                mime,
                {
                    "crop_applied": True,
                    "original_size": original_size,
                    "processed_size": cropped.size,
                    "crop_box": box,
                },
            )
    except Exception as exc:
        return raw, mime, {"crop_applied": False, "reason": type(exc).__name__}


def _pil_format_for_mime(mime: str, fallback: str | None) -> str:
    if mime in ("image/jpeg", "image/jpg"):
        return "JPEG"
    if mime == "image/png":
        return "PNG"
    if mime == "image/webp":
        return "WEBP"
    if mime == "image/bmp":
        return "BMP"
    return fallback or "PNG"


def _find_content_bbox(img) -> tuple[int, int, int, int] | None:
    width, height = img.size
    if width < 8 or height < 8:
        return None

    alpha_box = img.getchannel("A").point(lambda a: 255 if a > 10 else 0).getbbox()
    if alpha_box and _is_meaningful_crop(alpha_box, width, height):
        return alpha_box

    corners = [
        img.getpixel((0, 0)),
        img.getpixel((width - 1, 0)),
        img.getpixel((0, height - 1)),
        img.getpixel((width - 1, height - 1)),
    ]
    best_box = None
    best_removed = 0
    for bg in corners:
        box = _bbox_different_from_color(img, bg, threshold=22)
        if not box or not _is_meaningful_crop(box, width, height):
            continue
        removed = width * height - (box[2] - box[0]) * (box[3] - box[1])
        if removed > best_removed:
            best_box = box
            best_removed = removed
    return best_box


def _bbox_different_from_color(img, bg: tuple[int, int, int, int], threshold: int) -> tuple[int, int, int, int] | None:
    width, height = img.size
    px = img.load()
    left, top, right, bottom = width, height, -1, -1
    br, bgc, bb, ba = bg
    for y in range(height):
        for x in range(width):
            r, g, b, a = px[x, y]
            if a <= 10:
                continue
            if max(abs(r - br), abs(g - bgc), abs(b - bb), abs(a - ba)) > threshold:
                if x < left:
                    left = x
                if y < top:
                    top = y
                if x > right:
                    right = x
                if y > bottom:
                    bottom = y
    if right < left or bottom < top:
        return None
    pad = 2
    return (max(0, left - pad), max(0, top - pad), min(width, right + pad + 1), min(height, bottom + pad + 1))


def _is_meaningful_crop(box: tuple[int, int, int, int], width: int, height: int) -> bool:
    crop_w = box[2] - box[0]
    crop_h = box[3] - box[1]
    if crop_w < 24 or crop_h < 24:
        return False
    crop_area = crop_w * crop_h
    total = width * height
    if crop_area < total * 0.20:
        return False
    return crop_area <= total * 0.97


def prepare_uploaded_assets(image_list: Iterable[tuple[bytes, str]] | None) -> list[dict]:
    assets: list[dict] = []
    for index, item in enumerate(list(image_list or [])[:20], start=1):
        if not item:
            continue
        raw, mime = item[0], item[1] if len(item) > 1 else "image/jpeg"
        if not raw:
            continue
        raw, mime, image_meta = preprocess_uploaded_image(raw, mime)
        ext = _ext_from_mime(mime)
        asset_id = f"user_upload_{index:03d}"
        rel_path = f"{UPLOAD_DIR}/{asset_id}{ext}"
        assets.append(
            {
                "asset_id": asset_id,
                "path": rel_path,
                "wxml_path": f"/{rel_path}",
                "usage": "user_content_image",
                "role_hint": "hero" if index == 1 else "content",
                "mime": mime or "image/jpeg",
                "data_b64": base64.b64encode(raw).decode("ascii"),
                "preprocess": image_meta,
            }
        )
    return assets


def asset_prompt_block(assets: list[dict]) -> str:
    if not assets:
        return ""
    public = [
        {
            "asset_id": a["asset_id"],
            "path": a["wxml_path"],
            "usage": a.get("usage", "user_content_image"),
            "role_hint": a.get("role_hint", "content"),
        }
        for a in assets
    ]
    return (
        "\n\n【用户上传图片 asset_list】\n"
        f"{public}\n\n"
        "如果 asset_list 中存在 usage=user_content_image 的图片，你必须在 WXML 中使用它。\n"
        "你不能创造新的图片 URL。\n"
        "你不能使用 Unsplash/Picsum/远程图片链接。\n"
        "你不能使用 localhost、127.0.0.1、blob、base64、tmp、streamlit 路径。\n"
        "你只能使用 asset_list 中给定的 path。\n"
        "优先把用户图片放在页面顶部 hero/banner 区域。\n"
        "不要把同一张图片连续重复铺满列表；同一个 path 最多复用 2 次。\n"
    )


def _has_asset_reference(wxml: str, asset: dict) -> bool:
    candidates = {
        asset.get("wxml_path", ""),
        asset.get("path", ""),
        asset.get("path", "").lstrip("/"),
    }
    return any(c and c in (wxml or "") for c in candidates)


def _asset_path(asset: dict) -> str:
    return (asset.get("wxml_path") or asset.get("path") or "").replace("\\", "/")


def _select_fallback_asset(assets: list[dict]) -> dict | None:
    return next((a for a in assets if a.get("role_hint") == "hero" or a.get("role") == "hero"), None) or (assets[0] if assets else None)


def _insert_hero_image(wxml: str, image_path: str) -> str:
    hero = f'<image class="{DEFAULT_HERO_CLASS}" src="{image_path}" mode="widthFix" />'
    text = wxml or ""
    if not text.strip():
        return hero
    m = re.search(r"<view\b[^>]*>", text)
    if m:
        return text[: m.end()] + "\n  " + hero + text[m.end() :]
    return hero + "\n" + text


def _insert_after_opening_view(wxml: str, block: str) -> str:
    text = wxml or ""
    if not text.strip():
        return block
    m = re.search(r"<view\b[^>]*>", text)
    if m:
        return text[: m.end()] + "\n  " + block + text[m.end() :]
    return block + "\n" + text


def _gallery_block(assets: list[dict]) -> str:
    lines = ['<view class="uploaded-gallery">']
    for asset in assets:
        lines.append(
            f'  <image class="uploaded-gallery-image" src="{asset["wxml_path"]}" mode="aspectFill" />'
        )
    lines.append("</view>")
    return "\n".join(lines)


def _ensure_hero_style(wxss: str) -> str:
    text = wxss or ""
    if f".{DEFAULT_HERO_CLASS}" in text:
        return text
    return (
        text.rstrip()
        + "\n\n"
        + f".{DEFAULT_HERO_CLASS} {{\n"
        + "  width: 100%;\n"
        + "  display: block;\n"
        + "  border-radius: 20rpx;\n"
        + "  margin-bottom: 24rpx;\n"
        + "}\n"
    )


def _ensure_gallery_style(wxss: str) -> str:
    text = wxss or ""
    if ".uploaded-gallery" in text:
        return text
    return (
        text.rstrip()
        + "\n\n"
        + ".uploaded-gallery {\n"
        + "  display: flex;\n"
        + "  gap: 16rpx;\n"
        + "  margin: 0 0 24rpx;\n"
        + "  overflow-x: auto;\n"
        + "  white-space: nowrap;\n"
        + "}\n\n"
        + ".uploaded-gallery-image {\n"
        + "  width: 180rpx;\n"
        + "  height: 180rpx;\n"
        + "  flex: 0 0 180rpx;\n"
        + "  display: block;\n"
        + "  border-radius: 18rpx;\n"
        + "  background: #f3f4f6;\n"
        + "}\n"
    )


def _replace_polluted_image_paths(text: str, replacement: str) -> str:
    if not text:
        return text
    patterns = [
        r"blob:[^\"'\s<>]+",
        r"https?://(?:localhost|127\.0\.0\.1)[^\"'\s<>]*",
        r"(?:localhost|127\.0\.0\.1):\d+[^\"'\s<>]*",
        r"/tmp/[^\"'\s<>]*",
        r"data:image/[^\"']+",
        r"https?://(?:images\.unsplash\.com|source\.unsplash\.com|unsplash\.com)[^\"'\s<>]*",
        r"https?://(?:picsum\.photos)[^\"'\s<>]*",
        r"[^\"'\s<>]*streamlit[^\"'\s<>]*",
    ]
    result = text
    for pattern in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def _replace_nth(text: str, old: str, new: str, nth: int) -> str:
    start = -1
    for _ in range(nth):
        start = text.find(old, start + 1)
        if start < 0:
            return text
    return text[:start] + new + text[start + len(old) :]


def _diversify_repeated_asset_paths(text: str, assets: list[dict]) -> str:
    """Rotate repeated local asset paths so generated lists do not show one image everywhere."""
    if not text:
        return text
    paths: list[str] = []
    seen: set[str] = set()
    for asset in assets:
        path = _asset_path(asset)
        if path and path not in seen:
            paths.append(path)
            seen.add(path)
    if len(paths) < 2:
        return text

    result = text
    spare_paths = [path for path in paths if path not in result]
    if not spare_paths:
        spare_paths = paths[1:]

    for path in paths:
        count = result.count(path)
        while count > 1 and spare_paths:
            replacement = spare_paths.pop(0)
            if replacement == path:
                continue
            result = _replace_nth(result, path, replacement, 2)
            count -= 1
    return result


def attach_assets_and_fallback(
    page_files: dict | None,
    assets: list[dict],
    library_assets: list[dict] | None = None,
) -> dict:
    result = dict(page_files or {})
    upload_assets = list(assets or [])
    library_candidates = list(library_assets or [])
    candidate_assets = upload_assets + library_candidates
    if not candidate_assets:
        return result

    wxml = result.get("wxml", "") or ""
    wxss = result.get("wxss", "") or ""
    js = result.get("js", "") or ""
    first = _select_fallback_asset(candidate_assets)
    if not first:
        return result
    first_path = _asset_path(first)
    if not first_path:
        return result

    wxml = _replace_polluted_image_paths(wxml, first_path)
    js = _replace_polluted_image_paths(js, first_path)
    js = _diversify_repeated_asset_paths(js, candidate_assets)

    if not any(_has_asset_reference(wxml, asset) for asset in candidate_assets):
        wxml = _insert_hero_image(wxml, first_path)
        wxss = _ensure_hero_style(wxss)

    missing_assets = [asset for asset in upload_assets[1:] if not _has_asset_reference(wxml, asset)]
    if missing_assets:
        wxml = _insert_after_opening_view(wxml, _gallery_block(missing_assets))
        wxss = _ensure_gallery_style(wxss)

    result["wxml"] = wxml
    result["wxss"] = wxss
    result["js"] = js
    result["assets"] = upload_assets
    result["library_assets"] = library_candidates
    return result


def decode_asset_bytes(asset: dict) -> bytes:
    return base64.b64decode(asset.get("data_b64", ""))


def validation_asset_files(page_files: dict | None) -> dict[str, str]:
    files: dict[str, str] = {}
    for asset in (page_files or {}).get("assets", []) or []:
        asset_path = _asset_path(asset).lstrip("/")
        if asset_path:
            files[asset_path] = ""
    for asset in (page_files or {}).get("library_assets", []) or []:
        asset_path = _asset_path(asset).lstrip("/")
        if asset_path:
            files[asset_path] = ""
    return files


def assets_to_preview_images(assets: list[dict] | None) -> list[tuple[bytes, str]]:
    images: list[tuple[bytes, str]] = []
    for asset in assets or []:
        try:
            images.append((decode_asset_bytes(asset), asset.get("mime") or "image/jpeg"))
        except Exception:
            continue
    return images
