from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from render_wxml import render_phone_html
from scaffold import APP_WXSS

OUT = ROOT / "vercel_minipilot"
GOLDEN_DIR = ROOT / "gemma_core" / "golden_examples"

PRODUCT_NAME = "MiniPilot Agent"
TAGLINE = "一句生意需求，生成小程序 MVP。"
POWERED = "Powered by Gemma 4."

CASES = [
    {
        "id": "ai_wedding_studio",
        "title": "AI 婚礼美学工作室",
        "type": "高端服务预约",
        "positioning": "一句高端婚礼影像需求，快速生成作品集、AI 服务与套餐预约的小程序 MVP。",
        "prompt": "生成一个 AI 婚礼美学工作室小程序页面，包含作品集、AI 服务、套餐预约、底部导航和高级黑金视觉风格。",
    },
    {
        "id": "michelin_restaurant",
        "title": "米其林餐厅",
        "type": "餐饮预订",
        "positioning": "一句高客单价餐饮需求，生成餐厅调性、招牌菜单和预约入口的小程序 MVP。",
        "prompt": "生成一个米其林餐厅小程序页面，包含餐厅封面、主厨推荐、招牌菜展示、营业信息和底部预约按钮。",
    },
    {
        "id": "coffee_shop",
        "title": "咖啡点单",
        "type": "门店交易",
        "positioning": "一句门店点单需求，生成分类、商品、购物车和结算栏都能看见的小程序 MVP。",
        "prompt": "生成一个咖啡店点单小程序页面，包含门店封面、分类 Tab、商品列表、购物车和底部结算栏。",
    },
    {
        "id": "product_detail",
        "title": "商品详情页",
        "type": "电商转化",
        "positioning": "一句商品销售需求，生成主图、价格、规格、优惠信息和底部购买入口。",
        "prompt": "生成一个电商商品详情页，包含商品主图、价格、规格选择、优惠信息和底部购买按钮。",
    },
]


def read_case(case_id: str) -> dict[str, str]:
    folder = GOLDEN_DIR / case_id
    return {
        ext: (folder / f"index.{ext}").read_text(encoding="utf-8", errors="replace")
        for ext in ("wxml", "wxss", "js")
    }


def build_case_payload() -> list[dict]:
    payload = []
    for case in CASES:
        files = read_case(case["id"])
        phone = render_phone_html(files["wxml"], files["wxss"], files["js"], app_wxss=APP_WXSS)
        payload.append({**case, "phoneHtml": phone, "files": files})
    return payload


def json_script(data: object) -> str:
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def shell(title: str, body: str, script: str = "") -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>{CSS}</style>
</head>
<body>
{body}
{script}
</body>
</html>
"""


CSS = """
:root{--ink:#141414;--muted:#626873;--line:#e5e1d8;--paper:#fbfaf6;--surface:#fff;--green:#2f7d68;--blue:#244b72;--purple:#6f5c8f;--accent:#b96b36;--soft:#f4f0e8;--shadow:0 18px 50px rgba(42,36,25,.09)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"PingFang SC","Microsoft YaHei",sans-serif}button,input,textarea{font:inherit}a{color:inherit}.wrap{max-width:1320px;margin:0 auto;padding:44px 28px 84px}.topbar{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:34px}.brand{font-size:13px;font-weight:900;letter-spacing:.18em;text-transform:uppercase;color:#454b55}.nav{display:flex;gap:10px;flex-wrap:wrap}.btn{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:0 16px;border-radius:7px;border:1px solid var(--ink);background:#fff;color:var(--ink);font-weight:850;text-decoration:none;cursor:pointer}.btn.primary{background:var(--ink);color:#fff}.btn.ghost{border-color:var(--line);background:#fff}.btn.small{min-height:34px;padding:0 12px;font-size:13px}.hero{min-height:72vh;display:grid;grid-template-columns:minmax(0,.9fr) minmax(420px,1fr);gap:48px;align-items:center;border-bottom:1px solid var(--line);padding-bottom:46px}.kicker{color:var(--green);text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:900}.hero h1{font-size:clamp(58px,7.5vw,112px);line-height:.9;margin:18px 0 24px}.lead{font-size:24px;line-height:1.35;margin:0 0 16px}.sub{font-size:17px;color:var(--muted);line-height:1.72;max-width:720px}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}.hero-stage{display:grid;grid-template-columns:220px minmax(0,1fr);gap:18px;align-items:stretch}.case-rail{display:grid;gap:10px;align-content:start}.case-pill{width:100%;text-align:left;border:1px solid var(--line);border-radius:8px;background:#fff;padding:14px 13px;cursor:pointer;box-shadow:0 8px 20px rgba(45,39,30,.035)}.case-pill strong{display:block;font-size:15px}.case-pill span{display:block;margin-top:4px;color:var(--muted);font-size:12px}.case-pill.active{border-color:var(--green);box-shadow:0 0 0 3px rgba(47,125,104,.12);background:#f8fffc}.phone-panel{background:#eef1f5;border:1px solid #e4e8ef;border-radius:8px;padding:18px;box-shadow:var(--shadow);min-height:640px}.phone-frame{width:100%;height:700px;border:0;background:transparent;display:block}.section{padding:58px 0;border-bottom:1px solid var(--line)}.section h2{font-size:36px;margin:0 0 12px}.section-intro{color:var(--muted);line-height:1.7;max-width:820px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:28px}.grid.five{grid-template-columns:repeat(5,minmax(0,1fr))}.card{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:20px;box-shadow:0 10px 30px rgba(48,43,35,.05)}.card h3{margin:0 0 8px;font-size:18px}.card p{margin:0;color:var(--muted);line-height:1.6;font-size:14px}.case-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:26px}.case-card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:18px;cursor:pointer;box-shadow:0 10px 30px rgba(48,43,35,.05);transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}.case-card:hover,.case-card.active{transform:translateY(-2px);border-color:var(--green);box-shadow:0 16px 40px rgba(47,125,104,.12)}.case-card .type{font-size:12px;color:var(--green);font-weight:900;letter-spacing:.08em;text-transform:uppercase}.case-card h3{font-size:22px;margin:10px 0}.case-card p{color:var(--muted);line-height:1.55;font-size:14px}.prompt{background:#f6f2ea;border:1px solid #ebe3d6;border-radius:8px;padding:13px 14px;line-height:1.65;color:#2d2d2d;font-size:14px}.case-detail{display:grid;grid-template-columns:minmax(0,.58fr) minmax(400px,.42fr);gap:24px;margin-top:28px;align-items:start}.detail-copy{background:#fff;border:1px solid var(--line);border-radius:8px;padding:24px}.detail-copy h3{font-size:34px;margin:10px 0}.chips{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.chips span{background:#fff;border:1px solid var(--line);border-radius:999px;padding:6px 10px;font-size:12px}.source-modal{position:fixed;inset:0;background:rgba(16,16,16,.55);display:none;align-items:center;justify-content:center;padding:28px;z-index:20}.source-modal.open{display:flex}.modal-card{width:min(980px,100%);max-height:86vh;overflow:hidden;background:#fff;border-radius:8px;box-shadow:0 28px 90px rgba(0,0,0,.25);display:grid;grid-template-rows:auto auto minmax(0,1fr)}.modal-head{display:flex;justify-content:space-between;align-items:center;padding:16px 18px;border-bottom:1px solid var(--line)}.tabs{display:flex;gap:8px;padding:12px 18px;border-bottom:1px solid var(--line)}.tab{border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 12px;cursor:pointer}.tab.active{background:#141414;color:#fff;border-color:#141414}.code{margin:0;padding:18px;overflow:auto;background:#111;color:#f4f4f4;font:12px/1.55 Consolas,Monaco,monospace;white-space:pre-wrap}.pipe{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}.pipe div{background:#191919;color:#fff;border-radius:8px;padding:16px 12px;min-height:86px}.pipe span{display:block;color:#bcbcbc;font-size:12px;margin-top:7px}.demo-shell{display:grid;grid-template-columns:310px minmax(380px,1fr) minmax(360px,.85fr);gap:22px;align-items:start}.panel{background:#fff;border:1px solid var(--line);border-radius:8px;padding:20px;box-shadow:0 10px 30px rgba(48,43,35,.05)}.panel-title{font-size:26px;margin:0 0 18px}.panel-title.brief{color:#141414}.panel-title.trace{color:var(--blue)}.panel-title.preview{color:var(--purple)}.textarea{width:100%;min-height:176px;border:1px solid #d9d4c8;border-radius:8px;padding:14px;font-size:15px;line-height:1.6;resize:vertical}.sample-buttons{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:16px 0}.mode{display:grid;gap:10px;margin:20px 0}.radio-line{display:flex;gap:8px;align-items:flex-start;color:#333;font-size:14px}.trace-list{display:grid;gap:12px}.trace-card{border:1px solid var(--line);border-radius:8px;padding:16px;background:#fff;display:grid;grid-template-columns:56px 1fr;gap:14px;align-items:start}.badge{display:inline-flex;align-items:center;justify-content:center;min-height:34px;border-radius:8px;background:#2f7d68;color:#fff;font-size:12px;font-weight:900}.badge.pending{background:#d7d1c5;color:#594e42}.trace-card h4{margin:0 0 8px}.trace-card p{margin:0;color:var(--muted);line-height:1.55}.metrics{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.metric{border:1px solid var(--line);border-radius:999px;padding:5px 9px;font-size:12px;background:#fbfaf6}.preview-stage{background:linear-gradient(165deg,#efecf4 0%,#fff 55%);border:1px solid #efecf4;border-radius:8px;padding:22px 18px}.source-box{margin-top:18px}.source-actions{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}.live-code{height:240px;border-radius:8px;overflow:auto}.notice{margin-top:14px;color:var(--muted);font-size:13px;line-height:1.6}.toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#141414;color:#fff;padding:10px 14px;border-radius:999px;display:none;z-index:30}.toast.show{display:block}.link-note{font-size:13px;color:var(--muted);margin-top:10px;line-height:1.55}
@media(max-width:1100px){.hero,.hero-stage,.case-detail,.demo-shell{grid-template-columns:1fr}.case-grid,.grid.five{grid-template-columns:repeat(2,minmax(0,1fr))}.phone-panel{min-height:0}.phone-frame{height:680px}}
@media(max-width:720px){.wrap{padding:28px 18px 64px}.topbar{align-items:flex-start}.hero h1{font-size:56px}.grid,.case-grid,.pipe{grid-template-columns:1fr}.sample-buttons{grid-template-columns:1fr}.phone-frame{height:620px}.modal-card{max-height:92vh}}
"""


def shared_script(page: str) -> str:
    data = json_script(build_case_payload())
    return f"""<script id="case-data" type="application/json">{data}</script>
<script>
const CASES = JSON.parse(document.getElementById('case-data').textContent);
let selected = CASES[0];
let activeSource = 'wxml';
const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => Array.from(root.querySelectorAll(s));

function byId(id) {{ return CASES.find(c => c.id === id) || CASES[0]; }}
function setPhone(frame, item) {{ if (frame) frame.srcdoc = item.phoneHtml; }}
function toast(text) {{
  let el = $('.toast');
  if (!el) {{ el = document.createElement('div'); el.className = 'toast'; document.body.appendChild(el); }}
  el.textContent = text; el.classList.add('show'); setTimeout(() => el.classList.remove('show'), 1800);
}}
function codeOf(item, tab) {{ return item.files?.[tab] || ''; }}
function openSource(item=selected, tab='wxml') {{
  selected = item; activeSource = tab;
  const modal = $('#sourceModal'); if (!modal) return;
  $('#modalTitle').textContent = item.title + ' · Source';
  $$('.tab', modal).forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  $('#modalCode').textContent = codeOf(item, tab);
  modal.classList.add('open');
}}
function closeSource() {{ const modal = $('#sourceModal'); if (modal) modal.classList.remove('open'); }}
function usePrompt(item) {{ location.href = '/live?case=' + encodeURIComponent(item.id); }}

function initShowcase() {{
  const heroFrame = $('#heroPhone');
  const detailFrame = $('#detailPhone');
  const rail = $('#caseRail');
  const caseGrid = $('#caseGrid');
  function render(item) {{
    selected = item;
    setPhone(heroFrame, item); setPhone(detailFrame, item);
    $('#detailType').textContent = item.type;
    $('#detailTitle').textContent = item.title;
    $('#detailText').textContent = item.positioning;
    $('#detailPrompt').textContent = item.prompt;
    $$('.case-pill,[data-case-card]').forEach(el => el.classList.toggle('active', el.dataset.case === item.id));
  }}
  if (rail) rail.innerHTML = CASES.map(c => `<button class="case-pill" data-case="${{c.id}}"><strong>${{c.title}}</strong><span>${{c.type}}</span></button>`).join('');
  if (caseGrid) caseGrid.innerHTML = CASES.map(c => `<article class="case-card" data-case-card data-case="${{c.id}}"><div class="type">${{c.type}}</div><h3>${{c.title}}</h3><p>${{c.positioning}}</p></article>`).join('');
  document.addEventListener('click', e => {{
    const btn = e.target.closest('[data-case]');
    if (btn && (btn.classList.contains('case-pill') || btn.hasAttribute('data-case-card'))) {{
      render(byId(btn.dataset.case));
      $('#cases')?.scrollIntoView({{behavior:'smooth', block:'start'}});
    }}
    if (e.target.closest('[data-open-source]')) openSource(selected);
    if (e.target.closest('[data-use-prompt]')) usePrompt(selected);
    if (e.target.closest('[data-copy-prompt]')) navigator.clipboard?.writeText(selected.prompt).then(() => toast('Prompt copied'));
    if (e.target.closest('[data-close-source]')) closeSource();
    const tab = e.target.closest('.tab');
    if (tab) openSource(selected, tab.dataset.tab);
  }});
  render(new URLSearchParams(location.search).get('case') ? byId(new URLSearchParams(location.search).get('case')) : CASES[0]);
}}

function initLive() {{
  const params = new URLSearchParams(location.search);
  const initial = params.get('case') ? byId(params.get('case')) : CASES[2];
  const prompt = $('#promptInput');
  const phone = $('#livePhone');
  const code = $('#liveCode');
  const sourceTabs = $$('.source-actions .tab');
  let item = initial, tab = 'wxml';
  function select(next) {{
    item = next; prompt.value = next.prompt; setPhone(phone, next);
    updateTrace('ready'); renderCode();
  }}
  function renderCode() {{
    sourceTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
    code.textContent = codeOf(item, tab);
  }}
  function updateTrace(state) {{
    const chars = prompt.value.trim().length;
    const lines = Object.values(item.files || {{}}).join('\\n').split('\\n').length;
    $('#metricPrompt').textContent = `prompt chars ${{chars}}`;
    $('#metricTokens').textContent = `prompt tokens ~${{Math.max(800, chars * 38)}}`;
    $('#metricLines').textContent = `source lines ${{lines}}`;
    $$('.trace-card .badge').forEach((b, i) => {{
      b.classList.toggle('pending', state === 'running' && i > 1);
      b.textContent = state === 'running' && i > 1 ? '...' : 'OK';
    }});
  }}
  function inferCase() {{
    const text = prompt.value;
    if (/婚|摄影|影像|wedding/i.test(text)) return byId('ai_wedding_studio');
    if (/米其林|餐厅|菜单|菜|restaurant|menu/i.test(text)) return byId('michelin_restaurant');
    if (/商品|电商|详情|购买|product/i.test(text)) return byId('product_detail');
    if (/咖啡|点单|购物车|coffee/i.test(text)) return byId('coffee_shop');
    return item;
  }}
  document.addEventListener('click', e => {{
    const sample = e.target.closest('[data-sample]');
    if (sample) select(byId(sample.dataset.sample));
    if (e.target.closest('[data-generate]')) {{
      updateTrace('running');
      setTimeout(() => {{ select(inferCase()); toast('Vercel demo rendered a verified local sample'); }}, 420);
    }}
    if (e.target.closest('[data-live-source]')) openSource(item, tab);
    if (e.target.closest('[data-live-copy]')) navigator.clipboard?.writeText(prompt.value).then(() => toast('Prompt copied'));
    if (e.target.closest('[data-live-zip]')) toast('线上展示版不生成真实 Zip；本地 8505 可下载完整工程');
    if (e.target.closest('[data-live-deploy]')) toast('微信预览需要本地 8505 的 AppID/private key');
    const t = e.target.closest('.source-actions .tab');
    if (t) {{ tab = t.dataset.tab; renderCode(); }}
    if (e.target.closest('[data-close-source]')) closeSource();
    const modalTab = e.target.closest('#sourceModal .tab');
    if (modalTab) openSource(selected, modalTab.dataset.tab);
  }});
  select(initial);
}}

if ('{page}' === 'showcase') initShowcase();
if ('{page}' === 'live') initLive();
</script>"""


def source_modal() -> str:
    return """<div class="source-modal" id="sourceModal" role="dialog" aria-modal="true">
  <div class="modal-card">
    <div class="modal-head"><strong id="modalTitle">Source</strong><button class="btn small" data-close-source>Close</button></div>
    <div class="tabs"><button class="tab active" data-tab="wxml">WXML</button><button class="tab" data-tab="wxss">WXSS</button><button class="tab" data-tab="js">JS</button></div>
    <pre class="code" id="modalCode"></pre>
  </div>
</div>"""


def build_index() -> str:
    body = f"""<main class="wrap">
  <header class="topbar">
    <div class="brand">MiniPilot Agent · 小程序 MVP 生成智能体</div>
    <nav class="nav"><a class="btn ghost small" href="/live">Open Generator</a><a class="btn ghost small" href="#cases">Cases</a></nav>
  </header>
  <section class="hero">
    <div>
      <div class="kicker">GDG Shanghai Gemma 4 Hackathon / Track A</div>
      <h1>{PRODUCT_NAME}</h1>
      <p class="lead">小程序 MVP 生成智能体</p>
      <p class="sub"><strong>{TAGLINE}</strong><br>{POWERED} 面向小微商家、本地门店和个体经营者，把一句自然语言生意需求转成可预览、可下载的小程序 MVP。</p>
      <div class="actions"><a class="btn primary" href="/live">Open MVP Generator</a><a class="btn" href="#cases">View MVP Cases</a></div>
      <p class="link-note">Vercel /live 已接入 Google AI Studio 服务端生成；本地 8505 仍保留完整 Streamlit、微信预览和下载链路。</p>
    </div>
    <div class="hero-stage">
      <div class="case-rail" id="caseRail"></div>
      <div class="phone-panel"><iframe id="heroPhone" class="phone-frame" title="Selected mini program preview"></iframe></div>
    </div>
  </section>
  <section class="section">
    <h2>为什么值得做</h2>
    <p class="section-intro">MiniPilot Agent 面向的是最常见、最实际的小程序原型需求：先看见 MVP，再决定要不要继续投入。</p>
    <div class="grid">
      <div class="card"><h3>小商家需要先看到</h3><p>咖啡点单、门店预约、活动报名、商品展示都能快速变成可讨论的页面。</p></div>
      <div class="card"><h3>MVP 不该先烧预算</h3><p>早期验证只需要一个能演示、能下载、能导入的原型，而不是完整外包链路。</p></div>
      <div class="card"><h3>反馈应该更早发生</h3><p>把沟通、设计、开发、返工压缩成一次自然语言输入和一组可视化结果。</p></div>
    </div>
  </section>
  <section class="section">
    <h2>技术亮点</h2>
    <div class="grid five">
      <div class="card"><h3>Gemma 4 Tool Calling</h3><p>模型通过工具调用输出 wxml / wxss / js 三件套。</p></div>
      <div class="card"><h3>Agentic Workflow</h3><p>需求理解、上下文组装、代码生成、解析、校验、自愈和预览形成闭环。</p></div>
      <div class="card"><h3>Static Validator</h3><p>拦截 HTML 混入、危险 API、路径污染和小程序语法高频错误。</p></div>
      <div class="card"><h3>Grounded Assets</h3><p>图片进入真实项目路径，避免扫码预览看不到图。</p></div>
      <div class="card"><h3>Dual Backend</h3><p>Google AI Studio 与 AMD vLLM Gemma 31B 共用同一工具协议。</p></div>
    </div>
  </section>
  <section class="section" id="cases">
    <h2>精选 MVP 案例</h2>
    <p class="section-intro">点击卡片会切换手机预览；也可以查看生成源码，或把对应 prompt 带到 8505 风格的生成器页面。</p>
    <div class="case-grid" id="caseGrid"></div>
    <div class="case-detail">
      <div class="detail-copy">
        <div class="kicker" id="detailType"></div>
        <h3 id="detailTitle"></h3>
        <p class="section-intro" id="detailText"></p>
        <div class="chips"><span>小程序 MVP</span><span>手机预览</span><span>可查看源码</span></div>
        <div class="prompt" id="detailPrompt"></div>
        <div class="actions"><button class="btn primary" data-use-prompt>Use this prompt</button><button class="btn" data-open-source>View source</button><button class="btn ghost" data-copy-prompt>Copy prompt</button></div>
      </div>
      <div class="phone-panel"><iframe id="detailPhone" class="phone-frame" title="Case preview"></iframe></div>
    </div>
  </section>
  <section class="section">
    <h2>技术架构</h2>
    <div class="pipe"><div>Business Prompt<span>one-line need</span></div><div>Gemma 4<span>tool calling</span></div><div>Page Code<span>wxml / wxss / js</span></div><div>Validator<span>hard errors / warnings</span></div><div>Repair Loop<span>self-correction</span></div><div>MVP Export<span>preview / zip</span></div></div>
  </section>
</main>{source_modal()}"""
    return shell(f"{PRODUCT_NAME} Showcase", body, shared_script("showcase"))


def build_live() -> str:
    body = f"""<main class="wrap">
  <header class="topbar">
    <div class="brand">MiniPilot Agent · Live MVP Generator</div>
    <nav class="nav"><a class="btn ghost small" href="/">Back to Showcase</a></nav>
  </header>
  <section class="section" style="padding-top:10px">
    <div class="kicker">MiniPilot Agent · Live MVP Generator</div>
    <h1 style="font-size:clamp(48px,6vw,86px);line-height:.95;margin:16px 0 18px">从一句生意需求到小程序 MVP</h1>
    <p class="sub"><strong>{TAGLINE}</strong> {POWERED}<br>这页复刻 8505 的交互结构：Brief、Gemma Agent Trace、Phone Preview、Source 与部署状态。线上版使用已验证样例渲染，不在浏览器暴露模型 API Key。</p>
  </section>
  <section class="demo-shell">
    <aside class="panel">
      <h2 class="panel-title brief">BRIEF</h2>
      <label>自然语言需求</label>
      <textarea class="textarea" id="promptInput"></textarea>
      <h3 style="margin:18px 0 10px;color:#8a8f99">没有思路？试试这些</h3>
      <div class="sample-buttons">
        <button class="btn ghost small" data-sample="coffee_shop">咖啡店点单</button>
        <button class="btn ghost small" data-sample="michelin_restaurant">餐厅菜单页</button>
        <button class="btn ghost small" data-sample="product_detail">商品详情页</button>
        <button class="btn ghost small" data-sample="ai_wedding_studio">AI 婚礼页</button>
      </div>
      <div class="mode">
        <label class="radio-line"><input type="radio" checked> 快速 Agent 模式（Google AI Studio 主链路）</label>
        <label class="radio-line"><input type="radio"> 深度生成模式（AMD vLLM Gemma 31B 自托管·长上下文）</label>
      </div>
      <button class="btn primary" style="width:100%" data-generate>Generate MVP Preview</button>
      <p class="notice">线上演示会根据 prompt 选择最接近的已验证样例；本地 8505 才会调用真实 Gemma 生成、下载 Zip 和微信预览。</p>
    </aside>
    <section class="panel">
      <h2 class="panel-title trace">GEMMA AGENT TRACE</h2>
      <div class="trace-list">
        <div class="trace-card"><span class="badge">OK</span><div><h4>STEP 01 Requirement Understanding</h4><p>识别行业、页面目标、交易/预约路径。</p><div class="metrics"><span class="metric" id="metricPrompt"></span></div></div></div>
        <div class="trace-card"><span class="badge">OK</span><div><h4>STEP 02 Context Assembly</h4><p>组合 prompt builder、golden examples 与本地 asset_list。</p><div class="metrics"><span class="metric" id="metricTokens"></span><span class="metric">examples 23</span><span class="metric">grounded assets</span></div></div></div>
        <div class="trace-card"><span class="badge">OK</span><div><h4>STEP 03 Function Calling</h4><p>create_miniprogram_page(wxml, wxss, js)</p><div class="metrics"><span class="metric">provider demo sample</span></div></div></div>
        <div class="trace-card"><span class="badge">OK</span><div><h4>STEP 04 Code Parsing</h4><p>WXML / WXSS / JS extracted.</p><div class="metrics"><span class="metric" id="metricLines"></span></div></div></div>
        <div class="trace-card"><span class="badge">OK</span><div><h4>STEP 05 Static Validator</h4><p>检查图片路径、事件绑定、危险 API 与小程序语法。</p><div class="metrics"><span class="metric">0 hard errors</span></div></div></div>
      </div>
      <div class="source-box">
        <div class="source-actions"><button class="tab active" data-tab="wxml">WXML</button><button class="tab" data-tab="wxss">WXSS</button><button class="tab" data-tab="js">JS</button><button class="btn small" data-live-source>Open source</button></div>
        <pre class="code live-code" id="liveCode"></pre>
      </div>
    </section>
    <aside class="panel">
      <h2 class="panel-title preview">PHONE PREVIEW</h2>
      <div class="preview-stage"><iframe id="livePhone" class="phone-frame" title="Live preview"></iframe></div>
      <div class="actions"><button class="btn primary" data-live-zip>Download ZIP</button><button class="btn" data-live-deploy>WeChat Preview</button><button class="btn ghost" data-live-copy>Copy Prompt</button></div>
    </aside>
  </section>
</main>{source_modal()}"""
    return shell(f"{PRODUCT_NAME} Live Demo", body, shared_script("live"))


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / "index.html").write_text(build_index(), encoding="utf-8")
    (OUT / "live.html").write_text(build_live(), encoding="utf-8")
    (OUT / "package.json").write_text(
        json.dumps(
            {
                "name": "minipilot-agent",
                "version": "1.0.0",
                "private": True,
                "scripts": {"build": "echo static"},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (OUT / "vercel.json").write_text(
        json.dumps(
            {
                "version": 2,
                "rewrites": [
                    {"source": "/live", "destination": "/live.html"},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(OUT)


if __name__ == "__main__":
    main()
