"""
Gemma Match · 黄金样例「仿真机」预览服务器（独立运行，不依赖也不修改其他模块的行为）
================================================================================
单独开一个本地 HTTP 服务，把 golden_examples/high_quality 下的 3 个高质量样例
渲染进 375px 手机外壳里，并加载真实的 WeChat 运行时 shim，可以直接在浏览器中
点击底部 tabBar 切换、输入文字、点按钮看 toast —— 即「仿真机」交互预览。

复用了项目里现成的 render_wxml.render_phone_html（只读调用，不改其内部逻辑）。

启动：
    python preview_golden.py            # 默认 http://127.0.0.1:8700
    python preview_golden.py 9000       # 指定端口

注意：样例里的图片是 /assets/library/*.jpg 占位路径，本地无此资源，预览时会自动
回退到 picsum 随机占位图（这是 render_wxml 既有的容错行为），不影响布局与交互演示。
"""
from __future__ import annotations

import sys
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "gemma_core"))

from render_wxml import render_phone_html  # noqa: E402

try:
    from scaffold import APP_WXSS  # noqa: E402
except Exception:
    APP_WXSS = ""

HQ_DIR = os.path.join(BASE_DIR, "golden_examples", "high_quality")

EXAMPLES = [
    ("product_detail", "高级商品详情页", "HeroBanner 轮播 · 规格卡片 · 加购/购买 toast"),
    ("event_signup", "高级活动报名页", "活动主视觉 · 报名表单 input · 提交 toast"),
    ("store_booking", "高级门店预约页", "门店 Hero · 服务/日期/时段选择 · 预约 toast"),
]


def _load(name: str) -> dict:
    d = os.path.join(HQ_DIR, name)
    out = {}
    for ext in ("wxml", "wxss", "js"):
        path = os.path.join(d, f"index.{ext}")
        with open(path, "r", encoding="utf-8") as f:
            out[ext] = f.read()
    return out


def render_one(name: str) -> str:
    files = _load(name)
    return render_phone_html(
        files["wxml"], files["wxss"], files["js"], app_wxss=APP_WXSS
    )


def index_page() -> str:
    cards = []
    for name, title, desc in EXAMPLES:
        cards.append(
            f"""
      <section class="col">
        <div class="meta">
          <h2>{title}</h2>
          <p>{desc}</p>
          <code>golden_examples/high_quality/{name}/</code>
        </div>
        <iframe class="phone-frame" src="/phone?name={name}" loading="lazy"></iframe>
      </section>"""
        )
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gemma Match · 黄金样例仿真机预览</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0f1115;color:#e8eaed;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;padding:32px 24px 60px}}
  header{{max-width:1240px;margin:0 auto 28px}}
  header h1{{font-size:24px;font-weight:800}}
  header p{{color:#9aa0a6;margin-top:8px;font-size:14px;line-height:1.6}}
  .grid{{max-width:1240px;margin:0 auto;display:flex;flex-wrap:wrap;gap:28px;justify-content:center}}
  .col{{display:flex;flex-direction:column;align-items:center;width:392px}}
  .meta{{width:100%;background:#1a1d24;border:1px solid #262a33;border-radius:14px;padding:16px 18px;margin-bottom:16px}}
  .meta h2{{font-size:17px;font-weight:700}}
  .meta p{{color:#9aa0a6;font-size:13px;margin:6px 0 10px;line-height:1.5}}
  .meta code{{font-size:12px;color:#7cc0ff;background:#11151c;padding:4px 8px;border-radius:6px;display:inline-block}}
  .phone-frame{{width:392px;height:760px;border:none;border-radius:24px;background:transparent}}
  footer{{max-width:1240px;margin:36px auto 0;color:#5f6571;font-size:12px;line-height:1.7;text-align:center}}
</style>
</head>
<body>
  <header>
    <h1>🎨 Gemma Match · 黄金样例「仿真机」预览</h1>
    <p>下面三台手机各自加载了一个高质量教学样例，内置 WeChat 运行时 shim —— 直接点击底部 tabBar 切换 activeTab、在输入框打字、点按钮看 toast，即可验证交互。图片为占位路径，预览自动回退随机占位图。</p>
  </header>
  <div class="grid">{''.join(cards)}</div>
  <footer>这是独立的只读预览服务（preview_golden.py），不修改生成链路 / app.py / showcase.py 的任何行为。</footer>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, status: int = 200):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send(index_page())
            return
        if parsed.path == "/phone":
            name = (parse_qs(parsed.query).get("name") or [""])[0]
            if name not in {e[0] for e in EXAMPLES}:
                self._send("<h1>404 - unknown example</h1>", 404)
                return
            try:
                self._send(render_one(name))
            except Exception as exc:  # surface render errors in the iframe
                self._send(f"<pre>render error: {exc}</pre>", 500)
            return
        self._send("<h1>404</h1>", 404)

    def log_message(self, *args):
        pass  # keep console quiet


def main():
    port = 8700
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print("=" * 60)
    print("  Gemma Match · 黄金样例仿真机预览服务已启动")
    print(f"  打开浏览器访问： {url}")
    print("  按 Ctrl+C 停止")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止预览服务。")
        server.shutdown()


if __name__ == "__main__":
    main()
