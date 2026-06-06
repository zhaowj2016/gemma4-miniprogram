# Worksheet — cc-worker（Claude Code）

**你的角色**：复杂逻辑 Agent。负责打通核心生成流程中最难的部分。
**工作目录**：当前文件夹（gemma_match_cc/），分支 `agent/cc-worker`。
**完成后**：更新 `coordination/status/cc-worker.md`，然后 `git add -A && git commit -m "cc-worker: <描述>"`。

---

## 任务 1：读清楚现状

先读以下文件，了解已有代码的状态：
- `gemma_core/BUILD_SPEC.md`（第 4 节：Function Calling 规范）
- `gemma_client.py`（当前实现，可能是三段标记版本）
- `app.py`（当前 Streamlit UI）
- `validators.py`（校验器，直接复用，不要修改）

---

## 任务 2：gemma_client.py — 实现 Native Function Calling

**目标**：让 `gemma_client.py` 通过 Google Generative AI SDK 调用 Gemma 4，
使用 Function Calling（Tool Use）拿到结构化的 `{wxml, wxss, js}`，
而不是解析三段标记字符串。

**要求**：
```python
# 必须定义 TOOLS（参考 BUILD_SPEC.md 第 4 节的结构）
# 必须实现 call_gemma_with_tools(prompt: str) -> dict
# 返回 {'wxml': str, 'wxss': str, 'js': str}
# 若 Function Call 未触发，退回三段标记解析（parser.py 已有，直接调）
```

**接入方式优先级**：
1. 优先尝试 `google-generativeai` SDK（`import google.generativeai as genai`）
2. 若本地无此库，检查 `legacy-python/` 下已有客户端代码，参考改写
3. API Key 从环境变量 `GEMINI_API_KEY` 读取；若无，退回 LM Studio 本地调用

---

## 任务 3：app.py — 集成与 UI 打磨

**目标**：让 `app.py` 使用 Task 2 的 `call_gemma_with_tools`，走完完整流程：
```
用户输入 → call_gemma_with_tools → validate_project → 展示代码 + 下载 zip
         ↘ 失败 → 自愈一次 → 仍失败 → fallback 黄金样例
```

**UI 必须有**：
- 文本输入框 + 3 个示例 prompt 按钮（活动报名 / 商品详情 / 商品列表）
- 生成按钮，点击时 spinner
- 自愈时显示 `⏳ 正在进行第 1 次自愈重试...`
- 校验通过：显示三段代码（expander）+ Zip 下载按钮
- 校验失败但用了 fallback：黄色警告条说明
- appid 提示：下载按钮旁注明替换 `touristappid`

**不要改**：`validators.py`、`scaffold.py`、`zip_exporter.py`（这些已稳定）

---

## 任务 4：冒烟测试

用以下 3 个 prompt 各跑一次，截图（或记录）结果：
1. "生成一个活动报名页"
2. "生成一个商品详情页，包含价格和购买按钮"
3. "生成一个商品列表页"

记录：是否成功、是否触发过自愈、是否 fallback、zip 是否可下载。

---

## 验收标准

- [ ] `streamlit run app.py` 能启动，无报错
- [ ] 输入 prompt → 看到三段代码 + 校验结果 + 下载按钮
- [ ] 下载 zip 解压后结构正确（含 app.json、pages/index/index.* 等）
- [ ] 至少 2 个 prompt 走 Function Calling 路径（非 fallback）
- [ ] `coordination/status/cc-worker.md` 已更新，git commit 完成
