# Gemma Match — 构建任务规范 (给编码 Agent 执行)

> 读完这份再动手。这不是理念文档，是一份要逐条落实的工程任务单。
> 上一次失败的根因：agent 把这份项目误解成"手搓一个小程序"。**你要建的是
> 一个 Streamlit 生成器应用，不是一个小程序。** 见第 0 节。

---

## 0. 你要交付的是什么（最重要）

- ❌ 不是：一个微信小程序（那只是本应用的"输出产物"之一）
- ✅ 是：一个 **Python + Streamlit Web 应用**，用户在浏览器输入自然语言，
  应用调用 **Gemma 4** 生成小程序页面代码，经静态校验后打包成 zip 供下载

**验收标准**：跑起来后用户在浏览器里看到输入框，输入"生成一个商品详情页"，点生成，
页面出现 WXML/WXSS/JS 代码 + 校验结果 + Zip 下载按钮。
如果你产出的是一堆 .wxml/.wxss 文件，就是又做错了。

---

## 1. 技术栈（固定）

- Python 3.10+
- Streamlit（界面，不要用 Flask/React 另起）
- 模型：**Gemma 4**（比赛强制要求，运行时模型必须是 Gemma 4）
- Gemma 调用：Google AI Studio API 或本地 Ollama，取决于现有配置
- 标准库：`json`, `re`, `zipfile`, `pathlib`
- **直接复用 `validators.py`，不要重写**

---

## 2. 文件结构

```
app.py                # Streamlit 入口与界面
gemma_client.py       # 封装 Gemma 4 调用（含 Function Calling，见第 4 节）
prompt_builder.py     # 系统 prompt + few-shot
scaffold.py           # 固定脚手架文件内容（见第 5 节）
validators.py         # 【已给你，直接用】静态校验器
zip_exporter.py       # 合并脚手架 + 页面文件 → zip bytes
golden_examples.py    # 内联两个黄金样例（few-shot + fallback）
requirements.txt      # 比赛提交必须有
README.md             # 比赛提交必须有（含一键启动，见第 7 节）
```

---

## 3. 主流程

```
用户输入 prompt
  → build_prompt()
  → call_gemma_with_tools()          # 用 Function Calling，见第 4 节
  → 拿到 {'wxml':..,'wxss':..,'js':..}
  → validate_project(page_files, full_project=False)
        PASS → export_zip → 展示代码 + 下载按钮
        FAIL → build_repair_prompt(把 errors 喂回去) → 再 call 一次
        第 2 次仍 FAIL → 关键词选黄金样例 fallback，提示"已生成接近需求的基础版本"
```

自愈最多 **1 次**。不做 patch，一律全量重生成。

---

## 4. 输出协议：Native Function Calling（核心，评分 25% 权重在这里）

⚠️ 比赛评分明确要求"深度利用 Gemma 4 原生函数调用，而非简单 Prompt 工程"。
用三段标记或 JSON manifest 解析在评委眼里是"简单 Prompt 工程"，拿不到技术分。

**正确做法：定义一个工具，让 Gemma 4 通过 Function Calling 返回代码。**

```python
# gemma_client.py

TOOLS = [
    {
        "name": "create_miniprogram_page",
        "description": "生成微信小程序 pages/index/index 页面的三个核心文件",
        "parameters": {
            "type": "object",
            "properties": {
                "wxml": {
                    "type": "string",
                    "description": "页面 WXML 结构代码，只使用合法小程序组件"
                },
                "wxss": {
                    "type": "string",
                    "description": "页面 WXSS 样式代码"
                },
                "js": {
                    "type": "string",
                    "description": "页面 JS 逻辑代码，必须包含 Page({}) 构造，数据用本地 mock"
                }
            },
            "required": ["wxml", "wxss", "js"]
        }
    }
]

def call_gemma_with_tools(prompt: str) -> dict:
    """
    调用 Gemma 4，通过 Function Calling 拿到三个文件内容。
    返回 {'wxml': str, 'wxss': str, 'js': str}，或抛出异常。

    注意：不同调用方式（Google AI Studio / Ollama / HuggingFace）的 tool calling
    API 格式不同，按你的实际接入方式适配。核心逻辑是：
      1. 把 TOOLS 传给模型
      2. 从响应中找 tool_use / function_call 块
      3. 提取 arguments（已是结构化 dict，无需手动解析）
    """
    # ---- 用 Google Generative AI SDK 的示例（根据实际接入方式替换）----
    # response = model.generate_content(prompt, tools=TOOLS)
    # for part in response.candidates[0].content.parts:
    #     if part.function_call:
    #         return dict(part.function_call.args)
    # raise ValueError("Gemma 未触发 Function Call，检查 prompt 或模型版本")
    pass
```

**优势**：args 已是结构化 dict，无需解析三段标记或转义 JSON，直接取 `wxml`/`wxss`/`js` 字段。

如果所用的 Gemma 版本/接入方式暂不支持 Function Calling（如某些本地量化版本），
则退回三段标记格式（见附录），但在 README 和技术报告里仍要说明你的设计意图是 Function Calling。

---

## 5. 固定脚手架（scaffold.py）

模型**只**生成 pages/index/index 的 wxml/wxss/js 三个文件。
下面 5 个文件由 zip_exporter 固定写入，不让模型碰：

**app.json**
```json
{"pages":["pages/index/index"],"window":{"navigationBarTitleText":"Gemma Match","navigationBarBackgroundColor":"#ffffff","navigationBarTextStyle":"black"},"style":"v2","sitemapLocation":"sitemap.json"}
```
**app.js**: `App({})`
**app.wxss**: `page { background:#f7f8fa; font-size:28rpx; color:#333; }`
**pages/index/index.json**: `{"navigationBarTitleText":"Gemma Match"}`
**project.config.json**: appid 必须用 `"touristappid"`（不要用 YOUR_APPID！）

```json
{"appid":"touristappid","projectname":"gemma-match-generated","compileType":"miniprogram","miniprogramRoot":"./","setting":{"es6":true,"postcss":true,"minified":false,"urlCheck":false}}
```

---

## 6. 给 Gemma 的系统 Prompt 要点

- 你是微信小程序页面生成器，通过 `create_miniprogram_page` 工具返回页面代码
- 只能用：view, text, image, button, input, textarea, form, scroll-view, swiper, swiper-item, block
- 数据全部用本地 mock 写在 JS data 里
- **严禁（上一版踩过的坑，逐条列出）**：
  - 禁止 `<div>` `<p>` `<span>` 等 HTML 标签，一律用 view/text
  - 禁止 `{{price.toFixed(2)}}` 这类 binding 里调函数，金额格式化在 JS 做好存为字符串
  - swiper 用 `current`，不是 `current-index`
  - 禁止 wx.login / wx.request / wx.requestPayment / wx.getLocation / wx.cloud
- 附上黄金样例做 few-shot（golden_examples.py 里有两个）

---

## 7. 比赛提交必须有的文件

### requirements.txt（示例）
```
streamlit>=1.35
google-generativeai>=0.8   # 或对应的调用库
```

### README.md 必须包含
```markdown
# Gemma Match

用 Gemma 4 Native Function Calling 生成微信小程序源码的 AI 应用。

## 快速启动
pip install -r requirements.txt
streamlit run app.py

## 架构说明
[一段话说明 Function Calling 如何驱动生成流程]

## Demo
[截图或 GIF]
```

---

## 8. fallback（golden_examples.py）

- 含"报名/表单/预约" → signup_form
- 含"商品/价格/购买/详情" → product_detail
- 其他 → product_detail（默认）

两个样例三件套在 `golden_examples/` 目录里，已通过静态校验器，直接内联进来。

---

## 9. 明确不做

Docker / 无头编译 / miniprogram-ci / 多页面路由 / 登录支付 /
真实 wx.request / 云开发 / 地图 / canvas / 第三方 npm / patch 引擎 /
向量检索 / WYSIWYG / 体验版二维码。

---

## 10. 提交步骤（代码写完后，队长操作）

1. Fork https://github.com/gdgshanghai/Gemma4-Hackathon-ShangHai
2. 在 `/submissions/2026/A/gemma-match/` 目录下放代码（含 README.md + requirements.txt）
3. 向官方仓库发 Pull Request，标题：`[赛道A] Gemma Match - [队伍名]`
4. PR 合并后，队长去 https://hackathon.googdg.cn/onsite-submit 填材料表单
5. **截止：2026 年 6 月 8 日 23:59**（评审以截止前最后一次 commit 为准）

---

## 11. 验收

1. `streamlit run app.py` 能启动，有输入框 + 示例按钮 + 生成按钮
2. 输入 prompt → 看到三段代码 + 校验结果 + Zip 下载
3. 校验失败 → 自愈一次 → 仍失败 fallback，不崩溃
4. 下载 zip 解压，`python validators.py <解压目录>` 输出 PASS
5. 至少 2 个生成的 zip 手动导入微信开发者工具确认干净（人工）

---

## 附录：三段标记兜底协议（Function Calling 不可用时）

```
===WXML===
<view>...</view>
===WXSS===
.page{...}
===JS===
Page({...})
```

按三个标记 split，strip 首尾空行，路径写死为 pages/index/index.*。

