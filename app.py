import sys
import os
import uuid
import json
from pathlib import Path

_GEMMA_CORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemma_core")
if _GEMMA_CORE not in sys.path:
    sys.path.insert(0, _GEMMA_CORE)

import streamlit as st
import streamlit.components.v1 as components
from gemma_client import call_gemma_with_tools, call_gemma_text
from prompt_builder import (
    build_prompt,
    build_repair_prompt,
    build_enriched_prompt,
    CLARIFY_TEMPLATE,
    parse_clarify_questions,
)
try:
    from prompt_builder import build_review_prompt as _imported_review
    _HAS_REVIEW = True
except ImportError:
    _HAS_REVIEW = False

def build_review_prompt(user_prompt: str, page_files: dict) -> str:
    if _HAS_REVIEW:
        return _imported_review(user_prompt, page_files)
    # inline fallback
    wxml = page_files.get("wxml", "")
    wxss = page_files.get("wxss", "")
    js   = page_files.get("js", "")
    wl, sl, jl = len(wxml.splitlines()), len(wxss.splitlines()), len(js.splitlines())
    code = json.dumps({"wxml": wxml, "wxss": wxss, "js": js}, ensure_ascii=False, indent=2)
    return (
        "你是微信小程序代码 QA 工程师。对以下代码做自检优化，通过 create_miniprogram_page 工具返回最终版本。\n"
        "自检清单：1.代码量<900行→扩充数据和区块 2.数组条目<4→补至5-6条 3.缺底部操作栏→补充 "
        "4.Unsplash ID含大写→改小写 5.卡片无阴影/圆角→补充\n"
        "即使无改动也必须调用 create_miniprogram_page 工具返回三文件。\n\n"
        f"用户需求：{user_prompt}\n"
        f"代码量：WXML {wl}行 WXSS {sl}行 JS {jl}行 共{wl+sl+jl}行\n\n"
        f"待审核代码：\n{code}\n"
    )
from validators import validate_project
from zip_exporter import export_zip
from golden_examples import get_golden_example
from render_wxml import render_phone_html
from scaffold import APP_WXSS

st.set_page_config(page_title="Gemma Match", page_icon="✨", layout="wide")

# ── Share link helpers ────────────────────────────────────────────────────────
_SHARE_DIR = Path(__file__).parent / "demo_cache" / "shares"
_SHARE_DIR.mkdir(parents=True, exist_ok=True)

def _save_share(page_files: dict, title: str = "") -> str:
    share_id = uuid.uuid4().hex[:8]
    (_SHARE_DIR / f"{share_id}.json").write_text(
        json.dumps({"files": page_files, "title": title}, ensure_ascii=False),
        encoding="utf-8",
    )
    return share_id

def _load_share(share_id: str) -> dict | None:
    p = _SHARE_DIR / f"{share_id}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None

# ── Handle ?share=<id> preview-only mode ─────────────────────────────────────
_params = st.query_params
if "share" in _params:
    _sid = _params["share"]
    _data = _load_share(_sid)
    if _data:
        pf = _data["files"]
        _title = _data.get("title", "Gemma Match 预览")
        st.title(f"📱 {_title}")
        st.caption("由 **Gemma Match** 生成 · Powered by Gemma 4 Native Function Calling")
        _left, _right = st.columns([5, 7], gap="large")
        with _left:
            try:
                from scaffold import APP_WXSS as _aws
                components.html(render_phone_html(pf["wxml"], pf["wxss"], pf["js"], _aws), height=720, scrolling=False)
            except Exception as _e:
                st.error(f"预览渲染失败：{_e}")
        with _right:
            _tabs = st.tabs(["WXML", "WXSS", "JS"])
            with _tabs[0]: st.code(pf.get("wxml",""), language="html", line_numbers=True)
            with _tabs[1]: st.code(pf.get("wxss",""), language="css", line_numbers=True)
            with _tabs[2]: st.code(pf.get("js",""), language="javascript", line_numbers=True)
            _zip = export_zip(pf)
            st.download_button("📦 下载 ZIP", _zip, "gemma_match_miniprogram.zip", "application/zip", type="primary", use_container_width=True)
        st.stop()
    else:
        st.error(f"分享链接已失效或不存在（ID: {_sid}）")
        st.stop()

# ── session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("stage", "input"),          # input | clarifying | done
    ("original_input", ""),
    ("clarify_questions", []),
    ("image_list", None),        # list of (bytes, mime_type), replaces single image_bytes
    ("page_files", None),
    ("used_fallback", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── header ────────────────────────────────────────────────────────────────────
st.title("✨ Gemma Match")
st.markdown(
    "**Gemma 4 Native Function Calling** 驱动的微信小程序代码生成器 · "
    "支持多模态图片输入 · 智能需求澄清 · 一键下载 ZIP"
)
st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# STAGE: input
# ═════════════════════════════════════════════════════════════════════════════
if st.session_state.stage == "input":

    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader("📝 描述你的需求")

        EXAMPLES = [
            "生成一个活动报名页",
            "生成一个商品详情页，包含价格和购买按钮",
            "生成一个餐厅点餐页，带菜品列表和购物车",
        ]
        c1, c2, c3 = st.columns(3)
        for col, ex in zip([c1, c2, c3], EXAMPLES):
            if col.button(ex, use_container_width=True, key=f"ex_{ex}"):
                st.session_state.original_input = ex
                st.rerun()

        user_input = st.text_area(
            "用自然语言描述目标页面",
            value=st.session_state.original_input,
            height=120,
            placeholder="例如：生成一个商品详情页，包含商品轮播图、规格选择和底部购买按钮",
            key="input_text",
        )

    with right:
        st.subheader("🖼️ 上传参考图片（可选）")
        st.caption("上传设计稿、产品图、竞品截图等，Gemma 4 多模态自动决策用途")

        MAX_IMGS = 20
        MAX_MB = 8.0
        uploaded_files = st.file_uploader(
            f"支持 JPG / PNG / WebP / GIF / BMP（最多 {MAX_IMGS} 张，每张 ≤ {int(MAX_MB)} MB）",
            type=["jpg", "jpeg", "png", "webp", "gif", "bmp"],
            accept_multiple_files=True,
            key="multi_img_upload",
            label_visibility="collapsed",
        )

        if uploaded_files:
            valid_imgs = []
            for uf in uploaded_files[:MAX_IMGS]:
                raw = uf.read()
                size_mb = len(raw) / 1024 / 1024
                if size_mb > MAX_MB:
                    st.warning(f"⚠️ {uf.name} ({size_mb:.1f} MB) 超过 {int(MAX_MB)} MB，已跳过")
                else:
                    valid_imgs.append((raw, uf.type or "image/jpeg", uf.name, size_mb))

            if valid_imgs:
                st.session_state.image_list = [(d, m) for d, m, _, _ in valid_imgs]
                # Preview thumbnails (up to 4 in a row)
                cols = st.columns(min(len(valid_imgs), 4))
                for col, (raw, mime, name, size_mb) in zip(cols, valid_imgs[:4]):
                    col.image(raw, caption=f"{name[:12]}\n{size_mb:.1f} MB", use_container_width=True)
                if len(valid_imgs) > 4:
                    st.caption(f"+ {len(valid_imgs)-4} 张（共 {len(valid_imgs)} 张）")
                st.caption(f"✅ 已加载 {len(valid_imgs)} 张参考图片，Gemma 4 将分析每张图片并自主决定使用位置")
        elif st.session_state.get("image_list"):
            n = len(st.session_state.image_list)
            st.info(f"已有 {n} 张参考图片（本次已清除，上方重新上传）")
            st.session_state.image_list = None

    st.divider()
    btn_col1, btn_col2, _ = st.columns([1, 1, 2])

    analyze_clicked = btn_col1.button(
        "🔍 AI 需求分析",
        type="primary",
        disabled=not (user_input or "").strip(),
        use_container_width=True,
        help="Gemma 4 先理解需求，提几个关键问题，帮你生成更精准的代码",
    )
    quick_clicked = btn_col2.button(
        "⚡ 快速生成",
        disabled=not (user_input or "").strip(),
        use_container_width=True,
        help="跳过分析，直接生成",
    )

    if analyze_clicked and (user_input or "").strip():
        st.session_state.original_input = user_input.strip()
        with st.spinner("Gemma 4 正在理解您的需求..."):
            try:
                clarify_prompt = CLARIFY_TEMPLATE.format(user_input=user_input.strip())
                img_list = st.session_state.get("image_list") or []
                # Use only the first image for the quick clarification call (speed)
                first_img = img_list[0] if img_list else None
                raw = call_gemma_text(
                    clarify_prompt,
                    image_data=first_img[0] if first_img else None,
                    image_mime=first_img[1] if first_img else "image/jpeg",
                )
                questions = parse_clarify_questions(raw)
                st.session_state.clarify_questions = questions
                st.session_state["_clarify_ai_success"] = True
            except Exception as e:
                from prompt_builder import _DEFAULT_CLARIFY_QUESTIONS
                st.session_state.clarify_questions = [q.copy() for q in _DEFAULT_CLARIFY_QUESTIONS]
                st.session_state["_clarify_ai_success"] = False
                st.session_state["_clarify_err"] = str(e)
        st.session_state.stage = "clarifying"
        st.rerun()

    if quick_clicked and (user_input or "").strip():
        st.session_state.original_input = user_input.strip()
        st.session_state.clarify_questions = []
        st.session_state.stage = "generating"
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# STAGE: clarifying
# ═════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "clarifying":

    if not st.session_state.get("_clarify_ai_success", True):
        st.warning(
            f"⚠️ AI 分析暂时不可用（{st.session_state.get('_clarify_err', '')}），"
            "以下为通用参考问题，建议直接点「快速生成」。"
        )

    st.subheader("🤔 Gemma 4 需求分析")
    st.caption(f"基于「**{st.session_state.original_input}**」，选择最符合你想法的选项，Gemma 会根据你的选择生成更精准的代码")

    answers = []
    LABELS = {"a": "A", "b": "B", "c": "C"}

    for i, q_data in enumerate(st.session_state.clarify_questions):
        st.markdown(f"**Q{i+1}. {q_data['q']}**")

        options = [
            f"A    {q_data['a']}",
            f"B    {q_data['b']}",
            f"C    {q_data['c']}",
            "D    其他（自定义输入）",
        ]
        choice = st.radio(
            label=f"q{i}",
            options=options,
            key=f"q{i}_radio",
            horizontal=True,
            label_visibility="collapsed",
            index=None,
        )

        answer_text = ""
        if choice is not None:
            if choice.startswith("A"):
                answer_text = q_data["a"]
            elif choice.startswith("B"):
                answer_text = q_data["b"]
            elif choice.startswith("C"):
                answer_text = q_data["c"]
            elif choice.startswith("D"):
                answer_text = st.text_input(
                    "请输入自定义内容",
                    key=f"q{i}_custom",
                    placeholder="描述你的具体要求...",
                    label_visibility="collapsed",
                )

        answers.append((q_data["q"], answer_text))

    img_list = st.session_state.get("image_list") or []
    if img_list:
        st.caption(f"📎 {len(img_list)} 张参考图片已附加")
        cols = st.columns(min(len(img_list), 5))
        for col, (raw, _) in zip(cols, img_list[:5]):
            col.image(raw, use_container_width=True)

    st.divider()
    g_col, b_col, _ = st.columns([1, 1, 2])

    answered_count = sum(1 for _, a in answers if a)
    generate_clicked = g_col.button(
        f"🚀 生成代码{f'（已选 {answered_count}/{len(answers)} 题）' if answered_count else ''}",
        type="primary",
        use_container_width=True,
    )
    back_clicked = b_col.button("← 返回修改", use_container_width=True)

    if back_clicked:
        st.session_state.stage = "input"
        st.rerun()

    if generate_clicked:
        st.session_state.stage = "generating"
        st.session_state["_qa_pairs"] = answers
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# STAGE: generating (runs immediately, then transitions to done)
# ═════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "generating":

    qa_pairs  = st.session_state.get("_qa_pairs", [])
    img_list  = st.session_state.get("image_list") or []
    img_count = len(img_list)

    if qa_pairs:
        prompt = build_enriched_prompt(
            st.session_state.original_input,
            qa_pairs,
            image_count=img_count,
        )
    else:
        prompt = build_prompt(st.session_state.original_input)
        if img_count == 1:
            prompt += "\n\n【多模态输入】用户上传了 1 张参考图片，请分析图片内容、配色和风格，在生成的代码中自然融入。"
        elif img_count > 1:
            prompt += f"\n\n【多模态输入】用户上传了 {img_count} 张参考图片，请逐一分析并自主决定每张的用途和放置位置。"

    result = None
    with st.status("🧠 Gemma 4 工作中...", expanded=True) as gen_status:
        # Step 1: Generate
        st.write("📡 正在发送请求到 **gemma-4-31b-it**（预计 15-30 秒）...")
        if img_count:
            st.write(f"🖼️ 已附加 {img_count} 张参考图片（多模态输入）")
        try:
            result = call_gemma_with_tools(
                prompt,
                image_list=img_list if img_list else None,
            )
            wxml_lines = len(result.get("wxml", "").splitlines())
            wxss_lines = len(result.get("wxss", "").splitlines())
            js_lines   = len(result.get("js",   "").splitlines())
            st.write(
                f"✅ 模型返回成功 · WXML {wxml_lines}行 · WXSS {wxss_lines}行 · JS {js_lines}行"
            )
        except Exception as e:
            st.write(f"❌ 调用失败：{e}")
            gen_status.update(label="❌ 生成失败", state="error")
            if st.button("重新开始"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()
            st.stop()

        # Step 2: Validate
        st.write("🔍 正在校验代码质量...")
        val_files = {
            "pages/index/index.wxml": result.get("wxml", ""),
            "pages/index/index.wxss": result.get("wxss", ""),
            "pages/index/index.js":   result.get("js", ""),
        }
        val_result = validate_project(val_files, full_project=False)

        if val_result.ok:
            st.write("✅ 代码通过静态校验")
        else:
            errs = val_result.hard_errors
            st.write(f"⚠️ 发现 {len(errs)} 个问题：{' · '.join(errs[:2])}{'...' if len(errs)>2 else ''}")
            st.write("🔧 启动自愈，重新调用模型修复...")

            try:
                repair_prompt = build_repair_prompt(
                    st.session_state.original_input, result, errs
                )
                result = call_gemma_with_tools(repair_prompt)
                val_files = {
                    "pages/index/index.wxml": result.get("wxml", ""),
                    "pages/index/index.wxss": result.get("wxss", ""),
                    "pages/index/index.js":   result.get("js", ""),
                }
                val_result = validate_project(val_files, full_project=False)
                if val_result.ok:
                    st.write("✅ 自愈成功，代码通过校验")
                else:
                    st.write("⚠️ 自愈后仍有问题，回退到最相近的黄金样例")
                    result = get_golden_example(st.session_state.original_input)
                    st.session_state.used_fallback = True
            except Exception:
                st.write("⚠️ 自愈调用失败，回退到黄金样例")
                result = get_golden_example(st.session_state.original_input)
                st.session_state.used_fallback = True

        # Step 3: Self-review (second 31b pass — quality polish)
        if not st.session_state.used_fallback:
            st.write("🔎 31B 自检优化中（第二轮）...")
            try:
                review_prompt = build_review_prompt(st.session_state.original_input, result)
                reviewed = call_gemma_with_tools(review_prompt)
                old_total = sum(len(result.get(k, "").splitlines()) for k in ("wxml", "wxss", "js"))
                new_total = sum(len(reviewed.get(k, "").splitlines()) for k in ("wxml", "wxss", "js"))
                if new_total >= old_total - 30:
                    delta = new_total - old_total
                    delta_str = f"+{delta}" if delta >= 0 else str(delta)
                    result = reviewed
                    st.write(f"✨ 自检完成 · 代码量 {old_total} → {new_total} 行（{delta_str}）")
                else:
                    st.write(f"⚠️ 自检返回代码偏短（{new_total}行 vs 原{old_total}行），保留原版本")
            except Exception as e:
                st.write(f"⚠️ 自检跳过：{e}")

        gen_status.update(label="✅ 生成完成！", state="complete")

    st.session_state.page_files = result
    st.session_state.stage = "done"
    st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# STAGE: done — show results
# ═════════════════════════════════════════════════════════════════════════════
elif st.session_state.stage == "done" and st.session_state.page_files:

    page_files = st.session_state.page_files
    wxml = page_files.get("wxml", "")
    wxss = page_files.get("wxss", "")
    js   = page_files.get("js", "")

    if st.session_state.used_fallback:
        st.warning("⚠️ 自动修复未能通过校验，已回退到最接近需求的预置黄金样例。")
    else:
        st.success("✅ 代码生成成功，已通过静态校验！")

    preview_col, code_col = st.columns([5, 7], gap="large")

    with preview_col:
        st.markdown("**📱 手机预览**")
        try:
            phone_html = render_phone_html(
                wxml, wxss, js,
                app_wxss=APP_WXSS,
                user_images=st.session_state.get("image_list"),
            )
            components.html(phone_html, height=720, scrolling=False)
        except Exception as e:
            st.error(f"预览渲染失败：{e}")

    with code_col:
        st.markdown(f"**生成代码 — 「{st.session_state.original_input[:30]}」**")
        code_tabs = st.tabs(["📄 WXML", "🎨 WXSS", "⚡ JS"])
        with code_tabs[0]:
            st.code(wxml, language="html", line_numbers=True)
        with code_tabs[1]:
            st.code(wxss, language="css", line_numbers=True)
        with code_tabs[2]:
            st.code(js, language="javascript", line_numbers=True)

        wxml_l = len(wxml.splitlines())
        wxss_l = len(wxss.splitlines())
        js_l   = len(js.splitlines())
        st.caption(
            f"代码量：WXML {wxml_l} 行 · WXSS {wxss_l} 行 · JS {js_l} 行 "
            f"· 共 {wxml_l+wxss_l+js_l} 行"
        )

        zip_bytes = export_zip(page_files)
        dl_col, share_col, deploy_col = st.columns(3)
        with dl_col:
            st.download_button(
                label="📦 下载小程序 ZIP",
                data=zip_bytes,
                file_name="gemma_match_miniprogram.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True,
            )
        with share_col:
            if st.button("🔗 生成分享链接", use_container_width=True, help="生成可直接访问的预览页链接"):
                _sid = _save_share(page_files, title=st.session_state.original_input[:30])
                st.session_state["_share_id"] = _sid
        with deploy_col:
            if st.button("📱 上传到微信预览", use_container_width=True, help="需要 AppID + 私钥"):
                st.session_state["_show_deploy"] = True

        if st.session_state.get("_share_id"):
            _sid = st.session_state["_share_id"]
            # Try to get the actual URL from Streamlit's external URL
            _base = st.get_option("browser.serverAddress") or "localhost"
            _port = st.get_option("browser.serverPort") or 8501
            _share_url = f"http://{_base}:{_port}/?share={_sid}"
            st.success("✅ 分享链接已生成！任何人打开下方链接即可查看手机预览效果：")
            st.code(_share_url, language="text")

        st.caption(
            "💡 导入微信开发者工具时选择「游客模式」，"
            "或将 project.config.json 中的 `touristappid` 替换为真实 AppID。"
        )

    st.divider()

    # Debug log viewer
    with st.expander("🔍 调试日志（API 调用全过程）", expanded=False):
        _log_path = Path(__file__).parent / "demo_cache" / "gemma.log"
        if _log_path.exists():
            _lines = _log_path.read_text(encoding="utf-8").strip().split("\n")
            st.code("\n".join(_lines[-80:]), language="text")
            st.caption(f"日志路径：{_log_path}  共 {len(_lines)} 行，显示最近 80 行")
        else:
            st.caption("尚无日志文件，请先生成一次代码。")

    # WeChat CI deploy — shown when user clicks the button above, or always visible via expander
    if st.session_state.get("_show_deploy"):
        st.subheader("📱 上传到微信预览")
        wechat_appid = st.text_input("AppID", placeholder="wxxxxxxxxxxxxxxxe", key="deploy_appid")
        wechat_key = st.text_area(
            "私钥内容（粘贴 private.xxx.key 文件内容）",
            height=120,
            placeholder="-----BEGIN RSA PRIVATE KEY-----\n...",
            key="deploy_key",
        )
        if st.button("🔳 生成微信预览二维码", type="primary", use_container_width=True):
            if not wechat_appid.strip():
                st.error("请填写 AppID")
            elif not wechat_key.strip():
                st.error("请粘贴私钥内容")
            else:
                with st.spinner("正在上传到微信服务器..."):
                    try:
                        from ci_deployer import deploy_to_wechat
                        qr_path = deploy_to_wechat(page_files, wechat_appid.strip(), wechat_key.strip())
                        st.success("✅ 预览二维码生成成功！用微信扫码即可在手机上预览。")
                        st.image(qr_path, width=240)
                    except Exception as e:
                        st.error(f"上传失败：{e}")

    if st.button("🔄 重新开始", type="secondary"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
