import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "gemma_core"))

import streamlit as st
from gemma_client import call_gemma_with_tools
from prompt_builder import build_prompt, build_repair_prompt
from validators import validate_project
from zip_exporter import export_zip
from golden_examples import get_golden_example

st.set_page_config(page_title="Gemma Match", page_icon="✨", layout="centered")
st.title("✨ Gemma Match")
st.markdown(
    "用 **Gemma 4 Native Function Calling** 生成微信小程序源码，"
    "一键下载 ZIP 导入开发者工具。"
)

# --- Session state init ---
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "page_files" not in st.session_state:
    st.session_state.page_files = None
if "used_fallback" not in st.session_state:
    st.session_state.used_fallback = False

st.subheader("需求输入")

# Example prompt buttons
EXAMPLES = [
    "生成一个活动报名页",
    "生成一个商品详情页，包含价格和购买按钮",
    "生成一个商品列表页",
]
col1, col2, col3 = st.columns(3)
for col, ex in zip([col1, col2, col3], EXAMPLES):
    if col.button(ex, use_container_width=True):
        st.session_state.user_input = ex
        st.rerun()

user_input = st.text_area(
    "描述你要生成的页面",
    value=st.session_state.user_input,
    height=100,
    placeholder="例如：生成一个商品详情页，包含商品图片、价格标签和底部购买按钮",
)

generate_clicked = st.button(
    "🚀 生成代码",
    type="primary",
    disabled=not user_input.strip(),
    use_container_width=True,
)

# --- Generation flow ---
if generate_clicked and user_input.strip():
    st.session_state.user_input = user_input
    st.session_state.page_files = None
    st.session_state.used_fallback = False

    # Step 1: Initial generation (few-shot prompt from gemma_core/prompt_builder)
    with st.spinner("正在调用 Gemma 4 Native Function Calling 生成代码..."):
        try:
            result = call_gemma_with_tools(build_prompt(user_input.strip()))
        except Exception as e:
            st.error(f"生成失败：{e}")
            st.stop()

    # Step 2: Validate
    val_files = {
        "pages/index/index.wxml": result.get("wxml", ""),
        "pages/index/index.wxss": result.get("wxss", ""),
        "pages/index/index.js": result.get("js", ""),
    }
    val_result = validate_project(val_files, full_project=False)

    # Step 3: Self-heal once if validation fails
    if not val_result.ok:
        with st.spinner("⏳ 正在进行第 1 次自愈重试..."):
            try:
                repair_prompt = build_repair_prompt(
                    user_input.strip(), result, val_result.hard_errors
                )
                result = call_gemma_with_tools(repair_prompt)
                val_files = {
                    "pages/index/index.wxml": result.get("wxml", ""),
                    "pages/index/index.wxss": result.get("wxss", ""),
                    "pages/index/index.js": result.get("js", ""),
                }
                val_result = validate_project(val_files, full_project=False)
            except Exception:
                val_result.hard_errors.append("自愈调用失败")

        # Fallback to golden example if still failing
        if not val_result.ok:
            result = get_golden_example(user_input)
            st.session_state.used_fallback = True

    st.session_state.page_files = result

# --- Result display ---
if st.session_state.page_files:
    page_files = st.session_state.page_files

    st.markdown("---")

    if st.session_state.used_fallback:
        st.warning(
            "⚠️ 自动修复未能通过校验，已回退到与您需求最接近的预置黄金样例。"
            "已生成接近需求的基础版本，可直接下载使用。"
        )
    else:
        st.success("✅ 代码生成成功，已通过静态校验！")

    # Code expanders
    with st.expander("📄 WXML", expanded=True):
        st.code(page_files.get("wxml", ""), language="html")
    with st.expander("🎨 WXSS"):
        st.code(page_files.get("wxss", ""), language="css")
    with st.expander("⚡ JS"):
        st.code(page_files.get("js", ""), language="javascript")

    # Download + appid hint
    zip_bytes = export_zip(page_files)
    dl_col, hint_col = st.columns([1, 2])
    with dl_col:
        st.download_button(
            label="📦 下载小程序 ZIP",
            data=zip_bytes,
            file_name="gemma_match_miniprogram.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )
    with hint_col:
        st.caption(
            "💡 导入微信开发者工具时，AppID 请选择「游客模式」，"
            "或在 project.config.json 中将 `touristappid` 替换为真实 AppID。"
        )

    # WeChat preview QR code
    st.markdown("---")
    with st.expander("📱 一键生成微信预览二维码（需要 AppID + 私钥）"):
        st.caption(
            "填入小程序 AppID 和在微信公众平台下载的私钥内容，"
            "点击按钮即可生成可用手机扫码预览的二维码。"
        )
        wechat_appid = st.text_input("AppID", placeholder="wxxxxxxxxxxxxxxxe")
        wechat_key = st.text_area(
            "私钥内容（粘贴 private.xxx.key 文件内容）",
            height=120,
            placeholder="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----",
        )
        if st.button("🔳 生成微信预览二维码", type="primary", use_container_width=True):
            if not wechat_appid.strip():
                st.error("请填写 AppID")
            elif not wechat_key.strip():
                st.error("请粘贴私钥内容")
            else:
                with st.spinner("正在上传到微信服务器，生成预览二维码..."):
                    try:
                        from ci_deployer import deploy_to_wechat
                        qr_path = deploy_to_wechat(page_files, wechat_appid.strip(), wechat_key.strip())
                        st.success("✅ 预览二维码生成成功！用微信扫码即可在手机上预览。")
                        st.image(qr_path, width=240)
                    except Exception as e:
                        st.error(f"上传失败：{e}")

    if st.button("🔄 重新开始", type="secondary"):
        st.session_state.page_files = None
        st.session_state.used_fallback = False
        st.session_state.user_input = ""
        st.rerun()
