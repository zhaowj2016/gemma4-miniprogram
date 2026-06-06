import os
# 修复Mac下Streamlit空白页面问题，切换文件监听模式
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "poll"
# 关闭遥测，消除启动邮箱弹窗
os.environ["STREAMLIT_TELEMETRY_ENABLED"] = "false"

import streamlit as st
from google import genai

# 读取本地环境变量的API Key
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 页面基础配置
st.set_page_config(page_title="Gemma4 小程序生成器", layout="wide")
st.title("🤖 Gemma4 AI 微信小程序生成平台")

# 左右分栏布局
col1, col2 = st.columns(2)

with col1:
    st.subheader("💬 输入小程序开发需求")
    user_input = st.text_area(
        "示例：生成完整登录页面，包含手机号输入框、密码输入框、红色登录按钮",
        height=150
    )
    generate_btn = st.button("🚀 一键生成小程序完整代码")

    if generate_btn:
        if not user_input.strip():
            st.warning("请填写你的小程序需求！")
        else:
            with st.spinner("Gemma4 正在生成WXML/WXSS/JS代码..."):
                prompt = f"""
你是专业微信小程序开发工程师，根据用户需求输出完整可运行代码，包含 wxml、wxss、js 三部分，代码规范完整。
用户需求：{user_input}
仅输出代码内容，不要额外文字解释。
                """
                response = client.models.generate_content(
                    model="gemma-4-26b-a4b-it",
                    contents=prompt
                )
                st.success("✅ 代码生成完毕！右侧查看完整源码")
                st.session_state["output_code"] = response.text

with col2:
    st.subheader("📱 生成后的小程序源码")
    if "output_code" in st.session_state:
        st.code(st.session_state["output_code"], language="xml")