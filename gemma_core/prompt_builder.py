"""Prompt construction helpers for the mini-program generator."""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from image_library import select_image_assets
except Exception:
    def select_image_assets(user_prompt: str, limit: int = 8) -> list[dict]:
        return []

GOLDEN_DIR = BASE_DIR / "golden_examples"
# 高质量「黄金样例」目录（位于仓库根 golden_examples/high_quality），
# 与 gemma_core/golden_examples 的关键词召回池分开，作为专门的 few-shot 学习对象。
HIGH_QUALITY_DIR = REPO_ROOT / "golden_examples" / "high_quality"
CORPUS_INDEX_PATHS = (
    BASE_DIR / "corpus_index.json",
    GOLDEN_DIR / "corpus_index.json",
)

# high_quality 各样例的召回关键词（中文 token 难以靠分词命中，这里显式给出）。
HIGH_QUALITY_KEYWORDS: dict[str, list[str]] = {
    "product_detail": [
        "商品", "详情", "商品详情", "购买", "下单", "价格", "商城", "电商",
        "加购", "购物车", "规格", "product",
    ],
    "event_signup": [
        "活动", "报名", "活动报名", "报名表", "表单", "嘉宾", "日程",
        "峰会", "大会", "沙龙", "讲座", "event", "signup",
    ],
    "store_booking": [
        "门店", "预约", "门店预约", "预订", "到店", "时段", "档期", "服务预约",
        "美容", "美发", "spa", "理发", "booking", "reservation",
    ],
}

_CONSTRAINT_HEAD = """
你是微信小程序 pages/index/index 页面代码生成器。首选通过 create_miniprogram_page 工具返回页面代码; 如果当前运行环境没有工具调用能力, 才严格输出一个 JSON 对象, 只包含 wxml、wxss、js 三个键, 不要输出解释文字。

约束清单:
- 只用基础组件: view, text, image, button, input, textarea, form, scroll-view, swiper, swiper-item, block。
- 禁用 HTML 标签, 包括 div、span、p、a、img、ul、li 等。
- 禁止在 {{}} 里调用函数或表达式方法; 需要格式化的数据必须先在 JS data 中准备好。
- swiper 必须使用 current 属性, 禁止使用 current-index。
- 禁止调用真实能力 API: wx.login、wx.request、wx.requestPayment、wx.getLocation、wx.cloud。
- 数据必须使用本地 mock, 写在 JS 的 data 中。
- 必须全量输出三个文件内容, 分别对应 pages/index/index.wxml、pages/index/index.wxss、pages/index/index.js。
""".strip()

# 标准完整度（Google AI Studio · agent 模式）：受 maxOutputTokens=16384 限制，
# 总量控制在 ~570-850 行，确保完整闭合不被截断。
_COMPLETENESS_STANDARD = """
代码完整度要求（覆盖完整 > 行数堆砌——按页面复杂度灵活把握，禁止为了凑数而注水或堆砌无意义内容）:
- WXML: 覆盖「顶部 Banner/轮播」「分类筛选 Tab」「主内容网格（6+卡片）」「推荐/统计区块」「底部固定操作栏」五大区域，结构写全通常在 150-220 行左右，区域不全比行数不够更糟。
- WXSS: 完整的卡片样式、渐变色、圆角、阴影、active 状态动画、骨架屏占位、响应式布局，写全通常在 300-450 行左右。
- JS data: 丰富 mock——至少 4 个数组（每个 6-8 条目）+ 多层嵌套对象 + 完整状态管理字段，写全通常在 120-180 行左右。
- 图片: JS data 的每条数据可以有 image 字段，但最终路径必须来自下方 asset_list；禁止自创或补充远程图片 URL。
- 图片最终以本地 asset_list 为准：即使参考样例或旧说明里出现 Unsplash，也不能在最终代码里使用远程图片 URL。
- 交互完整: tab 切换（bindtap + data-* 传参）、数量增减、收藏/点赞、加购物车（在 JS methods 实现）。
""".strip()

# 深度完整度（AMD vLLM 自托管 31B · deep 模式）：自托管网关上下文/输出预算更宽裕，
# 不存在云端按量限流的顾虑，应该把模型的长输出能力真正用起来——总量目标 ~1300-1800 行，
# 比标准档明显更丰富，但仍要求「内容真实完整」而不是机械重复注水。
_COMPLETENESS_DEEP = """
代码完整度要求（自托管长上下文模型，预算充足——把篇幅花在「内容更丰富」而不是「重复注水」上）:
- WXML: 在标准五大区域基础上再扩展更多真实区块（如多组横向滑动卡片、标签云、用户评价/口碑区、常见问题、相关推荐二级列表、空状态/加载态占位等），整体写全通常在 300-420 行左右。
- WXSS: 覆盖每个区块的精细样式、多套配色层次、悬浮/按压/加载态动画、骨架屏占位、深色模式适配，整体写全通常在 650-900 行左右。
- JS data: 至少 6-8 个数组（每个 8-12 条目，字段丰富、数据有真实感）+ 多层嵌套对象 + 完整状态管理字段，整体写全通常在 350-500 行左右。
- 图片: JS data 的每条数据可以有 image 字段，但最终路径必须来自下方 asset_list；禁止自创或补充远程图片 URL。
- 图片最终以本地 asset_list 为准：即使参考样例或旧说明里出现 Unsplash，也不能在最终代码里使用远程图片 URL。
- 交互丰富且真实: tab 切换、筛选/排序、数量增减、收藏/点赞、加购物车、弹窗/抽屉、表单校验等都要在 JS methods 中真实实现，不要只摆样子。
- 总量目标：三个文件合计 ~1300-1800 行的充实程度——结构完整、信息密度高，每一段都承载真实可信的内容，而不是为了凑数堆砌空壳区块或重复条目。
""".strip()

_DESIGN_SPEC = """
设计排版规范（必须遵守）:
- 间距系统: 使用 8rpx 的整数倍——section 间距 40-48rpx，card 内边距 24-32rpx，元素间距 16-24rpx，避免随意数值。
- 字号层级: 大标题 40-48rpx font-weight:900，小标题 28-32rpx font-weight:700，正文 24-26rpx，辅助说明 20-22rpx color:#888，层级清晰可辨。
- 卡片规范: 每张卡片必须有 border-radius(16-24rpx) + box-shadow(0 4rpx 16rpx rgba(0,0,0,.08)) + overflow:hidden，图片区高度 180-240rpx。
- 色彩体系: 定义主色（如 #1a73e8）+ 辅色 + 背景色（如 #f5f7fa）+ 文字色（#1a1a1a / #666 / #999），全页面一致不混用。
- CTA 按钮: 主按钮高度 ≥ 88rpx，用渐变背景（linear-gradient），圆角 ≥ 16rpx，字重 700，阴影增强点击感。
- 列表项: 每条数据要包含图片 + 标题 + 副文本 + 操作控件（价格/按钮/标签），不要只有文字。
""".strip()


def _constraint_checklist(mode: str = "agent") -> str:
    """Assemble the constraint block; `deep` (self-hosted AMD 31B) gets a richer
    completeness target since its context/output budget isn't rate-limited like
    the cloud-hosted Google path."""
    completeness = _COMPLETENESS_DEEP if mode == "deep" else _COMPLETENESS_STANDARD
    return f"{_CONSTRAINT_HEAD}\n\n{completeness}\n\n{_DESIGN_SPEC}"


# Backward-compatible default (agent / Google path) — kept as a module-level
# constant since other call sites (eval_harness, generator, tests) reference it
# without knowing about `mode`.
CONSTRAINT_CHECKLIST = _constraint_checklist("agent")

HIGH_QUALITY_GUIDANCE = """
【如何使用下方「高质量黄金样例」——必须遵守】
1. 黄金样例只是「学习对象」，不是「填空模板」。要学的是：页面结构与视觉层级、卡片化布局质量、
   「顶部 HeroBanner + 内容区 + 底部 fake tabBar」的组织方式、三类基础交互（tab 点击切换 activeTab、
   input 双向绑定、button 触发 wx.showToast）的实现写法，以及小程序代码规范。
2. 严禁照搬：不得复制样例里的任何文案、商品/品牌名、配色、图片路径或固定布局骨架。
   若输出与样例文案或配色雷同，视为不合格。
3. 强制重组：必须依据「用户需求」重新挑选并组合页面模块——需要的区块要补，不相关的区块要删，
   区块顺序与层级按真实场景重排，而不是套用样例的固定结构。
4. 交互要求：至少各出现一次三类基础交互，但要落在符合本次场景的位置，不要机械照抄样例里的交互位置。
5. 代码规范向样例看齐：命名清晰、派生文案先在 JS data/方法里算好、WXML 的 {{}} 内不写方法调用、
   事件 handler 名与 JS 方法一一对应、卡片统一圆角与阴影。
6. 完整度对齐样例：产出一个结构完整、细节丰富的高质量页面（与样例同等体量、~1500-2000 行的充实程度），
   覆盖顶部 Banner、多个内容区块、丰富 mock 数据与完整交互，把质量与信息密度做足。
""".strip()

_STYLE_POOL = [
    "视觉风格：清爽白底，蓝色主色调，圆角卡片，适合通用电商/工具类。",
    "视觉风格：温暖米色系，橙红点缀，适合餐饮/生活类场景。",
    "视觉风格：深色夜间模式，渐变紫蓝，现代科技感。",
    "视觉风格：极简主义，大量留白，细线条，高级感商务定位。",
    "视觉风格：活力橙黄，圆润图标，面向年轻消费者。",
    "视觉风格：绿色清新，自然系，适合健康/运动/户外。",
]

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


def build_prompt(user_prompt: str, style_hint: str | None = None, asset_list: list[dict] | None = None) -> str:
    """Build a few-shot prompt from golden_examples and the user request."""
    # 高质量黄金样例：作为唯一的主 few-shot 学习对象（最相关的 1 个，带强约束）。
    # 这些样例本身已是 ~2000+ 行的完整高质量页面，单个就足以教学；
    # 仅当没有高质量样例时，才回退到普通召回池补 1 个，以控制上下文体积、避免请求过大。
    hq_example = _select_high_quality(user_prompt, _load_high_quality_examples())
    pool = [] if hq_example else _select_examples(user_prompt, _load_examples(), limit=1)

    # Random style direction: nudges Gemma to make distinct design decisions
    hint = style_hint or random.choice(_STYLE_POOL)

    parts = [CONSTRAINT_CHECKLIST]
    if hq_example:
        parts.append(HIGH_QUALITY_GUIDANCE)
        parts.append(
            "【高质量黄金样例 · 学习对象】"
            "（学习其结构 / 层级 / 交互 / 规范，严禁照搬文案、配色、图片路径与固定布局）："
        )
        parts.append(_format_example(hq_example))
    if pool:
        parts.append("参考样例(few-shot)（仅作结构参考，禁止照搬配色和布局）:")
        for example in pool:
            parts.append(_format_example(example))

    parts.append(f"设计要求（自主发挥，体现差异化）：{hint}")

    library_assets = select_image_assets(user_prompt, limit=8)
    combined_assets = list(asset_list or [])
    seen_paths = {
        (a.get("wxml_path") or a.get("path") or "").replace("\\", "/")
        for a in combined_assets
    }
    for asset in library_assets:
        path = (asset.get("wxml_path") or asset.get("path") or "").replace("\\", "/")
        if path and path not in seen_paths:
            combined_assets.append(asset)
            seen_paths.add(path)

    if combined_assets:
        public_assets = [
            {
                "asset_id": a.get("asset_id"),
                "path": a.get("wxml_path") or a.get("path"),
                "usage": a.get("usage", "user_content_image"),
                "role_hint": a.get("role_hint", "content"),
                "industry": a.get("industry"),
                "role": a.get("role"),
                "style": a.get("style"),
                "tags": a.get("tags", []),
            }
            for a in combined_assets[:12]
        ]
        parts.append(
            "本地图片 asset_list（唯一允许使用的图片来源）:\n"
            + json.dumps(public_assets, ensure_ascii=False, indent=2)
            + "\n\n"
            "图片硬规则：WXML 的 image src 只能使用 asset_list 中给定的 path。\n"
            "允许路径只包括 /assets/library/... 或 /assets/uploads/...。\n"
            "禁止创造新的图片 URL，禁止使用 Unsplash/Picsum/远程 http(s) 图片。\n"
            "禁止使用 localhost、127.0.0.1、blob、base64、tmp、streamlit 路径。\n"
            "如果 asset_list 中存在 usage=user_content_image 的图片，必须优先放在页面顶部 hero/banner 区域。\n"
            "如果没有用户上传图片，请从 role=hero 的 library_image 中选择一张作为顶部主视觉。"
        )
    parts.append("用户需求:")
    parts.append(user_prompt.strip())
    return "\n\n".join(parts).strip() + "\n"


CLARIFY_TEMPLATE = """\
你是一位资深微信小程序产品经理。用户描述了一个初步的小程序需求，请深入理解用户意图，针对这个具体需求提出 2-3 个最关键的澄清问题，每个问题给出 3 个具体的选项供用户快速选择。

输出格式（严格 JSON 数组，不输出任何其他内容，不加 markdown 代码块）：
[
  {{"q": "针对用户需求的具体问题（15字以内）", "a": "选项一（具体内容，10字以内）", "b": "选项二（具体内容，10字以内）", "c": "选项三（具体内容，10字以内）"}},
  ...
]

核心要求：
- 问题必须针对「{user_input}」这个具体需求，不要问与该需求无关的通用问题
- 三个选项要有明显差异，覆盖最常见的几种方向
- 选项直接写内容，不加 A/B/C 前缀

用户需求：{user_input}
"""

_DEFAULT_CLARIFY_QUESTIONS = [
    {"q": "主要使用场景？", "a": "商品展示与购买", "b": "活动报名预约", "c": "内容浏览收藏"},
    {"q": "目标用户群体？", "a": "年轻消费者（18-35岁）", "b": "商务职场人士", "c": "全年龄通用"},
    {"q": "视觉风格偏好？", "a": "简约白底，专业感", "b": "活泼多彩，年轻化", "c": "深色高端，科技感"},
]


def parse_clarify_questions(text: str) -> list[dict]:
    """Parse structured question+options list from Gemma's JSON response."""
    import json as _json
    import re as _re
    # Strip markdown code fences if present
    text = _re.sub(r'```(?:json)?\s*', '', text).strip()
    m = _re.search(r'\[.*\]', text, _re.DOTALL)
    if m:
        try:
            qs = _json.loads(m.group(0))
            if isinstance(qs, list) and qs:
                valid = [
                    q for q in qs[:3]
                    if isinstance(q, dict)
                    and all(k in q for k in ("q", "a", "b", "c"))
                ]
                if valid:
                    return valid
        except Exception:
            pass
    return [q.copy() for q in _DEFAULT_CLARIFY_QUESTIONS]


def build_enriched_prompt(
    original: str,
    qa_pairs: list[tuple[str, str]],
    image_count: int = 0,
    style_hint: str | None = None,
    asset_list: list[dict] | None = None,
) -> str:
    """Build generation prompt from original intent + clarification Q&A + optional images."""
    base = build_prompt(original, style_hint=style_hint, asset_list=asset_list)
    answered = [(q, a) for q, a in qa_pairs if a and a.strip()]
    if answered:
        qa_lines = "\n".join(f"- {q}：{a}" for q, a in answered)
        base += f"\n\n需求补充（来自用户确认）：\n{qa_lines}"
    if image_count == 1:
        base += (
            "\n\n【多模态输入】用户上传了 1 张参考图片（附在消息中）。"
            "请仔细分析图片内容和视觉风格，优先将这张图片作为页面顶部 HeroBanner 的主视觉，"
            "但 WXML 的 image src 只能使用上方 asset_list 中的 /assets/uploads/... 本地路径。"
            "在 WXSS 中参考图片的配色方案。"
        )
    elif image_count > 1:
        base += (
            f"\n\n【多模态输入】用户上传了 {image_count} 张参考图片（附在消息中）。"
            "请逐一分析每张图片的内容：\n"
            "- 商品/产品图 → 作为轮播图或商品主图，在 image src 填入对应的 /assets/uploads/... 本地路径\n"
            "- UI 设计稿/截图 → 参考其布局结构和组件设计\n"
            "- 背景/场景图 → 提取配色用于 WXSS\n"
            "- 图标/logo → 用于头像区或导航区\n"
            "所有图片都应有实际用途，但 WXML 的 image src 只能使用上方 asset_list 中给出的本地路径。"
        )
    return base


_REVIEW_CHECKLIST = """
你是微信小程序 pages/index/index 页面代码生成器。
立即通过 create_miniprogram_page 工具输出完整最终版本，不要输出任何解释文字。

基于草稿代码升级为高质量完整版，升级目标（直接在输出代码中体现，无需说明）：
1. 内容完整、结构丰富而不是行数堆砌：JS mock 数据每个数组扩至 6-8 条，每条含 6+ 字段；WXML 按需补齐缺失的内容区块（推荐卡片、统计数字、功能入口网格）——目标是"信息完整可信"，不要为了拉长行数而堆砌无意义内容
2. JS data 任意数组条目 < 4 → 补充至 6-8 条，数据有真实感（真实城市/品牌/价格）
3. 若缺少底部固定操作栏 → 补充（购买/提交/寄件等场景适配按钮）
4. 检查所有 image src：最终只能保留 /assets/library/... 或 /assets/uploads/... 本地项目路径，不要补远程 URL
5. 图片 URL 若为占位符/Unsplash/Picsum/localhost/blob/base64/tmp → 删除或替换为当前代码里已有的本地项目图片路径
6. 补充 active/selected 状态样式（tab 高亮、按钮按压效果）
7. 所有卡片加 box-shadow 和 border-radius（16-24rpx 圆角 + rgba 阴影）

必须通过 create_miniprogram_page 工具返回完整 wxml + wxss + js，禁止输出任何 JSON 以外的文字。
""".strip()


def build_review_prompt(user_prompt: str, page_files: dict) -> str:
    """Second-pass self-review prompt: polish quality without changing scope."""
    normalized = _normalize_page_files(page_files)
    wxml_l = len(normalized["wxml"].splitlines())
    wxss_l = len(normalized["wxss"].splitlines())
    js_l   = len(normalized["js"].splitlines())
    total  = wxml_l + wxss_l + js_l
    code_json = json.dumps(normalized, ensure_ascii=False, indent=2)
    return (
        f"{_REVIEW_CHECKLIST}\n\n"
        f"原始用户需求：{user_prompt.strip()}\n"
        f"当前代码量：WXML {wxml_l}行 · WXSS {wxss_l}行 · JS {js_l}行 · 共 {total}行\n\n"
        f"待审核代码：\n{code_json}\n"
    )


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


_HIGH_QUALITY_TITLES = {
    "product_detail": "高级商品详情页",
    "event_signup": "高级活动报名页",
    "store_booking": "高级门店预约页",
}


def _load_high_quality_examples() -> list[dict[str, Any]]:
    """加载 golden_examples/high_quality 下的高质量黄金样例（专用 few-shot 学习对象）。"""
    examples: list[dict[str, Any]] = []
    if not HIGH_QUALITY_DIR.exists():
        return examples

    for sample_dir in sorted(p for p in HIGH_QUALITY_DIR.iterdir() if p.is_dir()):
        files = _read_example_files(sample_dir)
        if not all(files.values()):
            continue
        name = sample_dir.name
        title = _HIGH_QUALITY_TITLES.get(name, name)
        examples.append(
            {
                "id": name,
                "title": title,
                "prompt": title,
                "keywords": HIGH_QUALITY_KEYWORDS.get(name, list(_tokens(name))),
                "files": files,
            }
        )
    return examples


def _select_high_quality(
    user_prompt: str, examples: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """按关键词命中数挑出最相关的 1 个高质量样例；无命中则回退首个（保证总有学习对象）。"""
    if not examples:
        return None
    prompt_lower = user_prompt.lower()
    best, best_score = None, -1
    for ex in examples:
        score = sum(1 for kw in ex.get("keywords", ()) if str(kw).lower() in prompt_lower)
        if score > best_score:
            best, best_score = ex, score
    return best or examples[0]


def _load_examples() -> list[dict[str, Any]]:
    index = _load_first_json(CORPUS_INDEX_PATHS)
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


def _load_first_json(paths: tuple[Path, ...]) -> Any:
    for path in paths:
        data = _load_json(path)
        if data is not None:
            return data
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
    prompt_lower = user_prompt.lower()
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for example in examples:
        keywords = set(example.get("keywords") or ())
        text_tokens = _tokens(
            " ".join([example["id"], example.get("title", ""), example.get("prompt", "")])
        )
        score = len(query_tokens & (keywords | text_tokens))
        score += _substring_score(prompt_lower, keywords)
        score += _substring_score(prompt_lower, text_tokens)
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


def _substring_score(prompt_lower: str, candidates: set[str]) -> int:
    score = 0
    for candidate in candidates:
        item = str(candidate).lower().strip()
        if len(item) < 2:
            continue
        if item in prompt_lower:
            score += 2
    return score


def _format_example(example: dict[str, Any]) -> str:
    # 完整注入黄金样例（不截断）：让模型学到完整的高质量结构与 CSS。
    # 单个高质量样例 ~18K tokens，配合后端 64K 上下文 + 16K 输出可容纳。
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
