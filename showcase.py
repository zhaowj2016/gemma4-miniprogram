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
    ("michelin_restaurant",  "🍽️ 高端餐厅点餐"),
    ("restaurant_menu",      "🍜 餐厅点餐"),
    ("profile",              "👤 个人中心"),
    ("course_detail",        "📚 课程详情"),
]


# ── Streamlit UI ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Gemma Match · 效果展示",
    page_icon="🎨",
    layout="wide",
)
st.title("🎨 Gemma Match · 5 场景效果展示")
st.caption(
    "Gemma 4 Native Function Calling 生成的微信小程序代码，"
    "在浏览器中模拟 375px 手机宽度实时渲染。"
)

tabs = st.tabs([label for _, label in SHOWCASE])

for tab, (folder, label) in zip(tabs, SHOWCASE):
    with tab:
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
