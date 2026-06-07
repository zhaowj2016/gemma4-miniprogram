# Gemma Match

**GDG Shanghai Gemma 4 Hackathon · Track A — AI Agent**

用 **Gemma 4 Native Function Calling** 生成微信小程序源码的 AI Agent。商家或个人用一句自然语言描述需求（"做一个咖啡店点单页，要有商品列表和购物车"），Agent 在数十秒内完成需求理解 → 代码生成 → 自我审查三步推理，直接产出可导入微信开发者工具的完整工程 ZIP，并在浏览器内同步渲染可交互的手机预览。

---

## 这个项目想解决什么问题

小程序原型开发对非技术背景的小商家、个体创作者而言门槛不低：外包一个最简单的点单/预约类小程序 MVP，市场报价普遍在数千到上万元、周期数周；自己学着做，则要跨过"页面结构 → 样式 → 交互逻辑 → 工程文件组织"这一整条陡峭曲线。

Gemma Match 把这条链路压缩成"一句话输入 → 几十秒等待 → 拿到可直接用的工程文件"。它验证的不是"大模型能不能写代码"（这早已是常识），而是**"能不能把代码生成可靠到普通人不需要再读代码就敢用"**——这正是我们投入精力最多的地方：让 Agent 自己审查、自己修复、自己规避"看起来对、实际跑不起来"的坑。

---

## 核心亮点

| 亮点 | 说明 | 可验证依据 |
|---|---|---|
| **三步自主 Agent Pipeline** | 需求澄清 → 代码生成 → 自审优化，由三次独立的 Gemma 4 推理串联完成，而非一次性生成 | [app.py:215](app.py#L215)、[app.py:409-410](app.py#L409-L410) |
| **Native Function Calling，非文本解析** | 模型必须通过 `create_miniprogram_page` 工具结构化输出 wxml/wxss/js 三件套，触发率 100%（5/5 实测） | [gemma_client.py](gemma_client.py)、`tests/test_live.py` |
| **静态门禁 + 自愈重试** | 校验失败时把具体错误反馈给模型，让模型理解并修正自己的输出，而非简单重跑 | [validators.py](validators.py)、[app.py](app.py) |
| **多模态输入** | 支持上传参考图片，模型结合图片内容生成匹配风格的页面 | [app.py](app.py) `image_list` 全链路接入 |
| **浏览器内完整运行时模拟** | 自研 WXML→HTML 渲染器 + WeChat JS Shim，无需真机即可交互预览生成结果 | [render_wxml.py](render_wxml.py) |
| **23 个验证语料 + 知识锚定层** | 不依赖模型自由发挥外部资源引用，把"事实性查证"从生成过程中剥离，交给确定性校验 | 见下方"技术深度"一节 |

---

## 一键启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key（选其一）
cp .env.example .env          # 填入 GEMINI_API_KEY
# 或：export GEMINI_API_KEY=your_key_here

# 3. 启动主应用（代码生成器）
streamlit run app.py --server.port 8501

# 4. 可选：启动效果展示页
streamlit run showcase.py --server.port 8502
```

访问 `http://localhost:8501` 即可使用代码生成器；访问 `http://localhost:8502` 查看预生成场景展示。

### Docker 快速体验

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV GEMINI_API_KEY=your_key_here
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

```bash
docker build -t gemma-match .
docker run -p 8501:8501 -e GEMINI_API_KEY=your_key gemma-match
```

---

## Agent 架构（Track A 核心）

Gemma Match 实现了一个三步自主推理 Pipeline，每步由独立的 Gemma 4 模型实例完成：

```
用户输入（含可选参考图片）
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1 · 需求澄清  (gemma-4-27b-it)                        │
│  分析输入，提取业务场景、功能要点、UI 风格，补全模糊需求    │
└─────────────────┬───────────────────────────────────────────┘
                  │ 结构化 prompt
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2 · 代码生成  (gemma-4-31b-it · Native Function Call) │
│  调用 create_miniprogram_page(wxml, wxss, js) 工具           │
│  模型必须通过 Function Calling 返回结构化三件套              │
└─────────────────┬───────────────────────────────────────────┘
                  │ {wxml, wxss, js}
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3 · 自审优化  (gemma-4-31b-it)                        │
│  审阅生成结果，检查绑定完整性、内容真实感，输出最终版本     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────┐
│  静态门禁校验 (validators.py)                        │
│  · 拦截 HTML 标签混入 WXML                           │
│  · 拦截危险 wx.* API 调用                            │
│  · 检查 WXML 绑定函数 / JS Page() 完整性             │
│  校验失败 → 自愈重试（把 hard errors 反馈给模型）    │
│  仍失败 → golden_examples 语义检索 fallback          │
└──────────────────────────────────────────────────────┘
                  │
                  ▼
          ZIP 下载 + 交互式手机预览
```

### 为什么坚持 Native Function Calling，而不是更省事的文本解析

让大模型直接输出一段 JSON 或用约定好的标记包裹代码，再用正则/字符串匹配去解析——这是最常见、最省事的做法，但也是评委最容易识别出"简单 Prompt 工程"的地方：模型可能在前面多说一句话、漏加一个引号、用全角符号，解析就会脆性崩溃。

Gemma Match 选择把结构化输出的责任交还给模型本身——通过 Gemma 4 官方的 `functionDeclarations` 协议强制约束输出形状：

```python
TOOLS = [{
    "functionDeclarations": [{
        "name": "create_miniprogram_page",
        "description": "生成微信小程序页面三件套",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "wxml": {"type": "STRING"},
                "wxss": {"type": "STRING"},
                "js":   {"type": "STRING"}
            },
            "required": ["wxml", "wxss", "js"]
        }
    }]
}]

# toolConfig 强制模型必须调用工具
tool_config = {"functionCallingConfig": {"mode": "AUTO"}}
```

这不只是"调用方式"的差异，而是**让 Gemma 4 的结构化推理能力直接成为系统可靠性的来源**——触发率 100%（5/5 live 测试通过，见 `tests/test_live.py`），且即便模型某次未触发工具调用，系统仍保留三重 markers 文本解析作为兜底（[gemma_client.py](gemma_client.py)），双保险而不是单点依赖。

---

## 技术深度：一次完整的 grounding 问题排查

工程中最容易被低估的，往往不是"模型能不能生成"，而是"生成的内容是否经得起放到真实环境里跑"。我们在排查"图片在预览里正常、导入真机却加载失败"这个问题时，顺藤摸瓜揭开了一个所有 LLM 共性的短板——**模型对"格式长什么样"的记忆，远强于对"某个具体外部资源是否真实存在"的记忆**：模型生成的 Unsplash 图片 ID 格式完全正确、肉眼难辨，但对应的图片在服务器上根本不存在。

完整的排查过程——从根因定位、到验证"项目自带的参考语料本身也未被验证过"、到设计跨模型对照实验证明"换更大的模型也无法解决"、再到落地"人工核验的知识锚定层"修复方案——整理成了一篇案例研究，供有兴趣的评委/队友查阅：

📄 **[`docs/unsplash_grounding_case_study.md`](docs/unsplash_grounding_case_study.md)** — 案例研究：定位并修复 LLM 的"格式正确但内容幻觉"问题

修复后对项目中全部 38 个唯一外部图片引用（96 处）做了 HTTP 实测审计，**100% 可访问**。

---

## 交互式手机预览

`render_wxml.py` 实现了完整的 WXML → HTML 渲染 Pipeline，在浏览器内模拟微信小程序运行时：

- **标签转换**：`view/text/block/scroll-view` → HTML 等价元素
- **for 循环展开**：`wx:for` 静态展开，`dict[variable]` Tab 模式预渲染所有分组
- **条件渲染**：`wx:if` 保留在 DOM（`data-wx-if`），由注入的 JS Runtime 动态切换
- **bindtap 路由**：`bindtap` → `onclick`，调用内嵌页面 JS 的原始处理函数
- **WeChat JS Shim**：注入 `wx` 全局对象 + `Page()`，使页面 JS 在浏览器中正常执行
- **用户图片注入**：用户上传的图片以 base64 URI 替换占位图

效果展示页 (`showcase.py`) 内置 7 个预生成场景（咖啡点单、米其林餐厅、AI 婚礼工作室、高端定制服务、餐厅点餐、个人中心、课程详情），每个场景均可左预览、右查看完整源码。

---

## 目录结构

```text
app.py                       # Streamlit 主入口：输入 → 生成 → 预览 → 下载
showcase.py                  # 效果展示页（多场景，端口 8502）
render_wxml.py               # WXML → HTML 渲染器 + WeChat JS Runtime Shim
gemma_client.py              # Gemma 4 API + Native Function Calling 工具定义
validators.py                # 静态校验门禁（WXML/WXSS/JS 三项检查）
scaffold.py                  # 固定小程序脚手架（app.json/project.config.json 等）
zip_exporter.py              # 合并脚手架与页面三件套，打包 ZIP
golden_examples.py           # 黄金样例关键词检索 fallback
ci_deployer.py               # 微信开发者工具 CLI 集成（扫码预览/部署）
gemma_core/
  prompt_builder.py          # 三步 Agent Prompt 构建（含验证过的知识锚定库）
  golden_examples/           # 23 个预验证场景语料
  eval_harness.py            # 离线批量评测入口
  validators.py              # 同名校验器（gemma_core 版本）
docs/
  unsplash_grounding_case_study.md   # grounding 问题排查案例研究
tests/                       # 开发期验证脚本（live API 测试、smoke test、解析单测等）
requirements.txt
.env.example                 # API Key 配置模板
```

---

## 项目信息

**比赛**：GDG Shanghai Gemma 4 Hackathon（Track A — AI Agent）
**截止**：2026-06-08 23:59
**运行时模型**：`gemma-4-27b-it`（需求澄清）+ `gemma-4-31b-it`（代码生成 / 自审，Native Function Calling）

**这个项目最想被评委看到的，不是"它能生成代码"，而是：**
1. Gemma 4 的 Native Function Calling 能力被用作系统可靠性的核心来源，而非装饰性调用
2. 一个真正具备"自己发现问题、自己理解错误、自己修正"能力的多步 Agent 闭环
3. 工程上对"生成内容是否经得起真实环境检验"的较真——这篇 grounding 案例研究就是最直接的证据
4. 23 个跨行业场景验证出的方法论可扩展性，而不是一个只能演示一种场景的玩具
