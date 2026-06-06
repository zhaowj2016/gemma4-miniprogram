# Gemma Match

**GDG Shanghai Gemma 4 Hackathon · Track A — AI Agent**

用 **Gemma 4 Native Function Calling** 生成微信小程序源码的 AI Agent。用户在 Streamlit 页面输入自然语言需求，Agent 三步推理后输出可直接导入微信开发者工具的 ZIP，同时在浏览器内渲染交互式手机预览。

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

访问 `http://localhost:8501` 即可使用代码生成器；访问 `http://localhost:8502` 查看 5 个预生成场景展示。

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
用户输入
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1 · 需求澄清  (gemma-3-27b-it)                        │
│  分析输入，提取业务场景、功能要点、UI 风格，补全模糊需求    │
└─────────────────┬───────────────────────────────────────────┘
                  │ 结构化 prompt
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2 · 代码生成  (gemma-3-31b-it · Native Function Call) │
│  调用 create_miniprogram_page(wxml, wxss, js) 工具           │
│  模型必须通过 Function Calling 返回结构化三件套              │
└─────────────────┬───────────────────────────────────────────┘
                  │ {wxml, wxss, js}
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3 · 自审优化  (gemma-3-31b-it)                        │
│  审阅生成结果，检查绑定完整性，输出最终版本                 │
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

### Native Function Calling 实现

`gemma_client.py` 中使用 Gemma 4 官方 `functionDeclarations` 格式：

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

Function Calling 触发率：**100%**（5/5 live 测试通过，见 `test_live.py`）

---

## 交互式手机预览

`render_wxml.py` 实现了完整的 WXML → HTML 渲染 Pipeline，在浏览器内模拟微信小程序运行时：

- **标签转换**：`view/text/block/scroll-view` → HTML 等价元素
- **for 循环展开**：`wx:for` 静态展开，`dict[variable]` Tab 模式预渲染所有分组
- **条件渲染**：`wx:if` 保留在 DOM（`data-wx-if`），由注入的 JS Runtime 动态切换
- **bindtap 路由**：`bindtap` → `onclick`，调用内嵌页面 JS 的原始处理函数
- **WeChat JS Shim**：注入 `wx` 全局对象 + `Page()`，使页面 JS 在浏览器中正常执行
- **用户图片注入**：用户上传的图片以 base64 URI 替换占位图

效果展示页 (`showcase.py`) 内置 5 个场景：

| 场景 | 行数 | 特色 |
|------|------|------|
| 💍 AI婚礼工作室 | ~700 行 | 3 Tab 切换、图片画廊、AI 服务卡片 |
| 🍽️ 米其林餐厅 | ~620 行 | 品鉴/单点菜单、轮播 Banner、滚动播报 |
| 🍜 普通点餐 | ~500 行 | 商品列表、购物车计数 |
| 👤 个人中心 | ~400 行 | 用户信息、订单状态 |
| 📚 课程详情 | ~450 行 | 章节列表、进度显示 |

---

## 目录结构

```text
app.py                       # Streamlit 主入口：输入 → 生成 → 预览 → 下载
showcase.py                  # 效果展示页（5 场景，端口 8502）
render_wxml.py               # WXML → HTML 渲染器 + WeChat JS Runtime Shim
gemma_client.py              # Gemma 4 API + Native Function Calling 工具定义
validators.py                # 静态校验门禁（WXML/WXSS/JS 三项检查）
scaffold.py                  # 固定小程序脚手架（app.json/project.config.json 等）
zip_exporter.py              # 合并脚手架与页面三件套，打包 ZIP
golden_examples.py           # 黄金样例关键词检索 fallback
gemma_core/
  prompt_builder.py          # 三步 Agent Prompt 构建（含约束清单）
  golden_examples/           # 19 个预验证场景语料（含 ai_wedding_studio、michelin_restaurant）
  eval_harness.py            # 离线批量评测入口
  validators.py              # 同名校验器（gemma_core 版本）
requirements.txt
.env.example                 # API Key 配置模板
```

---

## 项目背景

**比赛**：GDG Shanghai Gemma 4 Hackathon（Track A — AI Agent）  
**截止**：2026-06-08 23:59  
**核心亮点**：
1. Gemma 4 Native Function Calling 强制输出结构化代码（非文本解析）
2. 三步自主 Agent Pipeline，具备自愈能力（hard error 反馈重试）
3. 浏览器内完整模拟微信小程序运行时（可交互手机预览）
4. 19 个黄金样例语料库，覆盖主流小程序场景
