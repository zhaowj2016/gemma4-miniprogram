# Worksheet — codex

**你的角色**：基建 Agent。负责数据语料、评测框架、prompt 模块。
**工作目录**：当前文件夹（gemma_match_codex/），分支 `agent/codex`。
**护栏（绝对不要违反）**：只在 `gemma_core/` 目录下新建文件。不要修改任何已有文件。
**完成后**：更新 `coordination/status/codex.md`，然后 `git add -A && git commit -m "codex: <描述>"`。

---

## 背景

这是一个微信小程序代码生成器（Streamlit + Gemma 4）的黑客松项目，截止 2026-06-08。
你的工作在 `gemma_core/` 子模块内，独立于主 app，不会冲突。

---

## 任务 A：扩充黄金样例语料

**目标**：在 `gemma_core/golden_examples/` 下新建场景文件夹，每个含 `index.wxml`、`index.wxss`、`index.js`。

**参考现有样例**（风格照这个写）：
- `gemma_core/golden_examples/product_detail/`
- `gemma_core/golden_examples/signup_form/`

**要覆盖的场景**（从下列挑 8-12 个，不要重复已有的）：
```
product_list（商品列表）、store_intro（门店介绍）、course_detail（课程详情）、
news_list（图文资讯列表）、news_detail（图文详情）、user_profile（个人中心）、
order_list（订单列表）、coupon_claim（优惠券领取）、job_posting（招聘岗位）、
restaurant_menu（餐饮菜单）、contact_us（联系我们）、survey_form（问卷收集）
```

**硬约束（违反即废）**：
- 禁止 `<div>` `<p>` `<span>` 等 HTML 标签，一律用 `view`/`text`
- 禁止在 `{{ }}` 里调函数，金额格式化在 JS data 里做好存成字符串
- swiper 用 `current`，不是 `current-index`
- 禁止 `wx.login` / `wx.request` / `wx.requestPayment` / `wx.getLocation` / `wx.cloud`
- 数据全用本地 mock；只用基础组件

**每写完一个，必须用校验器跑**：
```python
import sys
sys.path.insert(0, '.')  # 在 gemma_core/ 目录下运行
from validators import validate_project
files = {
    'pages/index/index.wxml': open('golden_examples/<场景>/index.wxml').read(),
    'pages/index/index.wxss': open('golden_examples/<场景>/index.wxss').read(),
    'pages/index/index.js':   open('golden_examples/<场景>/index.js').read(),
}
r = validate_project(files, full_project=False)
print('PASS' if r.ok else r.hard_errors)
```
只保留 r.ok == True 的样例，失败的修到通过或丢弃。

**同时生成两个 JSON 文件**：
- `gemma_core/corpus_index.json`：`[{"name": "product_list", "description": "...", "keywords": ["商品", "列表", "..."]}]`
- `gemma_core/benchmark_prompts.json`：`[{"scenario": "product_list", "prompt": "生成一个商品列表页，显示商品图片和价格"}]`

---

## 任务 B：完善 prompt_builder.py 和 eval_harness.py

文件已存在于 `gemma_core/`，打开看当前内容，判断是否完整，缺什么补什么。

**prompt_builder.py 必须有**：
```python
def build_prompt(user_prompt: str) -> str:
    # 从 golden_examples/ 按关键词挑 1-2 个相关样例做 few-shot
    # 拼成：约束清单 + 选中样例 + 用户需求
    ...

def build_repair_prompt(user_prompt: str, page_files: dict, errors: list) -> str:
    # 把校验错误喂回去，要求全量重出三文件
    ...
```

**eval_harness.py 必须能独立运行**：
```bash
cd gemma_core
python eval_harness.py   # 不需要真实 Gemma，用 golden_examples 做 stub
```
打印类似：
```
场景              | 首次    | hard_errors
product_list     | PASS    | 0
signup_form      | PASS    | 0
...
通过率: 100%
```

---

## 验收标准

- [ ] 至少 8 个新样例通过校验，文件在 `gemma_core/golden_examples/` 下
- [ ] `corpus_index.json` 和 `benchmark_prompts.json` 已生成
- [ ] `python gemma_core/eval_harness.py` 能跑通并打印通过率
- [ ] `gemma_core/prompt_builder.py` 的两个函数可正常 import
- [ ] `coordination/status/codex.md` 已更新，git commit 完成

---

## [总控补充 2026-06-06] Round 2 任务

**背景**：Round 1 全部完成（19 个样例 100% pass）。现在补齐提交必须有的文档。

### 任务 C：写提交用 README.md（根目录）

⚠️ 根目录已有 README.md（旧版规划文档）。**用新内容完整替换它**，符合比赛提交格式。

```markdown
# Gemma Match

用 Gemma 4 Native Function Calling 生成微信小程序源码的 AI 应用。

## 快速启动
pip install -r requirements.txt
streamlit run app.py

## 架构说明
[一段话：说明 Function Calling 如何驱动生成流程，mention TOOLS 定义、
call_gemma_with_tools、validate_project、zip 打包，自愈重试和 fallback 黄金样例机制]

## 黄金样例语料
gemma_core/golden_examples/ 包含 19 个预验证场景，全部通过 validators.py 静态校验。

## Demo
[占位：可添加截图路径]

## 项目结构
[用代码块列主要文件 + 一行说明]
```

字数 400-600，中文，简洁专业。

### 任务 D：写 gemma_core/README.md

内容：本目录用途、`python eval_harness.py` 运行说明、import 示例、19 个场景列表。
控制在 200 字以内。

### 验收（Round 2）
- [ ] 根目录 `README.md` 已替换为新内容，符合比赛格式
- [ ] `gemma_core/README.md` 已新建
- [ ] `coordination/status/codex.md` 追加 Round 2 完成项，git commit

---

## [总控补充 2026-06-06] Round 3 任务

**背景**：Round 2 已 merge，README 已是比赛格式。现在做最后的提交打磨。

### 任务 E：修复 README 中的本地路径

`README.md` 第 12 行提到 `E:\file+desktop\gemma_key.txt`，这是提交人电脑的绝对路径，公开提交后评委看到会扣印象分。

**修改该句为**：
```
运行前请配置环境变量 `GEMINI_API_KEY` 或复制 `.env.example` 为 `.env` 填入 key。
```
删掉原句中的本地路径部分，其余内容保持不变。

### 任务 F：验证 eval_harness 在 merge 后仍可用

在 `gemma_match_codex/` 目录下执行：
```bash
python gemma_core/eval_harness.py
```
确认通过率仍是 19/19。若有路径问题自行修复。将结果记录在 status 文件。

### 任务 G：完善 README Demo 占位说明

当前 Demo 章节是 `占位：可添加截图路径或演示 GIF`。将其替换为对评委有用的说明：
```markdown
## Demo

启动后访问 `http://localhost:8501`，在输入框描述目标页面（或点击示例按钮），
点击「生成代码」即可在约 5-10 秒内看到 WXML / WXSS / JS 三段代码及 ZIP 下载按钮。

生成的 ZIP 可直接导入[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)，
选择「游客模式」或将 `project.config.json` 中的 `touristappid` 替换为真实 AppID。
```

### 验收（Round 3）
- [ ] `README.md` 不含本地绝对路径
- [ ] `python gemma_core/eval_harness.py` 仍 19/19
- [ ] README Demo 章节已替换为有效说明
- [ ] `coordination/status/codex.md` 追加 Round 3 完成项，git commit
