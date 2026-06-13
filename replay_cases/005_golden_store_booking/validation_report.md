# Replay Case 005 — 验证报告

最终回归结果（2026-06-12，Round 4 修复后）。

---

## Static Validation

| 类别 | 结果 |
|------|------|
| Footer stability | ✅ PASS |
| Tabbar horizontal | ✅ PASS (4 tabs, y 坐标一致) |
| Image quality | ✅ PASS (27/29 loaded, 93%) |
| Unsplash check | ✅ PASS (0 found) |
| Runtime shim | ✅ PASS (Page + __wx + setData/__updateDOM) |
| Event bindings | ✅ PASS (onclick + oninput) |
| Carousel sync | ✅ PASS (__updateSwiperCounter present) |
| Summary sync | ✅ PASS (data-wx-text bindings) |
| Avatar constraints | ✅ PASS |
| Half-page prevention | ✅ PASS (min-height:380px) |
| **Overall** | **PASS (20P/0F/3W)** |

## Playwright Validation

| 检查项 | 结果 | 详情 |
|--------|------|------|
| footer_at_bottom | ✅ PASS | delta=0px |
| tabbar_horizontal | ✅ PASS | y0=1207 y1=1207 |
| tabbar_count | ✅ PASS | found 4 |
| no_horizontal_overflow | ✅ PASS | sw=359 cw=359 |
| images_loaded | ✅ PASS | 27/29 |
| no_unsplash_in_img | ✅ PASS | 0 found |
| tab_1_not_blank | ✅ PASS | service tab 有内容 |
| tab_2_not_blank | ✅ PASS | cases tab 有内容 |
| tab_3_not_blank | ✅ PASS | mine tab 有内容 |
| form_fillable | ✅ PASS | input filled |
| **Overall** | **PASS (10P/0F)** | |

## 增强验证 (test_residual_fixes.py)

| 检查项 | 结果 | 详情 |
|--------|------|------|
| C1 booking CTA home | ✅ PASS | 确认预约 visible |
| C2 service CTA hidden | ✅ PASS | display=none |
| C3 cases CTA hidden | ✅ PASS | display=none |
| C4 mine CTA hidden | ✅ PASS | display=none |
| C5 page height | ✅ PASS | scrollHeight=638px |
| C6 tabbar always visible | ✅ PASS | display=grid |

## Carousel 逐图验证

| Slide | Natural Size | Display Size | Hero | Status |
|-------|-------------|-------------|------|--------|
| 0 | 900×600 | 359×350 | 350px | ✅ CONTAINED |
| 1 | 900×1350 (竖版) | 359×350 | 350px | ✅ CONTAINED |
| 2 | 900×601 | 359×350 | 350px | ✅ CONTAINED |

Swiper 图片全部使用 `position:absolute; object-fit:cover` — 竖版图片安全裁剪，不污染布局。

---

## 结论

Case 005 通过全部静态和 Playwright 验证，是唯一一个所有 tab 有真实内容、零泄漏、零结构性缺陷的案例。可作为 Golden Case 冻结。
