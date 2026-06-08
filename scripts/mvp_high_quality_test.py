"""
最小 MVP：验证「高质量黄金样例」作为 few-shot 让 Gemma 学习并生成新页面的全链路。

跑通的链路（与 app.py 实际生产链路一致）：
    build_prompt(注入 1 个最相关的高质量黄金样例)  ->  call_gemma_with_tools(Gemma)
        ->  validators.validate_project(静态校验)  ->  失败则 build_repair_prompt 自愈一次
        ->  render_phone_html(仿真机预览)  ->  落盘 + 反抄袭对比

用法：
    python scripts/mvp_high_quality_test.py                      # 用默认 3 条需求
    python scripts/mvp_high_quality_test.py "帮我做一个花店预约页"   # 指定一条需求
    python scripts/mvp_high_quality_test.py --mode agent          # 强制走 Google AI Studio
    python scripts/mvp_high_quality_test.py --mode deep           # 强制走 AMD vLLM 网关

产物写入 dev_artifacts/mvp_output/<slug>/：index.wxml/wxss/js + preview.html
浏览器打开 preview.html 即可看到 Gemma 学样例后生成的真实效果。
"""
from __future__ import annotations

import sys
import os
import re
import time
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gemma_core"))

# Windows 控制台默认 GBK，强制 stdout 走 UTF-8，避免中文/符号 print 崩溃。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from prompt_builder import build_prompt, build_repair_prompt, _select_high_quality, _load_high_quality_examples  # noqa: E402
from gemma_client import call_gemma_with_tools  # noqa: E402
from validators import validate_project  # noqa: E402
from render_wxml import render_phone_html  # noqa: E402

try:
    from scaffold import APP_WXSS
except Exception:
    APP_WXSS = ""

OUT_ROOT = ROOT / "dev_artifacts" / "mvp_output"

DEFAULT_PROMPTS = [
    "帮我做一个精品手冲咖啡馆的线上商品详情页，可以选规格、加购物车",
    "做一个城市马拉松赛事的报名页面，有赛事介绍和报名表单",
    "我想要一个高端宠物美容店的到店预约页面，可以选服务和时间",
]


def slugify(text: str) -> str:
    s = re.sub(r"[^\w一-鿿]+", "_", text).strip("_")
    return s[:24] or "case"


def to_page_files(triple: dict) -> dict:
    return {
        "pages/index/index.wxml": triple["wxml"],
        "pages/index/index.wxss": triple["wxss"],
        "pages/index/index.js": triple["js"],
    }


def copy_overlap(generated_wxml: str, golden_wxml: str) -> float:
    """粗略的 8-gram 重合率，用来判断模型是否在机械照抄样例 WXML。"""
    def grams(s: str) -> set:
        toks = re.findall(r"[\w一-鿿]+", s)
        return {" ".join(toks[i:i + 8]) for i in range(max(0, len(toks) - 7))}
    g, h = grams(generated_wxml), grams(golden_wxml)
    if not g:
        return 0.0
    return len(g & h) / len(g)


def lines(triple: dict) -> dict:
    return {k: len(triple[k].splitlines()) for k in ("wxml", "wxss", "js")}


def run_one(prompt: str, mode: str) -> dict:
    print("\n" + "=" * 72)
    print(f"需求：{prompt}")
    print("=" * 72)

    # 1) 选中的高质量样例（学习对象）
    hq = _select_high_quality(prompt, _load_high_quality_examples())
    golden_wxml = hq["files"]["wxml"] if hq else ""
    print(f"[1/5] few-shot 学习对象 = {hq['id'] if hq else '(无)'} ({hq['title'] if hq else ''})")

    built = build_prompt(prompt)
    print(f"      prompt 体积：{len(built)} 字符（约 {len(built)//4} tokens）"
          f" | 含黄金样例引导：{'学习对象' in built}")

    # 2) 调用 Gemma
    print(f"[2/5] 调用 Gemma（mode={mode}）…")
    t0 = time.time()
    triple = call_gemma_with_tools(built, mode=mode)
    dt = time.time() - t0
    prov = triple.get("provider"); pm = triple.get("parse_method")
    print(f"      返回 OK（{dt:.1f}s）provider={prov} parse_method={pm} 行数={lines(triple)}")
    if triple.get("fallback_used"):
        print(f"      [注意] 发生跨后端兜底：{triple.get('fallback_reason')}")

    # 3) 静态校验
    files = to_page_files(triple)
    res = validate_project(files)
    print(f"[3/5] 静态校验：{'PASS' if res.ok else 'FAIL'} "
          f"(HARD {len(res.hard_errors)} / WARN {len(res.warnings)})")
    for e in res.hard_errors:
        print("        HARD:", e)

    # 4) 自愈一次（与 app.py 一致：把校验错误喂回模型）
    if not res.ok:
        print("[4/5] 触发自愈重生成…")
        repair = build_repair_prompt(prompt, files, res.hard_errors)
        try:
            triple = call_gemma_with_tools(repair, mode=mode)
            files = to_page_files(triple)
            res = validate_project(files)
            print(f"      自愈后：{'PASS' if res.ok else 'FAIL'} 行数={lines(triple)}")
        except Exception as e:
            print(f"      自愈调用失败：{e}")
    else:
        print("[4/5] 无需自愈")

    # 5) 反抄袭对比 + 渲染 + 落盘
    overlap = copy_overlap(triple["wxml"], golden_wxml)
    copied_brand = any(
        kw in triple["wxml"] for kw in ("晨光 S3", "灯塔 2026", "MUSE 美学空间")
    )
    print(f"[5/5] 反抄袭：与样例 WXML 的 8-gram 重合率 {overlap*100:.1f}% "
          f"| 直接照抄样例品牌名：{copied_brand}")

    out_dir = OUT_ROOT / slugify(prompt)
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("wxml", "wxss", "js"):
        (out_dir / f"index.{ext}").write_text(triple[ext], encoding="utf-8")
    try:
        html = render_phone_html(triple["wxml"], triple["wxss"], triple["js"], app_wxss=APP_WXSS)
        (out_dir / "preview.html").write_text(html, encoding="utf-8")
        print(f"      产物已写入：{out_dir}  （浏览器打开 preview.html 查看效果）")
    except Exception as e:
        print(f"      渲染预览失败：{e}")

    total = sum(lines(triple).values())
    return {
        "prompt": prompt, "golden": hq["id"] if hq else None,
        "provider": prov, "parse_method": pm, "ok": res.ok,
        "hard": len(res.hard_errors), "warn": len(res.warnings),
        "total_lines": total, "overlap": overlap, "copied_brand": copied_brand,
        "out_dir": str(out_dir),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", default=None)
    ap.add_argument("--mode", default="agent", choices=["auto", "agent", "deep"],
                    help="agent=优先Google AI Studio；deep=优先AMD vLLM；auto=系统决定")
    args = ap.parse_args()

    prompts = [args.prompt] if args.prompt else DEFAULT_PROMPTS
    summary = []
    for p in prompts:
        try:
            summary.append(run_one(p, args.mode))
        except Exception as e:
            print(f"!! 该需求失败：{e}")
            summary.append({"prompt": p, "error": str(e)})

    print("\n" + "#" * 72)
    print("MVP 汇总")
    print("#" * 72)
    for s in summary:
        if "error" in s:
            print(f"  [ERROR] {s['prompt'][:28]} -> {s['error'][:80]}")
            continue
        flag = "[PASS]" if s["ok"] else "[FAIL]"
        print(f"  {flag} 学[{s['golden']}] {s['provider']}/{s['parse_method']} "
              f"行{s['total_lines']} 重合{s['overlap']*100:.0f}% 抄品牌={s['copied_brand']} "
              f"-> {s['out_dir']}")


if __name__ == "__main__":
    main()
