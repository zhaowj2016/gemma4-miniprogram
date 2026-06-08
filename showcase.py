"""
Gemma Match — 5 场景效果展示
手机外框内实时渲染 WXML/WXSS，左预览右代码
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "gemma_core"))

import base64
import streamlit as st

from golden_examples import load_golden_from_folder
from scaffold import APP_WXSS
from render_wxml import render_phone_html

SHOWCASE = [
    ("ai_wedding_studio",    "💍 AI婚礼工作室"),
    ("michelin_restaurant",  "🍽️ 米其林餐厅"),
    ("coffee_shop",          "☕ 咖啡点单"),
    ("restaurant_menu",      "🍜 餐厅点餐"),
    ("luxury_service",       "💎 高端定制服务"),
    ("profile",              "👤 个人中心"),
    ("course_detail",        "📚 课程详情"),
]

# 对比展位：AMD vLLM 网关生成效果，"打磨前"与"打磨后"各一栏，
# 用于直观对比"第 2 步生成"和"第 3 步 31B 自检优化"之间的差距。
AMD_VLLM_RAW_DIR = os.path.join(os.path.dirname(__file__), "demo_cache", "amd_vllm_demo")
AMD_VLLM_REVIEWED_DIR = os.path.join(os.path.dirname(__file__), "demo_cache", "amd_vllm_demo_reviewed")
AMD_VLLM_RAW_LABEL = "🔬 AMD vLLM·打磨前（仅第2步生成）"
AMD_VLLM_REVIEWED_LABEL = "✨ AMD vLLM·打磨后（含第3步自检）"


def _load_demo_dir(dir_path: str) -> dict:
    result = {}
    for ext in ("wxml", "wxss", "js"):
        path = os.path.join(dir_path, f"{ext}.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                result[ext] = f.read().strip()
    return result


# ── Streamlit UI ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Gemma Match · 效果展示",
    page_icon="🎨",
    layout="wide",
)
st.title(f"🎨 Gemma Match · {len(SHOWCASE)} 场景效果展示 + 1 个对比展位")
st.caption(
    "Gemma 4 Native Function Calling 生成的微信小程序代码，"
    "在浏览器中模拟 375px 手机宽度实时渲染。"
)

DEMO_TABS = [
    (AMD_VLLM_RAW_LABEL, AMD_VLLM_RAW_DIR,
     "这一栏是 AMD vLLM 网关 31B 模型**单次** generate 调用的原始产出"
     "（未经过 pipeline 第 3 步 31B 自检优化、也未经自愈重试），"
     "刻意保留打磨前的样子，方便跟右边一栏对比——能直观看到「自检优化」这一步实际带来了多少提升。"),
    (AMD_VLLM_REVIEWED_LABEL, AMD_VLLM_REVIEWED_DIR,
     "这一栏是把左边那份「打磨前」的代码，喂给 AMD vLLM 31B 走完 pipeline 第 3 步"
     "（`build_review_prompt` 自检优化）之后的产出——和 app.py 实际交付给用户的最终结果是同一条链路、"
     "同一个模型，可以直接当作「AMD vLLM 全流程最终效果」来看。"),
]
all_entries = SHOWCASE + [(None, lbl) for lbl, _, _ in DEMO_TABS]
all_labels = [label for _, label in SHOWCASE] + [lbl for lbl, _, _ in DEMO_TABS]
tabs = st.tabs(all_labels)

for tab, (folder, label) in zip(tabs, all_entries):
    with tab:
        if folder is None:
            _, demo_dir, demo_note = next(d for d in DEMO_TABS if d[0] == label)
            files = _load_demo_dir(demo_dir)
            st.info(demo_note)
        else:
            files = load_golden_from_folder(folder)
        wxml = files.get("wxml", "")
        wxss = files.get("wxss", "")
        js   = files.get("js", "")

        col_phone, col_code = st.columns([5, 7], gap="large")

        with col_phone:
            st.markdown(f"**{label} — 手机预览**")
            try:
                phone_html = render_phone_html(wxml, wxss, js, app_wxss=APP_WXSS)
                b64 = base64.b64encode(phone_html.encode("utf-8")).decode("ascii")
                st.iframe(f"data:text/html;base64,{b64}", height=720)
            except Exception as e:
                st.error(f"渲染失败：{e}")
                import traceback
                st.code(traceback.format_exc())

        with col_code:
            st.markdown(f"**{label} — 生成代码**")
            code_tabs = st.tabs(["📄 WXML", "🎨 WXSS", "⚡ JS"])
            with code_tabs[0]:
                st.code(wxml, language="html", line_numbers=True)
            with code_tabs[1]:
                st.code(wxss, language="css", line_numbers=True)
            with code_tabs[2]:
                st.code(js, language="javascript", line_numbers=True)

            # Quick stats
            wxml_lines = len(wxml.splitlines())
            wxss_lines = len(wxss.splitlines())
            js_lines   = len(js.splitlines())
            st.caption(
                f"代码量：WXML {wxml_lines} 行 · WXSS {wxss_lines} 行 · JS {js_lines} 行 "
                f"· 共 {wxml_lines+wxss_lines+js_lines} 行"
            )
