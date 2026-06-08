from __future__ import annotations

import hashlib
import io
import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "assets" / "library"
MANIFEST = LIB_DIR / "assets_manifest.json"


REMOTE_ASSETS = [
    ("coffee_hero_001", "coffee", "hero", "warm editorial cafe", ["coffee", "cafe", "hero"], "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=900&q=80"),
    ("coffee_product_001", "coffee", "product", "clean product closeup", ["coffee", "beans", "product"], "https://images.unsplash.com/photo-1497515114629-f71d768fd07c?w=900&q=80"),
    ("coffee_store_001", "coffee", "store", "cozy shop interior", ["coffee", "store", "interior"], "https://images.unsplash.com/photo-1498804103079-a6351b050096?w=900&q=80"),
    ("restaurant_hero_001", "restaurant", "hero", "fine dining warm", ["restaurant", "food", "hero"], "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=900&q=80"),
    ("restaurant_product_001", "restaurant", "product", "dish closeup", ["restaurant", "dish", "menu"], "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=900&q=80"),
    ("restaurant_store_001", "restaurant", "store", "table atmosphere", ["restaurant", "table", "service"], "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=900&q=80"),
    ("beauty_hero_001", "beauty", "hero", "premium salon", ["beauty", "salon", "hero"], "https://images.unsplash.com/photo-1633681926022-84c23e8cb2d6?w=900&q=80"),
    ("beauty_service_001", "beauty", "service", "hair styling", ["beauty", "hair", "service"], "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=900&q=80"),
    ("beauty_product_001", "beauty", "product", "beauty detail", ["beauty", "makeup", "detail"], "https://images.unsplash.com/photo-1522337660859-02fbefca4702?w=900&q=80"),
    ("fashion_hero_001", "fashion", "hero", "fashion editorial", ["fashion", "hero", "lookbook"], "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=900&q=80"),
    ("fashion_product_001", "fashion", "product", "apparel detail", ["fashion", "product", "apparel"], "https://images.unsplash.com/photo-1445205170230-053b83016050?w=900&q=80"),
    ("fashion_store_001", "fashion", "store", "boutique display", ["fashion", "store", "boutique"], "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=900&q=80"),
    ("wedding_hero_001", "wedding", "hero", "fine art wedding", ["wedding", "hero", "romantic"], "https://images.unsplash.com/photo-1519741497674-611481863552?w=900&q=80"),
    ("wedding_event_001", "wedding", "event", "ceremony scene", ["wedding", "ceremony", "event"], "https://images.unsplash.com/photo-1532712938310-34cb3982ef74?w=900&q=80"),
    ("wedding_detail_001", "wedding", "detail", "wedding detail", ["wedding", "detail", "dress"], "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=900&q=80"),
    ("store_service_hero_001", "store_service", "hero", "service desk", ["store", "service", "hero"], "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=900&q=80"),
    ("store_service_staff_001", "store_service", "staff", "professional portrait", ["store", "staff", "service"], "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=900&q=80"),
    ("store_service_space_001", "store_service", "space", "workspace interior", ["store", "space", "service"], "https://images.unsplash.com/photo-1497366216548-37526070297c?w=900&q=80"),
    ("product_general_hero_001", "product_general", "hero", "clean product commerce", ["product", "commerce", "hero"], "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=900&q=80"),
    ("product_general_grid_001", "product_general", "product", "product grid", ["product", "grid", "shop"], "https://images.unsplash.com/photo-1574269909862-7e1d70bb8078?w=900&q=80"),
    ("product_general_detail_001", "product_general", "detail", "premium product detail", ["product", "detail", "commerce"], "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=900&q=80"),
    ("event_signup_hero_001", "event_signup", "hero", "conference audience", ["event", "signup", "hero"], "https://images.unsplash.com/photo-1521017432531-fbd92d768814?w=900&q=80"),
    ("event_signup_speaker_001", "event_signup", "speaker", "speaker portrait", ["event", "speaker", "signup"], "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=900&q=80"),
    ("event_signup_venue_001", "event_signup", "venue", "business venue", ["event", "venue", "signup"], "https://images.unsplash.com/photo-1497366216548-37526070297c?w=900&q=80"),
]


GENERATED_ASSETS = [
    ("education_hero_001", "hero", "deep blue learning dashboard", ["education", "course", "hero"], ("#17324d", "#f4c95d")),
    ("education_course_001", "course", "clean course card", ["education", "lesson", "course"], ("#f7f4ec", "#3d6f88")),
    ("education_teacher_001", "teacher", "mentor profile panel", ["education", "teacher", "profile"], ("#283618", "#dda15e")),
]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "GemmaMatchAssetLibrary/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get("content-type", "")
        if resp.status != 200 or "image" not in content_type.lower():
            raise RuntimeError(f"invalid image response {resp.status} {content_type}: {url}")
        return resp.read()


def save_remote(asset_id: str, industry: str, role: str, style: str, tags: list[str], url: str) -> dict:
    raw = fetch(url)
    with Image.open(io.BytesIO(raw)) as img:
        img = img.convert("RGB")
        local = f"assets/library/{industry}/{asset_id}.jpg"
        out_path = ROOT / local
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, "JPEG", quality=88, optimize=True)
        width, height = img.size
    return {
        "asset_id": asset_id,
        "local_path": f"/{local}",
        "industry": industry,
        "role": role,
        "style": style,
        "tags": tags,
        "aspect_ratio": round(width / height, 4),
        "source": "unsplash_existing_project_reference",
        "source_url": url,
        "attribution": "Unsplash image URL already present in this project; photographer metadata was not stored in the legacy reference.",
        "sha256": hashlib.sha256((ROOT / local).read_bytes()).hexdigest(),
    }


def save_generated(asset_id: str, role: str, style: str, tags: list[str], colors: tuple[str, str]) -> dict:
    industry = "education"
    local = f"assets/library/{industry}/{asset_id}.jpg"
    out_path = ROOT / local
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1200, 800), colors[0])
    draw = ImageDraw.Draw(img)
    for i in range(9):
        x0 = 80 + i * 120
        draw.rounded_rectangle((x0, 120 + (i % 3) * 90, x0 + 180, 520 + (i % 2) * 60), radius=26, outline=colors[1], width=5)
    draw.rounded_rectangle((120, 560, 1080, 690), radius=36, fill=colors[1])
    draw.rectangle((170, 600, 780, 625), fill=colors[0])
    draw.rectangle((170, 645, 520, 665), fill=colors[0])
    img.save(out_path, "JPEG", quality=90, optimize=True)
    return {
        "asset_id": asset_id,
        "local_path": f"/{local}",
        "industry": industry,
        "role": role,
        "style": style,
        "tags": tags,
        "aspect_ratio": 1.5,
        "source": "generated_local",
        "source_url": "",
        "attribution": "Generated locally for Gemma Match education placeholder assets.",
        "sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    LIB_DIR.mkdir(parents=True, exist_ok=True)
    assets = []
    for spec in REMOTE_ASSETS:
        assets.append(save_remote(*spec))
    for spec in GENERATED_ASSETS:
        assets.append(save_generated(*spec))
    manifest = {
        "version": 1,
        "generated_by": "scripts/build_image_library.py",
        "asset_count": len(assets),
        "allowed_roots": ["/assets/library/", "/assets/uploads/"],
        "assets": assets,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(assets)} assets to {MANIFEST}")


if __name__ == "__main__":
    main()
