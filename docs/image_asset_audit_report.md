# MiniPilot Agent Image Asset Audit

## Original Image Sources

- `gemma_core/prompt_builder.py`: legacy prompt rules listed Unsplash photo IDs and encouraged generated remote URLs. This was a model-hallucination risk because the images were not mini-program project files.
- `golden_examples/high_quality/*` and `gemma_core/golden_examples/*`: several examples used `https://images.unsplash.com/...` URLs inside JS mock data. These were remote references, not bundled assets.
- `render_wxml.py`: browser-only preview fallback used Picsum placeholders. These were only for iframe preview, not real mini-program assets.
- `assets/uploads`: user-uploaded images are prepared as `assets/uploads/user_upload_###.ext` and added to the generated project by backend code.
- `assets/library`: newly created curated local asset library. Referenced images are copied into the final Zip and preview projectPath as real project files.
- `demo_cache` and `dev_artifacts`: historical generated previews and diagnostics; not authoritative runtime sources.

## Remote Validation

- Remote image-like candidates checked: 262
- Valid HTTP 200 image responses: 169
- Invalid/template/non-image responses: 93
- Invalid examples include incomplete templates such as `https://picsum.photos/seed/{seed}/375/200` and placeholder Unsplash formats such as `photo-{ID}`.

## Local Library

- Manifest: `assets/library/assets_manifest.json`
- Total local library assets: 27
- Coverage: `coffee`, `restaurant`, `beauty`, `fashion`, `education`, `wedding`, `store_service`, `product_general`, `event_signup`
- Each category has 3 assets.

Example manifest entry:

```json
{
  "asset_id": "coffee_hero_001",
  "local_path": "/assets/library/coffee/coffee_hero_001.jpg",
  "industry": "coffee",
  "role": "hero",
  "style": "warm editorial cafe",
  "tags": ["coffee", "cafe", "hero"],
  "aspect_ratio": 1.4975,
  "source": "unsplash_existing_project_reference",
  "source_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=900&q=80",
  "attribution": "Unsplash image URL already present in this project; photographer metadata was not stored in the legacy reference."
}
```

## New Runtime Rules

- `prompt_builder` injects only 5-8 selected local candidates from `asset_list`.
- Allowed WXML image paths are `/assets/library/...` and `/assets/uploads/...`.
- The model is explicitly forbidden from creating Unsplash/Picsum/remote/localhost/blob/tmp/base64 image URLs.
- If uploaded images exist, the first upload is the hero priority.
- If no upload exists and the model omits images, backend inserts a `role=hero` library image.
- Browser preview inlines `/assets/library/...` files as data URIs only for iframe rendering; real WXML still keeps project paths.
- Zip export includes all uploaded assets plus the library assets referenced by the generated page.
- Existing miniprogram-ci preview workspace copies the same referenced library assets to keep `projectPath` consistent with the Zip while staying below WeChat preview package limits.
