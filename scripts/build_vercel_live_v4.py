from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "vercel_minipilot" / "live.html"


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MiniPilot Agent Live Demo</title>
  <style>
    :root{
      --paper:#f6f5f1;--surface:#fff;--surface-soft:#fbfaf6;--ink:#15171a;--ink-soft:#4d525a;--muted:#888c92;
      --line:#e7e2d6;--line-soft:#f1eee5;--accent:#b8632f;--accent-strong:#8c4622;--accent-soft:#f8ede1;
      --green:#2f7d68;--green-soft:#e6f1ec;--red:#c23b54;--red-soft:#f8e9ec;--amber:#b08a2e;--amber-soft:#f5f0e1;
      --zone-trace:#2c4a6e;--zone-trace-soft:#e8eef4;--zone-trace-strong:#1c3552;--zone-preview:#7c6a9c;--zone-preview-soft:#efecf4;--zone-preview-strong:#5e4f7a;
      --shadow-xs:0 1px 3px rgba(21,23,26,.045);--shadow-sm:0 6px 20px rgba(21,23,26,.055);--shadow-md:0 16px 44px rgba(21,23,26,.09);
      --r-sm:10px;--r-md:16px;--r-lg:24px;--ease:cubic-bezier(.22,.8,.25,1);
      --font:-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Helvetica Neue","Segoe UI","Microsoft YaHei UI","Microsoft YaHei",sans-serif;
    }
    *{box-sizing:border-box}html,body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--font)}button,textarea,input{font:inherit}a{color:var(--accent);font-weight:700;text-decoration:none}
    .wrap{max-width:1480px;margin:0 auto;padding:2.1rem 3rem 4rem}.topbar{display:flex;justify-content:space-between;gap:26px;align-items:flex-end;border-bottom:1px solid var(--line);padding-bottom:30px;margin-bottom:38px}
    .eyebrow{margin:0 0 14px;font-size:11.5px;font-weight:800;letter-spacing:.26em;text-transform:uppercase;color:var(--accent)}h1{font-size:64px;font-weight:800;margin:0 0 16px;letter-spacing:-.035em;line-height:1.04}.accent-word{color:var(--accent)}
    .title p:last-child{margin:0;color:var(--ink-soft);line-height:1.7;max-width:720px;font-size:15.5px}.status-pills{display:flex;gap:9px;flex-wrap:wrap;justify-content:flex-end}.pill{border:1px solid var(--line);border-radius:999px;padding:8px 14px;font-size:12px;font-weight:600;background:var(--surface);color:var(--ink-soft);box-shadow:var(--shadow-xs)}.pill b{color:var(--ink)}
    .empty{display:grid;grid-template-columns:.16fr 1fr .16fr}.result{display:grid;grid-template-columns:.74fr 1.13fr 1.13fr;gap:28px;align-items:start}.rail{min-width:0}.panel{background:transparent}.panel-title{margin:0 0 16px;font-size:12.5px;font-weight:800;color:var(--ink);text-transform:uppercase;letter-spacing:.14em;display:flex;align-items:center;gap:9px}.panel-title::before{content:"";width:7px;height:7px;border-radius:99px;background:var(--accent);display:inline-block}.panel-title.zone-trace{color:var(--zone-trace-strong)}.panel-title.zone-trace::before{background:var(--zone-trace)}.panel-title.zone-preview{color:var(--zone-preview-strong)}.panel-title.zone-preview::before{background:var(--zone-preview)}
    label{display:block;margin:0 0 7px;color:var(--ink-soft);font-size:14px}.textarea{width:100%;min-height:170px;border:1px solid var(--line);border-radius:var(--r-sm);background:var(--surface);font-size:14.5px;line-height:1.6;padding:14px 16px;resize:vertical;outline-color:var(--accent)}.empty .textarea{min-height:240px}
    .chip-label{font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:18px 0 11px}.chips{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:20px}.btn{border-radius:var(--r-sm);min-height:44px;font-weight:700;border:1px solid var(--line);background:var(--surface);color:var(--ink-soft);padding:0 16px;cursor:pointer;transition:all .18s var(--ease)}.btn:hover{border-color:var(--accent);color:var(--accent-strong);transform:translateY(-1px);box-shadow:var(--shadow-sm)}.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff;box-shadow:0 8px 22px rgba(44,74,110,.28)}.btn.primary:hover{background:var(--accent-strong);border-color:var(--accent-strong);color:#fff}.btn.small{min-height:36px;padding:0 13px;font-size:13px}.btn:disabled{opacity:.55;cursor:not-allowed;transform:none}
    .mode{display:grid;gap:10px;margin:20px 0;color:#333;font-size:14px}.mode label{display:flex;gap:8px;align-items:flex-start}.upload{border:1.5px dashed var(--line);border-radius:var(--r-md);padding:14px;background:var(--surface-soft);margin:16px 0}.upload input{width:100%}.notice{margin-top:12px;color:var(--muted);font-size:13px;line-height:1.6}
    .flow-steps{display:flex;flex-direction:column;gap:0;margin:16px 2px 18px}.flow-step{display:flex;align-items:flex-start;gap:11px;padding:7px 0;position:relative}.flow-step::before{content:"";position:absolute;left:11px;top:30px;width:1.5px;height:22px;background:var(--line)}.flow-step:last-child::before{display:none}.flow-step b{flex:none;display:inline-flex;align-items:center;justify-content:center;width:23px;height:23px;border-radius:99px;background:var(--surface);border:1.5px solid var(--line);color:var(--muted);font-size:11px;font-weight:800;z-index:1}.flow-step span{font-size:13px;font-weight:600;color:var(--muted);padding-top:2px}.flow-step.is-active b{background:var(--accent);border-color:var(--accent);color:#fff;box-shadow:0 0 0 4px var(--accent-soft)}.flow-step.is-active span{color:var(--accent-strong);font-weight:700}.flow-step.is-done b{background:var(--green);border-color:var(--green);color:#fff}
    .trace-list{position:relative;display:grid;gap:10px;padding-left:5px}.trace-list::before{content:"";position:absolute;left:27px;top:24px;bottom:24px;width:2px;background:linear-gradient(180deg,var(--zone-trace-soft),var(--line) 85%);z-index:0}.trace-item{position:relative;z-index:1;display:grid;grid-template-columns:46px minmax(0,1fr);gap:13px;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);padding:14px 16px;box-shadow:var(--shadow-xs)}.trace-badge{height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:10px;font-weight:800;letter-spacing:.04em;background:#9a9da3;box-shadow:0 0 0 4px var(--surface)}.trace-success .trace-badge{background:var(--green)}.trace-warning .trace-badge{background:var(--amber)}.trace-error .trace-badge{background:var(--red)}.trace-running .trace-badge{background:var(--zone-trace);animation:pulse 1.6s ease-in-out infinite}@keyframes pulse{50%{box-shadow:0 0 0 4px var(--zone-trace-soft)}}.trace-item h4{margin:0 0 4px;font-size:14.5px}.trace-step{font-size:10.5px;font-weight:800;letter-spacing:.1em;color:var(--zone-trace);margin-right:7px}.trace-item p{margin:0;color:var(--muted);font-size:13px;line-height:1.55}.trace-metrics{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}.trace-metrics span{border:1px solid var(--line-soft);border-radius:999px;padding:4px 9px;color:var(--ink-soft);font-size:11px;background:var(--surface-soft)}
    .phone-stage{background:linear-gradient(165deg,var(--zone-preview-soft) 0%,var(--surface) 46%);border:1px solid var(--zone-preview-soft);border-radius:var(--r-lg);padding:22px 18px 16px;box-shadow:0 16px 40px -22px var(--zone-preview)}iframe{width:100%;height:720px;border:0;border-radius:30px;background:transparent}.source{margin-top:34px;border-top:1px solid var(--line);padding-top:28px}.tabs{display:flex;gap:8px;margin-bottom:12px}.tab{border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:7px 13px;cursor:pointer}.tab.active{background:var(--ink);color:#fff;border-color:var(--ink)}pre{margin:0;padding:18px;border-radius:var(--r-sm);border:1px solid var(--line);background:#111;color:#f4f4f4;font:12px/1.55 Consolas,Monaco,monospace;white-space:pre-wrap;max-height:520px;overflow:auto}.debug-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}.toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#141414;color:#fff;padding:10px 14px;border-radius:999px;display:none;z-index:30}.toast.show{display:block}.hidden{display:none!important}
    @media(max-width:1100px){.wrap{padding:28px 18px 64px}.topbar,.result{display:block}.status-pills{justify-content:flex-start;margin-top:14px}h1{font-size:38px}.panel{margin-bottom:28px}iframe{height:660px}.empty{display:block}.debug-grid{grid-template-columns:1fr}}
  </style>
</head>
<body>
<main class="wrap">
  <header class="topbar">
    <div class="title">
      <p class="eyebrow">MiniPilot Agent · Live MVP Generator</p>
      <h1>从<span class="accent-word">一句生意需求</span>到小程序 MVP</h1>
      <p>一句生意需求，生成小程序 MVP。 Powered by Gemma 4. 描述你的商家需求，Gemma 4 会生成可预览、可下载的小程序页面代码。</p>
    </div>
    <div class="status-pills">
      <span class="pill">Backends&nbsp;<b>Google AI Studio Gemma 4</b></span>
      <span class="pill">●&nbsp;Live Generation</span>
      <span class="pill"><a href="/">← Back to Showcase</a></span>
    </div>
  </header>

  <section id="emptyState" class="empty">
    <div></div>
    <div class="panel"><div id="inputEmpty"></div></div>
    <div></div>
  </section>

  <section id="resultState" class="result hidden">
    <aside class="panel rail">
      <h3 class="panel-title">Brief</h3>
      <div id="inputResult"></div>
    </aside>
    <section class="panel">
      <h3 class="panel-title zone-trace">Gemma Agent Trace</h3>
      <div class="trace-list" id="traceList"></div>
    </section>
    <aside class="panel">
      <h3 class="panel-title zone-preview">Phone Preview</h3>
      <div class="phone-stage"><iframe id="phoneFrame" title="Phone preview"></iframe></div>
    </aside>
  </section>

  <section id="sourceSection" class="source hidden">
    <h3 class="panel-title">Generated Source</h3>
    <div class="tabs">
      <button class="tab active" data-tab="wxml">WXML</button>
      <button class="tab" data-tab="wxss">WXSS</button>
      <button class="tab" data-tab="js">JS</button>
    </div>
    <pre id="codeBlock"></pre>
    <div class="debug-grid">
      <div>
        <h3 class="panel-title">Validator</h3>
        <pre id="validatorBlock"></pre>
      </div>
      <div>
        <h3 class="panel-title">Debug</h3>
        <pre id="debugBlock"></pre>
      </div>
    </div>
  </section>
</main>
<div class="toast" id="toast"></div>

<template id="inputTemplate">
  <label>自然语言需求</label>
  <textarea class="textarea" id="promptInput" placeholder="例如：生成一个咖啡店点单小程序页面，包含门店封面、分类 Tab、商品列表、购物车和底部结算栏。"></textarea>
  <p class="chip-label">没有思路？试试这些</p>
  <div class="chips">
    <button class="btn small" data-prompt="生成一个咖啡店点单小程序页面，包含门店封面、分类 Tab、商品列表、购物车和底部结算栏。">咖啡店点单</button>
    <button class="btn small" data-prompt="生成一个餐厅菜单小程序页面，包含菜品分类、推荐菜、价格、购物车和下单按钮。">餐厅菜单页</button>
    <button class="btn small" data-prompt="生成一个电商商品详情页，包含商品主图、价格、规格选择、优惠信息和底部购买按钮。">商品详情页</button>
    <button class="btn small" data-prompt="生成一个 AI 婚礼美学工作室小程序页面，包含作品集、AI 服务、套餐预约、底部导航和高级黑金视觉风格。">AI 婚礼页</button>
  </div>
  <div class="mode">
    <label><input type="radio" checked /> 快速 Agent 模式（Google AI Studio 主链路）</label>
    <label><input type="radio" disabled /> 深度生成模式（AMD vLLM Gemma 31B 自托管·本地 8505 可用）</label>
  </div>
  <div class="upload">
    <label>上传参考图片（可选 · 多模态）</label>
    <input type="file" id="imageInput" multiple accept="image/jpeg,image/png,image/webp,image/gif,image/bmp" />
    <p class="notice" id="imageNotice">支持 JPG / PNG / WebP / GIF / BMP。Vercel 版会把图片随请求传给 Gemma 4，并优先放入 hero/banner。</p>
  </div>
  <div class="flow-steps">
    <div class="flow-step is-done"><b>✓</b><span>描述你的小程序需求</span></div>
    <div class="flow-step"><b>2</b><span>AI 澄清确认（本地 8505 版）</span></div>
    <div class="flow-step is-active"><b>3</b><span>生成小程序代码并预览</span></div>
  </div>
  <div class="chips">
    <button class="btn" id="analyzeBtn" disabled>AI 需求分析</button>
    <button class="btn primary" id="generateBtn">快速生成</button>
    <button class="btn" id="clearBtn">Clear</button>
  </div>
  <p class="notice">Vercel V4 版：前端保持 8505 的 Brief / Trace / Phone Preview / Source 工作台；生成由 /api/generate 在服务端调用 Google AI Studio，不在浏览器暴露 API Key。</p>
</template>

<script>
let files = null;
let trace = null;
let validation = null;
let activeTab = "wxml";
let images = [];

const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
const emptyInput = $("#inputEmpty");
const resultInput = $("#inputResult");
const inputTemplate = $("#inputTemplate").content.cloneNode(true);
emptyInput.appendChild(inputTemplate);

function syncInputIntoResult(){
  if (!resultInput.children.length) {
    resultInput.appendChild($("#inputEmpty").firstElementChild);
  }
}

function toast(text){
  const el = $("#toast");
  el.textContent = text;
  el.classList.add("show");
  setTimeout(()=>el.classList.remove("show"), 2200);
}

function promptEl(){ return $("#promptInput"); }
function setPrompt(text){ promptEl().value = text; }

async function readImages(){
  const input = $("#imageInput");
  const list = Array.from(input?.files || []).slice(0, 6);
  images = await Promise.all(list.map(file => new Promise(resolve => {
    const reader = new FileReader();
    reader.onload = () => resolve({ name:file.name, mime:file.type || "image/jpeg", data:String(reader.result) });
    reader.readAsDataURL(file);
  })));
  $("#imageNotice").textContent = images.length ? `已加载 ${images.length} 张参考图片，生成时会一起传给 Gemma 4。` : "支持 JPG / PNG / WebP / GIF / BMP。Vercel 版会把图片随请求传给 Gemma 4，并优先放入 hero/banner。";
}

function lineCount(s){ return String(s || "").split(/\r?\n/).length; }

function renderTrace(state, errorText){
  const prompt = promptEl()?.value || "";
  const lines = files ? lineCount(files.wxml)+lineCount(files.wxss)+lineCount(files.js) : 0;
  const steps = [
    ["Requirement Understanding", `识别行业、页面目标、交易/预约路径。`, [`prompt chars ${prompt.trim().length}`]],
    ["Context Assembly", `组合 prompt builder、asset_list 与图片规则。`, [`images ${images.length}`, trace ? `built prompt ${trace.built_prompt_chars}` : "asset_list ready"]],
    ["Function Calling", state === "error" ? errorText : `create_miniprogram_page(wxml, wxss, js)`, [trace ? `provider Google AI Studio` : "provider pending", trace ? `elapsed ${trace.elapsed}s` : ""]],
    ["Code Parsing", files ? `WXML / WXSS / JS extracted.` : "等待模型返回代码。", [files ? `source lines ${lines}` : ""]],
    ["Static Validator", validation ? (validation.ok ? "Validator passed: no hard errors." : "Validator reported issues.") : "等待校验。", validation ? [`errors ${validation.hard_errors?.length || 0}`, `warnings ${validation.warnings?.length || 0}`] : []],
  ];
  $("#traceList").innerHTML = steps.map((s, i) => {
    const cls = state === "error" && i === 2 ? "trace-error" : state === "running" && i >= 2 ? "trace-running" : state === "idle" ? "" : "trace-success";
    const badge = state === "running" && i >= 2 ? "..." : state === "error" && i === 2 ? "ERR" : "OK";
    return `<div class="trace-item ${cls}"><span class="trace-badge">${badge}</span><div><h4><span class="trace-step">STEP ${String(i+1).padStart(2,"0")}</span>${s[0]}</h4><p>${s[1] || ""}</p><div class="trace-metrics">${(s[2]||[]).filter(Boolean).map(m=>`<span>${m}</span>`).join("")}</div></div></div>`;
  }).join("");
}

function renderSource(){
  if (!files) return;
  $("#sourceSection").classList.remove("hidden");
  $$(".tab").forEach(t => t.classList.toggle("active", t.dataset.tab === activeTab));
  $("#codeBlock").textContent = files[activeTab] || "";
  $("#validatorBlock").textContent = JSON.stringify(validation || {}, null, 2);
  $("#debugBlock").textContent = JSON.stringify({ trace, provider: files.provider, parse_method: files.parse_method }, null, 2);
}

function showResults(){
  $("#emptyState").classList.add("hidden");
  $("#resultState").classList.remove("hidden");
  syncInputIntoResult();
}

async function generate(){
  const prompt = promptEl().value.trim();
  if (!prompt) return toast("请先输入自然语言需求");
  await readImages();
  showResults();
  files = null; trace = null; validation = null;
  renderTrace("running");
  $("#generateBtn").disabled = true;
  $("#generateBtn").textContent = "生成中...";
  try {
    const res = await fetch("/api/generate", {
      method:"POST",
      headers:{"content-type":"application/json"},
      body:JSON.stringify({ prompt, images })
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "生成失败");
    files = data.files;
    trace = data.trace;
    validation = data.validation;
    $("#phoneFrame").srcdoc = data.phoneHtml;
    renderTrace("done");
    renderSource();
    toast("Gemma 4 已生成小程序 MVP");
  } catch (err) {
    renderTrace("error", err.message || String(err));
    toast(err.message || String(err));
  } finally {
    $("#generateBtn").disabled = false;
    $("#generateBtn").textContent = "快速生成";
  }
}

document.addEventListener("click", e => {
  const p = e.target.closest("[data-prompt]");
  if (p) setPrompt(p.dataset.prompt);
  if (e.target.id === "generateBtn") generate();
  if (e.target.id === "clearBtn") { setPrompt(""); files=null; $("#resultState").classList.add("hidden"); $("#emptyState").classList.remove("hidden"); }
  const t = e.target.closest(".tab");
  if (t) { activeTab = t.dataset.tab; renderSource(); }
});
document.addEventListener("change", e => { if (e.target.id === "imageInput") readImages(); });

setPrompt(new URLSearchParams(location.search).get("prompt") || "生成一个咖啡店点单小程序页面，包含门店封面、分类 Tab、商品列表、购物车和底部结算栏。");
renderTrace("idle");
</script>
</body>
</html>
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(HTML, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
