import os
# 修复文件监听、关闭遥测
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "poll"
os.environ["STREAMLIT_TELEMETRY_ENABLED"] = "false"

import streamlit as st
import requests

# 页面基础配置
st.set_page_config(page_title="Gemma4 小程序生成器", layout="wide")
st.title("🤖 本地 AI 微信小程序生成平台")

# 左右分栏布局
col1, col2 = st.columns(2)

# LMStudio本地接口地址（固定127.0.0.1:1234）
LMSTUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

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
            with st.spinner("本地大模型正在生成WXML/WXSS/JS代码..."):
                prompt = f"""
你是专业微信小程序开发工程师，根据用户需求输出完整可运行代码，包含 wxml、wxss、js 三部分，代码规范完整。
用户需求：{user_input}
仅输出代码内容，不要额外文字解释。
                """
                headers = {"Content-Type": "application/json"}
                data = {
                    "model": "gemma-4-e4b-it",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 4000
                }
                try:
                    response = requests.post(LMSTUDIO_API_URL, json=data, timeout=120)
                    response.raise_for_status()
                    result = response.json()
                    code_content = result["choices"][0]["message"]["content"].strip()
                    st.success("✅ 代码生成完毕！右侧查看完整源码")
                    st.session_state["output_code"] = code_content
                except Exception as e:
                    st.error(f"❌ 调用本地模型失败：{str(e)}")
                    st.info("请确认LMStudio软件已打开、模型加载为READY状态！")

with col2:
    st.subheader("📱 生成后的小程序源码")
    if "output_code" in st.session_state:
        st.code(st.session_state["output_code"], language="xml")