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

---

## [总控补充 2026-06-06] Round 2 任务

**背景**：Round 1 已 merge。codex 已生成 19 个黄金样例 + corpus_index.json + 改进版 prompt_builder。
现在需要你把这些成果整合进主流程，完成最终冒烟验证。

### 任务 5：整合 gemma_core/prompt_builder

`app.py` 当前 import 的是根目录旧版 `prompt_builder.py`。需要切换到新版。

```python
# app.py 里把这行：
from prompt_builder import build_prompt, build_repair_prompt
# 改为：
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gemma_core'))
from prompt_builder import build_prompt, build_repair_prompt
```

验证：`python -c "from gemma_core.prompt_builder import build_prompt; print(build_prompt('生成一个商品详情页')[:100])"` 应输出含约束清单和 few-shot 的 prompt 片段。

### 任务 6：整合 fallback 路径

`app.py` 的 fallback 当前用的是根目录 `golden_examples.py`。
确认 `golden_examples.py` 的 `GOLDEN_DIR` 已指向 `gemma_core/golden_examples/`（已更新）。
检查 `SCENARIO_KEYWORDS` 是否涵盖 19 个场景（目前只有 13 个），把缺少的场景补全：

缺少的场景关键词（对照 `gemma_core/corpus_index.json`）：
- `portfolio`、`restaurant_menu`、`real_estate`、`service_pricing`、`job_posting`、`coupon_claim`（后几个可能已有，请自行比对后补齐）

### 任务 7：冒烟测试（代码静态验证）

由于 CLI 环境无法跑 Streamlit，改为写一个离线验证脚本：

```python
# 新建 test_smoke.py
# 1. import app 中的 generate_with_repair 函数（或等价逻辑）
# 2. mock call_gemma_with_tools → 直接返回 golden_examples/product_detail 的内容
# 3. 走完 validate → zip_exporter 全流程
# 4. 断言 zip bytes 非空 + 解压后包含 app.json、pages/index/index.wxml
# 5. python test_smoke.py 输出 PASS
```

### 验收（Round 2）
- [ ] `app.py` 使用 `gemma_core/prompt_builder.py`
- [ ] `golden_examples.py` 的 SCENARIO_KEYWORDS 已涵盖全部 19 个场景
- [ ] `python test_smoke.py` 输出 PASS
- [ ] `coordination/status/cc-worker.md` 追加 Round 2 完成项，git commit

---

## [总控补充 2026-06-06] Round 3 任务

**背景**：Round 2 已 merge。pipeline 端到端可用，test_smoke.py 3/3 PASS。现在做提交前的最后修整。

### 任务 8：修复 requirements.txt

`google-generativeai>=0.8` 在 Round 1 遗留下来，但实际已改用 `urllib.request`，该库并未安装也未 import。安装失败会让评委直接劝退。

**修改为**：
```
streamlit>=1.35
```
仅保留这一行，去掉 `google-generativeai`。

### 任务 9：新建 .env.example

在根目录新建 `.env.example`，内容：
```
# 在 Google AI Studio 获取：https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here
```
不要包含任何真实 key。

### 任务 10：Live API 多场景测试

用以下 5 个 prompt 依次调用 `call_gemma_with_tools(build_prompt(...))`，记录每个结果：
1. "生成一个活动报名页"
2. "生成一个商品详情页，包含价格和购买按钮"
3. "生成一个餐厅点餐页面"
4. "生成一个个人中心页，显示用户信息和订单入口"
5. "生成一个课程详情页"

对每个结果跑 `validate_project`，在 status 文件记录：Function Call 触发（Y/N）+ 校验结果（PASS/FAIL）+ hard_errors（如有）。

测试脚本示例：
```python
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, os.path.join('.', 'gemma_core'))
from gemma_client import call_gemma_with_tools
from prompt_builder import build_prompt
from validators import validate_project

prompts = [
    "生成一个活动报名页",
    "生成一个商品详情页，包含价格和购买按钮",
    "生成一个餐厅点餐页面",
    "生成一个个人中心页，显示用户信息和订单入口",
    "生成一个课程详情页",
]
for p in prompts:
    result = call_gemma_with_tools(build_prompt(p))
    val = validate_project({
        'pages/index/index.wxml': result.get('wxml',''),
        'pages/index/index.wxss': result.get('wxss',''),
        'pages/index/index.js':   result.get('js',''),
    }, full_project=False)
    print(f"[{'PASS' if val.ok else 'FAIL'}] {p[:20]}")
    if not val.ok:
        print(f"  Errors: {val.hard_errors[:2]}")
```

### 验收（Round 3）
- [ ] `requirements.txt` 只剩 `streamlit>=1.35`
- [ ] `.env.example` 已新建
- [ ] Live 5-prompt 测试结果已记录在 status 文件
- [ ] `coordination/status/cc-worker.md` 追加 Round 3 完成项，git commit
