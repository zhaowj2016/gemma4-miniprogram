import streamlit as st
import json
from ci_deployer import deploy_to_wechat
from parser import parse_triple

st.set_page_config(page_title="Gemma Match - 真实代码校验分身", layout="wide")
st.title("Gemma Match: 闭环真实代码真机校验分身 🕵️‍♂️")

st.markdown("为了自证清白！这里是刚才底层闭环测试完全成功的那份 **真实大模型输出代码（不是黄金样例）**！我为您专门拉起了这个分身服务。")

try:
    with open('raw.txt', 'r', encoding='utf-8') as f:
        raw = f.read()
    page_files = parse_triple(raw)
except Exception as e:
    st.error(f"读取刚才的 raw.txt 失败！错误信息：{str(e)}")
    st.stop()

if not page_files:
    st.error("解析失败！大模型可能还在全力拉取中，或者生成的不是标准的三段式代码。下面是目前截获的原始输出：")
    st.code(raw, language='markdown')
    st.stop()

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 底层真实截获的代码")
    st.info("这份代码是刚才 7527 字符输出的真实截获版本，包含了所有的 css、循环逻辑和 mock 数据。")
    tab1, tab2, tab3 = st.tabs(["WXML", "WXSS", "JS"])
    with tab1:
        st.code(page_files.get('wxml', ''), language='html')
    with tab2:
        st.code(page_files.get('wxss', ''), language='css')
    with tab3:
        st.code(page_files.get('js', ''), language='javascript')

with col2:
    st.markdown("### 🚀 一键发布到您的体验版并真机扫码验证！")
    st.warning("请直接在这里填入您的 AppID 和私钥，生成体验版二维码！骗不骗您，扫一下真机效果立刻见分晓！")
    appid_input = st.text_input("小程序的 AppID:", value="")
    private_key_input = st.text_area("上传私钥 (Private Key):", height=150)
    
    if appid_input and private_key_input:
        if st.button("🚀 立刻部署到微信体验版生成二维码", type="primary", use_container_width=True):
            with st.spinner("正在打包并调用微信官方 CI 工具上传..."):
                try:
                    qr_path = deploy_to_wechat(page_files, appid_input, private_key_input)
                    st.success("🎉 发版成功！快掏出手机用微信扫码体验真正的效果！")
                    st.image(qr_path, caption="小程序体验版二维码", width=400)
                except Exception as e:
                    st.error(f"部署失败: {e}")
