import streamlit as st
from prompt_builder import build_planning_prompt, build_learning_prompt, build_coding_prompt, build_repair_prompt, build_incremental_prompt
from gemma_client import call_gemma
from parser import parse_triple
from validators import validate_project
from zip_exporter import export_zip
from golden_examples import get_golden_example

st.set_page_config(page_title="Gemma Match Generator", layout="wide")
st.title("Gemma Match: Agentic Code Generator")
st.markdown("输入自然语言需求，不仅可以一键生成小程序代码，还可以通过**连续对话**不断微调样式和逻辑。")

st.sidebar.title("☁️ 微信云端部署配置")
st.sidebar.markdown("填写信息后即可将生成的代码一键发布为体验版。")
gemma_api_key_input = st.sidebar.text_input("Google AI Studio API Key:", value="", type="password", help="在此输入您的 API Key，优先级高于环境变量。")
st.sidebar.markdown("---")
appid_input = st.sidebar.text_input("小程序的 AppID:", value="")
private_key_input = st.sidebar.text_area("上传私钥 (Private Key):", height=150, help="在微信公众平台后台生成的私钥文件内容")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_page_files" not in st.session_state:
    st.session_state.current_page_files = None

# Show examples if no messages
if not st.session_state.messages:
    st.write("### 示例需求")
    examples = [
        "生成一个高端商品详情页，使用深色模式，添加底部购买悬浮条",
        "生成一个活动报名表单，包含炫酷的头部渐变背景",
        "生成一个带有卡片式阴影和圆角设计的个人中心"
    ]
    cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        if cols[i].button(f"示例 {i+1}"):
            st.session_state.example_clicked = ex
            st.rerun()

# Layout: Left for chat, Right for code
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💬 对话与调优")
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    user_input = st.chat_input("输入需求，或者输入指令修改当前生成的代码...")
    if "example_clicked" in st.session_state:
        user_input = st.session_state.example_clicked
        del st.session_state.example_clicked

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
                
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🔄 正在通过 Google AI Studio 调用云端 **Gemma-4-31B** 模型进行代码生成...")
                
                is_repair = False
                is_incremental = bool(st.session_state.current_page_files)
                
                if is_repair:
                    prompt = build_repair_prompt(user_input, st.session_state.current_page_files, [])
                    message_placeholder.markdown(f"🔄 正在根据验证错误自动修复代码...")
                    raw_output = call_gemma(prompt, api_key=gemma_api_key_input)
                elif is_incremental:
                    prompt = build_incremental_prompt(user_input, st.session_state.current_page_files)
                    message_placeholder.markdown(f"🔄 正在根据增量需求修改代码...")
                    raw_output = call_gemma(prompt, api_key=gemma_api_key_input)
                else:
                    message_placeholder.markdown(f"🔄 正在分析需求并进行架构推演...")
                    planning_prompt = build_planning_prompt(user_input)
                    plan_output = call_gemma(planning_prompt, api_key=gemma_api_key_input)
                    
                    if plan_output.startswith("ERROR:"):
                        message_placeholder.error(f"模型推演阶段调用失败: {plan_output}")
                        st.stop()
                        
                    # Use an expander to show the plan if people want to see it
                    with st.expander("查看模型架构推演结果", expanded=False):
                        st.write(plan_output)
                        
                    message_placeholder.markdown(f"🔄 推演完毕，正在提取黄金范式并强制模型深度学习结构...")
                    learning_prompt = build_learning_prompt(user_input)
                    learning_output = call_gemma(learning_prompt, api_key=gemma_api_key_input)
                    
                    if learning_output.startswith("ERROR:"):
                        message_placeholder.error(f"模型学习阶段调用失败: {learning_output}")
                        st.stop()
                        
                    with st.expander("查看范式学习解剖指南", expanded=False):
                        st.write(learning_output)
                        
                    message_placeholder.markdown(f"🔄 学习完毕，模型正在彻底吸收结构范式并全火力生成代码...")
                    coding_prompt = build_coding_prompt(plan_output, learning_output)
                    raw_output = call_gemma(coding_prompt, api_key=gemma_api_key_input)
                
                if raw_output.startswith("ERROR:"):
                    message_placeholder.error(f"模型调用失败: {raw_output}")
                    st.stop()
                    
                page_files = parse_triple(raw_output)
                needs_repair = False
                
                if not page_files:
                    needs_repair = True
                    errors = ["未找到 WXML, WXSS 或 JS 代码块。"]
                else:
                    val_files = {
                        "pages/index/index.wxml": page_files.get("wxml", ""),
                        "pages/index/index.wxss": page_files.get("wxss", ""),
                        "pages/index/index.js": page_files.get("js", "")
                    }
                    val_result = validate_project(val_files, full_project=False)
                    if not val_result.ok:
                        needs_repair = True
                        errors = val_result.hard_errors
                        
                if needs_repair:
                    message_placeholder.warning("初次生成存在错误，尝试自愈修复...")
                    repair_prompt = build_repair_prompt(user_input, page_files, errors)
                    raw_output = call_gemma(repair_prompt, api_key=gemma_api_key_input)
                    page_files = parse_triple(raw_output)
                    if not page_files:
                        message_placeholder.error("修复失败，已降级为黄金样例。")
                        page_files = get_golden_example(user_input)
                    else:
                        val_files = {
                            "pages/index/index.wxml": page_files.get("wxml", ""),
                            "pages/index/index.wxss": page_files.get("wxss", ""),
                            "pages/index/index.js": page_files.get("js", "")
                        }
                        val_result = validate_project(val_files, full_project=False)
                        if not val_result.ok:
                            message_placeholder.error("修复失败，已降级为黄金样例。")
                            page_files = get_golden_example(user_input)
                        else:
                            message_placeholder.success("自愈成功！")
                else:
                    message_placeholder.success("生成与校验通过！")
                    
                st.session_state.current_page_files = page_files
                st.session_state.messages.append({"role": "assistant", "content": "✅ 代码已生成/更新。您可以在右侧预览或继续提出修改意见。"})
                st.rerun()

with col2:
    st.subheader("💻 代码预览与导出")
    if st.session_state.current_page_files:
        page_files = st.session_state.current_page_files
        tab1, tab2, tab3 = st.tabs(["WXML", "WXSS", "JS"])
        with tab1:
            st.code(page_files.get('wxml', ''), language='html')
        with tab2:
            st.code(page_files.get('wxss', ''), language='css')
        with tab3:
            st.code(page_files.get('js', ''), language='javascript')
            
        zip_bytes = export_zip(page_files)
        st.download_button(
            label="📦 下载小程序 ZIP",
            data=zip_bytes,
            file_name="gemma_match_agentic.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )
        
        st.markdown("---")
        if appid_input and private_key_input:
            if st.button("🚀 部署到微信体验版", type="primary", use_container_width=True):
                with st.spinner("正在打包并调用微信官方 CI 工具上传..."):
                    from ci_deployer import deploy_to_wechat
                    try:
                        qr_path = deploy_to_wechat(page_files, appid_input, private_key_input)
                        st.success("发版成功！请用微信扫码体验：")
                        st.image(qr_path, caption="小程序体验版二维码", width=300)
                    except Exception as e:
                        st.error(f"部署失败: {e}")
        else:
            st.info("💡 如果需要一键发版到微信并直接扫码预览，请先在左侧边栏填写您的真实 AppID 和私钥。")
            
        st.markdown("---")
        if st.button("🗑️ 清空对话并重新开始", type="secondary"):
            st.session_state.messages = []
            st.session_state.current_page_files = None
            st.rerun()
    else:
        st.info("👈 请在左侧输入需求，生成的代码将在这里预览。")
