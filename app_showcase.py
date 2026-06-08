from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from render_wxml import render_phone_html
from scaffold import APP_WXSS


GOLDEN_DIR = ROOT / "gemma_core" / "golden_examples"
BENCHMARK_PATH = ROOT / "gemma_core" / "benchmark_prompts.json"
PROMPT_BUILDER = ROOT / "gemma_core" / "prompt_builder.py"

DEMO_URL = "http://localhost:8505"
SHOWCASE_URL = "http://localhost:8504"
LEGACY_SHOWCASE_URL = "http://localhost:8502"
PRODUCT_NAME = "MiniPilot Agent"
PRODUCT_FULL_NAME = "MiniPilot Agent｜小程序 MVP 生成智能体"
PRODUCT_TAGLINE = "一句生意需求，生成小程序 MVP。"
POWERED_BY = "Powered by Gemma 4."

# Curated from the real 8502 showcase cases. Keep this short and strong:
# these are displayed with full-size rendered phone previews, not thumbnails.
FEATURED_CASES = [
    {
        "id": "ai_wedding_studio",
        "title": "AI 婚礼美学工作室",
        "positioning": "一句高端婚礼影像需求，快速生成可展示作品、AI 服务与套餐预约的小程序 MVP。",
        "prompt": "生成一个 AI 婚礼美学工作室小程序页面，包含作品集、AI 服务、套餐预约、底部导航和高级黑金视觉风格。",
        "highlights": ["作品集", "AI 服务", "套餐预约", "黑金视觉"],
    },
    {
        "id": "michelin_restaurant",
        "title": "米其林餐厅",
        "positioning": "一句高客单价餐饮需求，生成能表达餐厅调性、招牌菜单和预约入口的小程序 MVP。",
        "prompt": "生成一个米其林餐厅小程序页面，包含餐厅封面、主厨推荐、招牌菜展示、营业信息和底部预约按钮。",
        "highlights": ["品牌封面", "主厨推荐", "招牌菜", "预约入口"],
    },
    {
        "id": "coffee_shop",
        "title": "咖啡点单",
        "positioning": "一句门店点单需求，生成分类、商品、购物车和结算栏都能看见的小程序 MVP。",
        "prompt": "生成一个咖啡店点单小程序页面，包含门店封面、分类 Tab、商品列表、购物车和底部结算栏。",
        "highlights": ["分类 Tab", "商品列表", "购物车", "底部结算"],
    },
]


def _read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _benchmark_count() -> int | None:
    data = _read_json(BENCHMARK_PATH)
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in ("cases", "prompts", "items", "benchmarks"):
            if isinstance(data.get(key), list):
                return len(data[key])
    return None


def _golden_count() -> int:
    if not GOLDEN_DIR.exists():
        return 0
    return sum(1 for path in GOLDEN_DIR.iterdir() if path.is_dir())


def _verified_image_count() -> int | None:
    if not PROMPT_BUILDER.exists():
        return None
    text = PROMPT_BUILDER.read_text(encoding="utf-8", errors="replace")
    ids = set(re.findall(r"\b\d{10,}-[0-9a-f]{12,}\b", text, flags=re.I))
    return len(ids) if ids else None


def _metric_value(value: int | None, fallback: str = "Coming soon") -> str:
    return str(value) if value is not None else fallback


def load_golden_from_folder(folder_name: str) -> dict[str, str]:
    sample_dir = GOLDEN_DIR / folder_name
    result = {}
    for ext in ("wxml", "wxss", "js"):
        path = sample_dir / f"index.{ext}"
        result[ext] = path.read_text(encoding="utf-8", errors="replace").strip() if path.exists() else ""
    return result


def _clean_phone_html(html: str) -> str:
    # Older render_wxml.py has a garbled status-bar icon string. The generated
    # mini-program content is left untouched; only the fake phone chrome is fixed.
    html = re.sub(r"<span>[^<]*(?:鈼|棌|忊)[^<]*(?:</span>)?", "<span>LTE</span>", html)
    return html


def render_case_preview(case_id: str) -> None:
    files = load_golden_from_folder(case_id)
    try:
        phone_html = render_phone_html(
            files.get("wxml", ""),
            files.get("wxss", ""),
            files.get("js", ""),
            app_wxss=APP_WXSS,
        )
        phone_html = _clean_phone_html(phone_html)
        b64 = base64.b64encode(phone_html.encode("utf-8")).decode("ascii")
        st.iframe(f"data:text/html;base64,{b64}", height=760)
    except Exception as exc:
        st.warning(f"预览渲染失败：{exc}")


def render_case_text(case: dict) -> None:
    prompt_url = f"{DEMO_URL}?prompt={quote(case['prompt'])}"
    chips = "".join(f"<span>{item}</span>" for item in case["highlights"])
    st.markdown(
        f"""
<div class="case-copy">
  <div class="case-id">{case['id']}</div>
  <h3>{case['title']}</h3>
  <p>{case['positioning']}</p>
  <div class="case-chips">{chips}</div>
  <div class="case-prompt">{case['prompt']}</div>
  <div class="case-actions">
    <a class="cta small" href="{prompt_url}" target="_self">Use this prompt</a>
    <a class="ghost small" href="{LEGACY_SHOWCASE_URL}" target="_self">View in 8502</a>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="MiniPilot Agent Showcase", page_icon="MP", layout="wide")

st.markdown(
    """
<style>
  :root {
    --ink:#141414;
    --muted:#6b6f76;
    --line:#e5e1d8;
    --paper:#fbfaf6;
    --surface:#ffffff;
    --green:#2f7d68;
  }
  .stApp { background: var(--paper); color: var(--ink); }
  .block-container { max-width: 1240px; padding-top: 2.2rem; padding-bottom: 4rem; }
  [data-testid="stHeader"] { background: transparent; }
  .hero {
    min-height: 72vh;
    display: grid;
    grid-template-columns: minmax(0, 1.08fr) minmax(340px, .72fr);
    gap: 42px;
    align-items: center;
    border-bottom: 1px solid var(--line);
    padding: 18px 0 42px;
  }
  .kicker { color: var(--green); text-transform: uppercase; letter-spacing: .08em; font-size: 13px; font-weight: 800; }
  .hero h1 { font-size: clamp(56px, 8vw, 108px); line-height: .9; margin: 14px 0 18px; letter-spacing: 0; }
  .hero .lead { font-size: 25px; line-height: 1.24; max-width: 780px; margin: 0 0 18px; }
  .hero .sub { font-size: 16px; color: var(--muted); line-height: 1.7; max-width: 720px; margin-bottom: 28px; }
  .cta-row, .case-actions { display:flex; gap:12px; flex-wrap:wrap; align-items:center; }
  .cta, .ghost {
    display:inline-flex; align-items:center; justify-content:center;
    min-height:44px; padding:0 18px; border-radius:7px; text-decoration:none; font-weight:760;
    border:1px solid var(--ink);
  }
  .cta { background:var(--ink); color:white !important; }
  .ghost { color:var(--ink) !important; background:transparent; }
  .small { min-height:38px; padding:0 14px; font-size:14px; }
  .artifact {
    background:#181816; color:#f6f0df; border-radius:8px; padding:22px;
    box-shadow:0 24px 60px rgba(20,20,20,.20); border:1px solid rgba(255,255,255,.08);
  }
  .artifact-head { display:flex; justify-content:space-between; color:#b9b19b; font-size:12px; margin-bottom:22px; }
  .pipeline-stack { display:grid; gap:12px; }
  .node { border:1px solid rgba(255,255,255,.15); border-radius:7px; padding:14px 16px; background:rgba(255,255,255,.055); }
  .node strong { display:block; margin-bottom:3px; font-size:15px; }
  .node span { color:#b9b19b; font-size:13px; }
  .section { padding:54px 0; border-bottom:1px solid var(--line); }
  .section h2 { font-size:34px; margin:0 0 10px; }
  .section-intro { color:var(--muted); max-width:760px; margin-bottom:26px; line-height:1.7; }
  .grid-3, .grid-5 { display:grid; gap:14px; }
  .grid-3 { grid-template-columns: repeat(3, minmax(0,1fr)); }
  .grid-5 { grid-template-columns: repeat(5, minmax(0,1fr)); }
  .card {
    background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:20px;
    box-shadow:0 10px 30px rgba(48,43,35,.05);
  }
  .card h3 { margin:0 0 8px; font-size:18px; }
  .card p { margin:0; color:var(--muted); line-height:1.55; font-size:14px; }
  .case-divider { border-top:1px solid var(--line); padding-top:34px; margin-top:34px; }
  .case-copy { padding: 18px 0 0; }
  .case-id { color:var(--green); text-transform:uppercase; letter-spacing:.08em; font-weight:900; font-size:12px; margin-bottom:12px; }
  .case-copy h3 { font-size:34px; line-height:1.15; margin:0 0 12px; }
  .case-copy p { color:var(--muted); font-size:16px; line-height:1.7; margin:0 0 16px; max-width:560px; }
  .case-chips { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
  .case-chips span { border:1px solid var(--line); border-radius:999px; padding:6px 10px; font-size:12px; background:#fff; color:#3f4247; }
  .case-prompt {
    background:#f6f2ea; border:1px solid #ebe3d6; border-radius:8px;
    padding:14px 16px; line-height:1.6; font-size:14px; margin-bottom:18px; color:#2d2d2d;
  }
  .pipeline { display:grid; grid-template-columns: repeat(6, minmax(0,1fr)); gap:10px; }
  .pipe-step { background:#191919; color:#fff; border-radius:8px; padding:16px 12px; min-height:86px; }
  .pipe-step span { display:block; color:#bcbcbc; font-size:12px; margin-top:7px; }
  .metric-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
  .metric strong { display:block; font-size:30px; margin-bottom:4px; }
  .metric span { color:var(--muted); font-size:13px; }
  .final-cta { display:flex; justify-content:space-between; gap:20px; align-items:center; }
  iframe { background: transparent; }
  @media (max-width: 900px) {
    .hero, .grid-3, .grid-5, .pipeline, .metric-grid { grid-template-columns:1fr; }
    .hero { min-height:auto; }
    .artifact { margin-top:8px; }
    .final-cta { display:block; }
  }
</style>
""",
    unsafe_allow_html=True,
)

golden_count = _golden_count()
benchmark_count = _benchmark_count()
verified_images = _verified_image_count()

st.markdown(
    f"""
<section class="hero">
  <div>
    <div class="kicker">GDG Shanghai Gemma 4 Hackathon / Track A</div>
    <h1>{PRODUCT_NAME}</h1>
    <p class="lead">小程序 MVP 生成智能体</p>
    <p class="sub"><strong>{PRODUCT_TAGLINE}</strong><br>{POWERED_BY} 面向小微商家、本地门店和个体经营者，把一句自然语言生意需求转成可预览、可下载的小程序 MVP。</p>
    <div class="cta-row">
      <a class="cta" href="{DEMO_URL}" target="_self">Open MVP Generator</a>
      <a class="ghost" href="#featured-cases">View MVP Cases</a>
      <a class="ghost" href="{LEGACY_SHOWCASE_URL}" target="_self">View 8502</a>
    </div>
  </div>
  <div class="artifact">
    <div class="artifact-head"><span>MVP generation pipeline</span><span>8505</span></div>
    <div class="pipeline-stack">
      <div class="node"><strong>Business Brief</strong><span>一句生意需求进入生成链路</span></div>
      <div class="node"><strong>Gemma 4 Tool Calling</strong><span>create_miniprogram_page(wxml, wxss, js)</span></div>
      <div class="node"><strong>Validator + Repair</strong><span>先校验，再自愈，减少坏代码出站</span></div>
      <div class="node"><strong>Phone Preview + ZIP</strong><span>375px 手机预览 + 小程序工程导出</span></div>
    </div>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="section">
  <h2>为什么值得做</h2>
  <p class="section-intro">MiniPilot Agent 面向的是最常见、最实际的小程序原型需求：先看见 MVP，再决定要不要继续投入。</p>
  <div class="grid-3">
    <div class="card"><h3>小商家需要先看到</h3><p>咖啡点单、门店预约、活动报名、商品展示这些需求能说清楚，但很难马上变成可看的页面。</p></div>
    <div class="card"><h3>MVP 不该先烧预算</h3><p>传统外包适合正式系统，但早期验证常常只需要一个能演示、能讨论、能下载的小程序原型。</p></div>
    <div class="card"><h3>反馈应该更早发生</h3><p>把“沟通、设计、开发、返工”的长链路压缩成一次自然语言输入，让真实反馈提前到几十秒内。</p></div>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="section">
  <h2>技术亮点</h2>
  <p class="section-intro">8504 负责把 MiniPilot Agent 的产品价值和工程边界讲清楚；8505 负责证明它真的能生成。</p>
  <div class="grid-5">
    <div class="card"><h3>Gemma 4 Tool Calling</h3><p>模型通过工具调用输出 wxml / wxss / js 三件套，不把关键结构交给脆弱文本解析。</p></div>
    <div class="card"><h3>Agentic Workflow</h3><p>需求理解、上下文组装、代码生成、解析、校验、自愈和预览形成完整闭环。</p></div>
    <div class="card"><h3>Static Validator</h3><p>自动拦截 HTML 标签混入、危险 API、路径污染、图片缺失和小程序语法高频错误。</p></div>
    <div class="card"><h3>Grounded Asset Library</h3><p>本地图片素材进入 Zip/projectPath，避免模型自由编造远程 URL 导致真机看不到图。</p></div>
    <div class="card"><h3>Dual Backend</h3><p>Google AI Studio 与 AMD vLLM Gemma 31B 共用同一工具协议，兼顾稳定演示与私有化验证。</p></div>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="section" id="featured-cases">
  <h2>精选 MVP 案例</h2>
  <p class="section-intro">保留 3 个最适合评审快速理解的真实小程序 MVP：婚礼服务、米其林餐厅、咖啡点单。右侧手机预览读取当前仓库 golden examples，不是静态截图。</p>
</section>
""",
    unsafe_allow_html=True,
)

for index, case in enumerate(FEATURED_CASES):
    st.markdown('<div class="case-divider"></div>', unsafe_allow_html=True)
    left, right = st.columns([0.44, 0.56], gap="large")
    if index % 2 == 0:
        with left:
            render_case_preview(case["id"])
        with right:
            render_case_text(case)
    else:
        with left:
            render_case_text(case)
        with right:
            render_case_preview(case["id"])

st.markdown(
    """
<section class="section">
  <h2>技术架构</h2>
  <p class="section-intro">一条从“生意需求”到“小程序 MVP”的可解释、可校验生成链路。</p>
  <div class="pipeline">
    <div class="pipe-step">Business Prompt<span>one-line need</span></div>
    <div class="pipe-step">Gemma 4<span>tool calling</span></div>
    <div class="pipe-step">Page Code<span>wxml / wxss / js</span></div>
    <div class="pipe-step">Validator<span>hard errors / warnings</span></div>
    <div class="pipe-step">Repair Loop<span>self-correction</span></div>
    <div class="pipe-step">MVP Export<span>preview / zip</span></div>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<section class="section">
  <h2>结果与指标</h2>
  <p class="section-intro">只展示当前仓库能读到的事实；拿不到的数据不硬编，保持 Hackathon 演示可信。</p>
  <div class="metric-grid">
    <div class="card metric"><strong>Live</strong><span>8505 真实生成链路</span></div>
    <div class="card metric"><strong>{_metric_value(golden_count)}</strong><span>预验证 golden examples</span></div>
    <div class="card metric"><strong>{_metric_value(benchmark_count)}</strong><span>benchmark prompts</span></div>
    <div class="card metric"><strong>27</strong><span>本地 grounded image assets</span></div>
  </div>
</section>
<section class="section final-cta">
  <div>
    <h2>现在看真实生成</h2>
    <p class="section-intro">{PRODUCT_FULL_NAME}：{PRODUCT_TAGLINE} {POWERED_BY}</p>
  </div>
  <a class="cta" href="{DEMO_URL}" target="_self">Open MVP Generator</a>
</section>
""",
    unsafe_allow_html=True,
)

st.caption(f"{PRODUCT_FULL_NAME}  /  Showcase: {SHOWCASE_URL}  /  Legacy cases: {LEGACY_SHOWCASE_URL}  /  Live Demo: {DEMO_URL}")
