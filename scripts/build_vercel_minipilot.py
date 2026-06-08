from __future__ import annotations

import base64
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
PRODUCT_FULL_NAME = "MiniPilot Agent｜小程序 MVP 生成智能体"
TAGLINE = "一句生意需求，生成小程序 MVP。"
POWERED = "Powered by Gemma 4."

CASES = [
    (
        "ai_wedding_studio",
        "AI 婚礼美学工作室",
        "一句高端婚礼影像需求，快速生成作品集、AI 服务与套餐预约的小程序 MVP。",
        "生成一个 AI 婚礼美学工作室小程序页面，包含作品集、AI 服务、套餐预约、底部导航和高级黑金视觉风格。",
    ),
    (
        "michelin_restaurant",
        "米其林餐厅",
        "一句高客单价餐饮需求，生成餐厅调性、招牌菜单和预约入口的小程序 MVP。",
        "生成一个米其林餐厅小程序页面，包含餐厅封面、主厨推荐、招牌菜展示、营业信息和底部预约按钮。",
    ),
    (
        "coffee_shop",
        "咖啡点单",
        "一句门店点单需求，生成分类、商品、购物车和结算栏都能看见的小程序 MVP。",
        "生成一个咖啡店点单小程序页面，包含门店封面、分类 Tab、商品列表、购物车和底部结算栏。",
    ),
]


def read_case(case_id: str) -> dict[str, str]:
    folder = GOLDEN_DIR / case_id
    return {
        ext: (folder / f"index.{ext}").read_text(encoding="utf-8", errors="replace")
        for ext in ("wxml", "wxss", "js")
    }


def phone_iframe(case_id: str) -> str:
    files = read_case(case_id)
    phone = render_phone_html(files["wxml"], files["wxss"], files["js"], app_wxss=APP_WXSS)
    b64 = base64.b64encode(phone.encode("utf-8")).decode("ascii")
    return f'<iframe class="phone-frame" src="data:text/html;base64,{b64}" loading="lazy"></iframe>'


def shell(title: str, body: str) -> str:
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
</body>
</html>
"""


CSS = """
:root{--ink:#141414;--muted:#646a73;--line:#e5e1d8;--paper:#fbfaf6;--surface:#fff;--green:#2f7d68;--accent:#b96b36}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"PingFang SC","Microsoft YaHei",sans-serif}
a{color:inherit}.wrap{max-width:1240px;margin:0 auto;padding:54px 24px 84px}.hero{min-height:74vh;display:grid;grid-template-columns:minmax(0,1.05fr) minmax(330px,.75fr);gap:48px;align-items:center;border-bottom:1px solid var(--line)}
.kicker{color:var(--green);text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:900}.hero h1{font-size:clamp(62px,8vw,112px);line-height:.9;margin:18px 0 24px}.lead{font-size:28px;line-height:1.25;margin:0 0 18px}.sub{font-size:17px;color:var(--muted);line-height:1.75;max-width:720px}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}.btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 18px;border-radius:7px;border:1px solid var(--ink);font-weight:800;text-decoration:none}.btn.primary{background:var(--ink);color:#fff}
.artifact{background:#181816;color:#f6f0df;border-radius:8px;padding:22px;box-shadow:0 24px 60px rgba(20,20,20,.2)}.artifact-head{display:flex;justify-content:space-between;color:#c7bfa9;font-size:12px;margin-bottom:22px}.node{border:1px solid rgba(255,255,255,.15);border-radius:7px;padding:15px 16px;background:rgba(255,255,255,.055);margin-bottom:12px}.node strong{display:block;margin-bottom:4px}.node span{color:#c7bfa9;font-size:13px}
.section{padding:58px 0;border-bottom:1px solid var(--line)}.section h2{font-size:36px;margin:0 0 12px}.section-intro{color:var(--muted);line-height:1.7;max-width:780px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:28px}.grid.five{grid-template-columns:repeat(5,minmax(0,1fr))}.card{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:20px;box-shadow:0 10px 30px rgba(48,43,35,.05)}.card h3{margin:0 0 8px;font-size:18px}.card p{margin:0;color:var(--muted);line-height:1.6;font-size:14px}
.case{display:grid;grid-template-columns:.46fr .54fr;gap:36px;align-items:center;padding:38px 0;border-top:1px solid var(--line)}.case:nth-child(even){grid-template-columns:.54fr .46fr}.case:nth-child(even) .copy{order:2}.case:nth-child(even) .phone-wrap{order:1}.case-id{color:var(--green);font-size:12px;font-weight:900;letter-spacing:.1em;text-transform:uppercase}.case h3{font-size:34px;margin:12px 0}.chips{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.chips span{background:#fff;border:1px solid var(--line);border-radius:999px;padding:6px 10px;font-size:12px}.prompt{background:#f6f2ea;border:1px solid #ebe3d6;border-radius:8px;padding:14px 16px;line-height:1.7;color:#2d2d2d}.phone-wrap{background:#f1f3f6;padding:18px;border-radius:8px}.phone-frame{width:100%;height:760px;border:0;background:transparent}
.pipe{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}.pipe div{background:#191919;color:#fff;border-radius:8px;padding:16px 12px;min-height:86px}.pipe span{display:block;color:#bcbcbc;font-size:12px;margin-top:7px}
.live-hero{min-height:100vh;display:grid;grid-template-columns:minmax(0,.9fr) minmax(360px,1fr);gap:42px;align-items:center}.studio{background:#fff;border:1px solid var(--line);border-radius:8px;padding:24px}.studio textarea{width:100%;min-height:210px;border:1px solid #d9d4c8;border-radius:8px;padding:16px;font-size:15px;line-height:1.6;resize:vertical}.trace{display:grid;gap:10px;margin-top:18px}.trace div{background:#f8f4ec;border:1px solid #eadfce;border-radius:8px;padding:12px 14px}.preview-note{color:var(--muted);font-size:13px;line-height:1.6;margin-top:12px}
@media(max-width:900px){.hero,.live-hero,.case,.case:nth-child(even),.grid,.grid.five,.pipe{grid-template-columns:1fr}.case:nth-child(even) .copy,.case:nth-child(even) .phone-wrap{order:initial}.phone-frame{height:680px}}
"""


def build_index() -> str:
    cases_html = []
    for case_id, title, positioning, prompt in CASES:
        cases_html.append(
            f"""<article class="case">
  <div class="copy">
    <div class="case-id">{html.escape(case_id)}</div>
    <h3>{html.escape(title)}</h3>
    <p class="section-intro">{html.escape(positioning)}</p>
    <div class="chips"><span>小程序 MVP</span><span>手机预览</span><span>可下载工程</span></div>
    <div class="prompt">{html.escape(prompt)}</div>
  </div>
  <div class="phone-wrap">{phone_iframe(case_id)}</div>
</article>"""
        )
    return shell(
        f"{PRODUCT_NAME} Showcase",
        f"""<main class="wrap">
  <section class="hero">
    <div>
      <div class="kicker">GDG Shanghai Gemma 4 Hackathon / Track A</div>
      <h1>{PRODUCT_NAME}</h1>
      <p class="lead">小程序 MVP 生成智能体</p>
      <p class="sub"><strong>{TAGLINE}</strong><br>{POWERED} 面向小微商家、本地门店和个体经营者，把一句自然语言生意需求转成可预览、可下载的小程序 MVP。</p>
      <div class="actions"><a class="btn primary" href="/live">Open MVP Generator</a><a class="btn" href="#cases">View MVP Cases</a></div>
    </div>
    <div class="artifact">
      <div class="artifact-head"><span>MVP generation pipeline</span><span>live</span></div>
      <div class="node"><strong>Business Brief</strong><span>一句生意需求进入生成链路</span></div>
      <div class="node"><strong>Gemma 4 Tool Calling</strong><span>create_miniprogram_page(wxml, wxss, js)</span></div>
      <div class="node"><strong>Validator + Repair</strong><span>先校验，再自愈，减少坏代码出站</span></div>
      <div class="node"><strong>Phone Preview + ZIP</strong><span>375px 手机预览 + 小程序工程导出</span></div>
    </div>
  </section>
  <section class="section">
    <h2>为什么值得做</h2>
    <p class="section-intro">MiniPilot Agent 面向的是最常见、最实际的小程序原型需求：先看见 MVP，再决定要不要继续投入。</p>
    <div class="grid">
      <div class="card"><h3>小商家需要先看到</h3><p>咖啡点单、门店预约、活动报名、商品展示这些需求能说清楚，但很难马上变成可看的页面。</p></div>
      <div class="card"><h3>MVP 不该先烧预算</h3><p>早期验证常常只需要一个能演示、能讨论、能下载的小程序原型。</p></div>
      <div class="card"><h3>反馈应该更早发生</h3><p>把沟通、设计、开发、返工的长链路压缩成一次自然语言输入。</p></div>
    </div>
  </section>
  <section class="section">
    <h2>技术亮点</h2>
    <div class="grid five">
      <div class="card"><h3>Gemma 4 Tool Calling</h3><p>模型通过工具调用输出 wxml / wxss / js 三件套。</p></div>
      <div class="card"><h3>Agentic Workflow</h3><p>需求理解、上下文组装、代码生成、解析、校验、自愈和预览形成闭环。</p></div>
      <div class="card"><h3>Static Validator</h3><p>自动拦截 HTML 混入、危险 API、路径污染和小程序语法高频错误。</p></div>
      <div class="card"><h3>Grounded Assets</h3><p>本地图片素材进入 Zip/projectPath，避免真机看不到图。</p></div>
      <div class="card"><h3>Dual Backend</h3><p>Google AI Studio 与 AMD vLLM Gemma 31B 共用同一工具协议。</p></div>
    </div>
  </section>
  <section class="section" id="cases"><h2>精选 MVP 案例</h2><p class="section-intro">3 个最适合评审快速理解的真实小程序 MVP，手机预览由仓库 golden examples 渲染生成。</p></section>
  {''.join(cases_html)}
  <section class="section">
    <h2>技术架构</h2>
    <div class="pipe">
      <div>Business Prompt<span>one-line need</span></div><div>Gemma 4<span>tool calling</span></div><div>Page Code<span>wxml / wxss / js</span></div><div>Validator<span>hard errors / warnings</span></div><div>Repair Loop<span>self-correction</span></div><div>MVP Export<span>preview / zip</span></div>
    </div>
  </section>
</main>""",
    )


def build_live() -> str:
    return shell(
        f"{PRODUCT_NAME} Live Demo",
        f"""<main class="wrap">
  <section class="live-hero">
    <div>
      <div class="kicker">MiniPilot Agent · Live MVP Generator</div>
      <h1>从一句生意需求到小程序 MVP</h1>
      <p class="sub"><strong>{TAGLINE}</strong> {POWERED}<br>Vercel 展示版复刻 8505 的输入与流程说明；完整实时生成链路仍由本地 Streamlit / 模型网关运行。</p>
      <div class="actions"><a class="btn primary" href="/">Back to Showcase</a></div>
    </div>
    <div class="studio">
      <label><strong>自然语言需求</strong></label>
      <textarea>生成一个咖啡店点单小程序页面，包含门店封面、分类 Tab、商品列表、购物车和底部结算栏。</textarea>
      <div class="trace">
        <div><strong>01 Requirement Understanding</strong><br>识别商家类型、页面模块和交易路径。</div>
        <div><strong>02 Gemma 4 Tool Calling</strong><br>调用 create_miniprogram_page 生成 wxml / wxss / js。</div>
        <div><strong>03 Static Validator</strong><br>校验 WXML 规则、图片路径、事件绑定和危险 API。</div>
        <div><strong>04 Preview / ZIP</strong><br>手机预览并导出可导入微信开发者工具的小程序工程。</div>
      </div>
      <p class="preview-note">提示：为了保证 Vercel 链接稳定打开，这里是 8505 的公开展示门面，不在浏览器端暴露模型 API Key。</p>
    </div>
  </section>
</main>""",
    )


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
                "routes": [
                    {"src": "/live", "dest": "/live.html"},
                    {"src": "/(.*)", "dest": "/index.html"},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(OUT)


if __name__ == "__main__":
    main()
