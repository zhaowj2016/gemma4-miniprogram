# MiniPilot Agent

**GDG Shanghai · Gemma 4 开发者大赛 · 赛道 A — 自主 AI Agent / Agentic Code Generation**

## One-line Pitch

> MiniPilot Agent 把 Gemma 4 从聊天模型，变成了小微商家的微信小程序 MVP 生成 Agent。
>
> MiniPilot Agent turns Gemma 4 from a chat model into a small-business WeChat Mini Program MVP generation agent.

一句自然语言描述生意想法 → Agent 通过 **Gemma 4 Function Calling** 理解需求、生成结构化代码、自我校验修复，并把用户上传图片与本地素材一起打包进真实小程序工程，交付一个**可预览、可下载**的小程序页面原型。

---

## Problem — 它要解决的真实问题（对应「真实影响力」30%）

小微商家、个体经营者、本地服务商户想做一个小程序，但常常卡在第一步：

- 不会写代码，传统外包报价数千到上万元、周期数周、沟通成本高；
- 大多数时候并不需要立刻上线一个完整系统，而是想先看到一个能直观判断"这个想法行不行"的 MVP；
- 咖啡点单、活动报名、门店介绍、预约表单、商品展示——这类高频小型需求，找专业团队开发反而"性价比"最低。

**目标用户**：小微商家 / 线下门店 / 个体经营者 / 本地服务商户 / 不会写代码但想快速验证小程序想法的人。

**典型 Prompt**（也是本项目推荐的稳定演示用例）：

- "帮我生成一个咖啡店点单小程序页面，要有商品列表、购物车和底部结算按钮"
- "帮我生成一个活动报名页，要有活动介绍、姓名手机号输入框和报名按钮"
- "帮我生成一个门店介绍页，要有门店封面、营业时间、地址、联系电话和预约按钮"

MiniPilot Agent **不是要替代专业开发**，而是把原本需要"沟通 → 设计 → 开发"才能验证的小程序 MVP 过程，压缩成一次自然语言输入——降低原型门槛、降低试错成本、缩短从想法到可视化原型的周期，让非技术用户也能快速看到效果。

---

## Solution

用户输入一句话需求（可选上传图片） →
Gemma 4 完成需求理解 → 通过 **Function Calling / Tool Calling** 调用 `create_miniprogram_page` 工具，生成结构化的 `wxml / wxss / js` 三件套 →
**Static Validator** 静态校验 → 触发 **Self-Correction** 自愈修复（把错误回传给 Gemma 重新生成）→
**Web 侧手机预览**实时渲染 + **ZIP 导出**。上传图片会被写入 `assets/uploads/`，本地行业素材来自 `assets/library/`；导出与微信预览只携带当前页面实际使用的素材，避免触发微信 2MB 预览包限制。

它的核心不是"调用一个模型把代码吐出来"，而是把 Gemma 4 真正放进一条**软件生产流程**里：理解需求、调用工具、生成代码、接受校验、修复错误、输出可视化结果——形成一个可闭环的 Agentic Workflow。

---

## Demo

- 启动方式见下方 [How to Run](#how-to-run)；在线演示 / Vercel 链接见提交登记信息。
- **推荐演示 Prompt**（来自近期真实迭代中更稳定、容易解释的场景，建议用于评审现场 / 录屏）：
  1. `帮我生成一个咖啡店点单小程序页面，要有商品列表、购物车和底部结算按钮`
  2. `帮我生成一个活动报名页，要有活动介绍、姓名手机号输入框和报名按钮`
  3. `生成一个电商商品详情页，包含商品主图、价格、规格选择、优惠信息和底部购买按钮`
- `app_showcase.py`（端口 8504）是对外展示页，精选 AI 婚礼工作室、米其林餐厅、咖啡点单等更适合讲故事的真实样例。
- `app_demo.py`（端口 8505）是实时生成页，展示 Brief → Gemma Agent Trace → Phone Preview → Source / Zip / 微信预览的完整闭环。预览区会持久化最近一次生成结果，避免页面刷新后丢掉长代码样本。

---

## Agent Pipeline

```text
用户自然语言需求（可选参考图片）
  │
  ▼
P0  需求理解         gemma-4-27b-it 文本推理，补全模糊意图、提炼场景与风格方向
  │
  ▼
P1  Function Calling   gemma-4-31b-it 通过 create_miniprogram_page 工具调用
  │                    （Google AI Studio 主链路 ←→ AMD vLLM Gemma 31B 自托管链路）
  ▼
P2  Code Generation   结构化产出 wxml / wxss / js 三件套
  │
  ▼
P3  Tool Call Parsing  统一解析层 parse_llm_message：
  │                    standard_tool_calls → gemma_raw_tool_call → plain_text_fallback
  ▼
P4  Static Validation  validators.py 静态门禁
  │                    （HTML 标签混入 / 危险 API / 敏感字段 / 事件绑定缺失……）
  ▼
P5  Self-Correction   校验失败 → 错误回传 Gemma 重新生成 → 再校验
  │                    仍失败 → 回退最相近的预验证黄金样例
  ▼
P6  Preview / Export   Web 侧手机预览（WXML→HTML 渲染 + WeChat Runtime Shim）
                       + ZIP 导出 + 分享链接
```

---

## Architecture

```text
Frontend (Streamlit · app_demo.py / app_showcase.py)
  │
  ▼
Model Router  (gemma_client.call_gemma_with_tools)
  ├─ AMD vLLM Client        自托管 Gemma 31B（model: gemm）
  │                         OpenAI-compatible /v1/chat/completions
  │                         + tools / tool_choice + vLLM --tool-call-parser gemma4，流式响应
  │
  └─ Google AI Studio Client   gemma-4-31b-it Native Function Calling
                               functionDeclarations + toolConfig.AUTO
                               官方托管，作为稳定主链路 / 失败兜底
  │
  ▼
统一 Tool Call 解析层  parse_llm_message
  （standard_tool_calls / gemma_raw_tool_call / plain_text_fallback 三层优先级，
    Google 与 AMD 共用同一契约，统一返回 {wxml, wxss, js, provider, parse_method}）
  │
  ▼
Static Validator (validators.py)  →  Self-Correction (prompt_builder.build_repair_prompt)
  │
  ▼
Render Layer：render_wxml.py（手机预览） / zip_exporter.py（工程导出） / 分享链接
```

> 说明：当前代码把「模型路由 / 双后端客户端 / Tool Call 解析层」三部分内聚实现在 [`gemma_client.py`](gemma_client.py) 单文件中（而非拆成多个独立模块），逻辑边界清晰、职责单一，只是物理文件组织与早期规划草案略有差异——技术报告中的代码引用均以实际文件路径为准。

---

## Gemma 4 Usage

| 用途 | 模型 | 调用方式 |
|---|---|---|
| 需求澄清 / 文本理解 | `gemma-4-27b-it`（Google AI Studio） | 普通文本生成，提炼场景关键词与风格方向 |
| 代码生成 + 自审（主链路） | `gemma-4-31b-it`（Google AI Studio，**Dense**） | **Native Function Calling**：`functionDeclarations` + `toolConfig.AUTO` 强制结构化输出 |
| 代码生成（自托管深度链路） | `gemma-4-31b-it`（AMD vLLM 自托管，**Dense**，served name `gemm`） | OpenAI-compatible `tools` + `tool_choice`，配合 vLLM `--tool-call-parser gemma4` |
| 长上下文 / 长输出 | AMD vLLM（`max_model_len = 32768`） | 适合复杂页面生成与多轮修改场景 |

> **模型选型说明**：`Gemma 4 26B-A4B` 是 **MoE** 架构，`Gemma 4 31B` 是 **Dense** 架构——本项目两条链路用的均为 **31B Dense**。

**为什么是双后端**：

- **Google AI Studio = Agent Mode（稳定主链路）**——官方托管 API、原生 Function Calling 支持完整、部署风险低，适合比赛现场稳定演示 Agent 工具调用流程；
- **AMD vLLM Gemma 31B = Deep Generation Mode（技术深度验证）**——验证开源 Gemma 4 的私有化部署能力，提供更长上下文、更长输出、更少限流，更适合复杂页面生成和多轮修改，也是面向"未来私有化部署 + 规模化"路线的可行性验证。两条链路并非互相替代关系：Google 负责稳定演示原生 Function Calling，AMD 负责长上下文 / 长输出 / 私有化部署能力的验证。

---

## Key Features

### 1. Native Function Calling，而非简单文本解析（技术卓越度 25%）

模型必须通过 `create_miniprogram_page` 工具结构化输出 `wxml / wxss / js` 三件套——这不是"调用方式"的偏好问题，而是让 **Gemma 4 的结构化推理能力直接成为系统可靠性的来源**。当前实现保留 live / parser / AMD tool-calls 验证脚本；比赛演示时以现场 API 可用性为准，不把一次旧 live 数字包装成永久承诺。

### 2. 双后端统一工具协议（技术卓越度 25% / 创新性 15%）

Google AI Studio 与 AMD 自托管 vLLM 共用同一套 `create_miniprogram_page` 工具协议，并都接入同一个统一解析层——意味着自部署模型和官方 API 可以无缝互为主备、平滑切换，而不是两套互不相干的代码路径。

### 3. 三层 Tool Call 解析优先级：standard → raw envelope → plain text（技术卓越度 25%）

- **Tier 1** `standard_tool_calls`：标准 OpenAI 格式 `tool_calls[]`（Google `functionCall` 与 AMD vLLM `gemma4` parser 的输出均归一到这一层）
- **Tier 2** `gemma_raw_tool_call`：当 Gemma 自有的 `<|tool_call>...<tool_call|>` 信封裸露为纯文本时的正则适配兜底
- **Tier 3** `plain_text_fallback`：纯三段标记文本解析，最后一道防线

三层不互相替代、不静默吞错——每一层的命中结果都写入日志，前端同步展示当前请求实际命中的 `provider` 与 `parse_method`，让"这次到底是怎么解析出来的"对评委完全透明（见 [`gemma_client.parse_llm_message`](gemma_client.py)）。

### 4. Static Validator 静态门禁（功能完备性 20%）

出站前的自动防蠢门禁：检查 WXML/WXSS/JS 是否完整生成、HTML 标签误用、`{{}}` 内非法函数调用、`<swiper current-index>` 误用、JS `Page({})` 构造、事件绑定缺失、`wx.login / wx.requestPayment / wx.cloud` 等危险真实能力 API、`appsecret / private_key / access_token / session_key` 等敏感字段泄漏。HARD 错误拦截出站并触发自愈，WARNING 仅展示不拦截——理由很直接："能下载的略有瑕疵 Zip，永远好过被误杀拦下的完美 Zip"。

### 5. Self-Correction 自愈闭环（创新性 15% / 功能完备性 20%）

官方 FAQ 对 Function Calling 最佳实践的建议是：当模型返回非标准格式时，应编写鲁棒异常捕获代码并触发 Agent 自我纠错。MiniPilot Agent 的对应实现：生成代码 → Validator 检查 → 发现 HARD 错误 → 把具体错误信息回传给 Gemma 重新生成 → 再次校验；若仍未通过，则回退到最接近原始需求的预验证黄金样例，确保演示链路绝不中断。

### 6. Grounded 图片资产链路（创新性 15%）

真实问题：模型会生成格式完全正确、肉眼难辨，但在真机小程序里不可访问的图片路径。解决方案已从“让模型记住远程 URL”升级为“后端提供本地 `asset_list`”：用户上传图保存为 `assets/uploads/user_upload_###.ext`，行业素材库保存为 `assets/library/...`，Prompt 强约束模型只能使用 `/assets/uploads/...` 或 `/assets/library/...`。如果模型漏插图片，后端会兜底插入 hero image；如果出现 `blob / localhost / data:image / tmp / Unsplash / Picsum` 等污染路径，Validator 会拦截。

近期资产审计记录见 [`docs/image_asset_audit_report.md`](docs/image_asset_audit_report.md)：历史远程图片候选检查 262 个，其中 169 个有效、93 个无效 / 模板 / 非图片；当前运行时素材库覆盖 9 个行业目录，共 27 张本地图片资产。旧的 Unsplash grounding 复盘仍保留在 [`docs/unsplash_grounding_case_study.md`](docs/unsplash_grounding_case_study.md)，作为为什么要做本地资产链路的证据。

### 7. Web 侧手机预览（功能完备性 20%）

自研 WXML → HTML 渲染管线 + 轻量 WeChat Runtime Shim（[`render_wxml.py`](render_wxml.py)）：标签转换、`wx:for` 循环展开、`wx:if` 条件渲染、`bindtap` 事件路由、`wx.showToast / navigateTo / getSystemInfo / Storage` 等常用 API mock + `Page() / setData`，无需安装微信开发者工具即可在浏览器里交互式预览生成结果。**这是 Web 侧低保真模拟，不是微信官方真机渲染或开发者工具编译结果。**

---

## Current Status — 诚实的能力分级

为了避免"过度宣传"，下面如实区分**已实现 / 半实现 / Roadmap**三档（这本身也是我们想体现的工程成熟度的一部分）：

### ✅ 已实现并验证（可在演示中直接展示）

- MiniPilot Agent 品牌化展示页（8504）+ 实时生成页（8505）
- Google AI Studio API 调用 + Native Function Calling（保留 live 验证脚本；现场结果受 API / quota 影响）
- AMD vLLM Gemma 31B 自托管推理 + 标准 `tool_calls` 返回（实测命中 `parse_method = standard_tool_calls`）
- 统一 Tool Call 解析层（三层优先级，Google + AMD 共用同一契约，前端可见 `provider` / `parse_method`）
- raw `<|tool_call>` 信封兜底解析（Gemma 私有格式裸露为文本时的适配层，未被新逻辑替换或删除）
- 长上下文 Prompt 组装（需求澄清 + few-shot 黄金样例检索 + 设计风格随机化）
- 本地图片 asset_list 注入：用户上传图进入 `assets/uploads/`，行业素材进入 `assets/library/`
- 图片路径污染拦截：禁止 `blob / localhost / data:image / tmp / Unsplash / Picsum` 进入 WXML
- 图片兜底插入：模型未使用上传图 / hero 图时，后端自动补 `<image class="hero-image" ... />`
- WXML / WXSS / JS 三件套拆包解析
- Static Validator 静态门禁（接入主流程，校验结果实时展示给用户）
- Self-Correction 自愈（HARD 错误触发，错误回传重新生成，仍失败则回退黄金样例）
- Web 侧手机预览（WXML → HTML 渲染 + WeChat Runtime Shim）
- ZIP 导出 + 分享链接；Zip 会包含全部用户上传图，以及当前页面引用到的 `assets/library` 素材

### ⚙️ 半实现 / 部分验证（已有代码，但存在边界条件或外部依赖）

- **微信官方真机预览二维码**：[`ci_deployer.py`](ci_deployer.py) 已真实集成官方 `miniprogram-ci` / `upload.js`，会把页面文件、上传图与本地素材复制到同一个 `projectPath` 后再预览；但它依赖真实 AppID、私钥、CI 权限、IP 白名单和微信侧频率限制，因此不作为核心展示路径，仅作为可选进阶能力保留；
- **AMD vLLM 自托管链路的可用性**：依赖外部云端 GPU 实例，实例重启会导致网关地址变化、需人工同步配置——技术上已验证可行（标准 `tool_calls` 已稳定命中），但尚不具备生产级"开箱即用"的稳定性；
- **图片裁剪**：上传图片会做轻量自动裁边，适合处理截图边缘黑块 / 空白边，但还不是完整的人工裁剪器或多图相册编辑器。

### 🗺️ Roadmap（明确列出，不与"已实现"混淆）

- 更完整的用户图片编辑：手动裁剪、主体定位、多图排序与素材管理
- LoRA / SFT 提升输出格式稳定性（详见 Limitations 中"为什么当前不做微调"）
- 将 `miniprogram-ci` 校验纳入主流程的自动化门禁（当前为可选手动操作）
- 多轮修改输入框 / 商业模板市场
- 更多场景的"导入微信开发者工具"人工验证记录与截图

---

## Limitations

诚实声明当前的工程边界，避免任何夸大宣传：

- **不是**生产级小程序编译器，**不保证**微信开发者工具 0 Error 编译——`validators.py` 是 Hackathon 阶段的自研静态门禁，用于提前拦截高频低级错误，不能取代真实编译验证；
- **未完成**完整的微信小程序上线链路，**未实现**支付 / 登录 / 云开发，且明确不在当前阶段范围内；
- **未进行**模型微调——当前阶段时间有限、ROCm / AMD 微调链路复杂；更关键的是，当前核心瓶颈并非模型知识本身，而是工具协议、静态校验、grounding 与 Demo 稳定性，微调也不适合用来"记忆图片 URL 等具体外部事实"（这正是 grounding 案例研究揭示的核心结论：模型对"格式长什么样"的记忆远强于对"某个具体实例是否真实存在"的记忆，唯一可靠的解法是把事实性查证从生成过程中剥离）；
- **多模态**目前是"上传图片进入真实项目资源 + 轻量自动裁边 + grounded 图片选取"，**未实现**完整的"图生小程序"闭环或音视频多模态；
- Web 侧手机预览是**低保真模拟**（轻量 WeChat Runtime Shim，覆盖常用 API 子集），不是微信真机渲染或开发者工具编译结果；部分生成结果可手动导入微信开发者工具进一步验证，生产级编译、真机预览和上线链路是下一阶段工作。

---

## Roadmap

- **短期**：打磨推理 + 工具调用 + Validator + Grounding 各环节的稳定性
- **中期**：积累更多高质量小程序生成样本，扩展跨行业场景覆盖
- **长期**：LoRA / SFT 提升输出格式稳定性与领域风格；探索 `miniprogram-ci` 自动化门禁、多轮修改、商业模板市场等方向

---

## How to Run

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key（任选其一）
cp .env.example .env          # 填入 GEMINI_API_KEY
# 或：export GEMINI_API_KEY=your_key_here

# 3. 启动实时生成页（代码生成器，含完整 Pipeline）
streamlit run app_demo.py --server.port 8505

# 4. 启动效果展示页（多场景速览，无需等待实时生成）
streamlit run app_showcase.py --server.port 8504
```

访问 `http://localhost:8505` 使用实时生成器；访问 `http://localhost:8504` 浏览 MiniPilot Agent 展示页。

> AMD vLLM 自托管链路是可选的加分项：在 `E:\file+desktop\gemma_amd_config.txt` 配置网关地址与凭证后自动启用；未配置时系统直接走 Google AI Studio 主链路，不影响核心功能可用性——这正是双后端架构"互为主备"的体现。

### Docker 快速体验

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV GEMINI_API_KEY=your_key_here
CMD ["streamlit", "run", "app_demo.py", "--server.port", "8505", "--server.address", "0.0.0.0"]
```

```bash
docker build -t minipilot-agent .
docker run -p 8505:8505 -e GEMINI_API_KEY=your_key minipilot-agent
```

---

## 目录结构

```text
app_demo.py                  # 实时生成页：输入 → 生成 → 校验 → 自愈 → 预览 → 下载 / 微信预览
app_showcase.py              # MiniPilot Agent 展示页（多场景速览，端口 8504）
app.py / showcase.py         # 早期入口，保留用于兼容旧流程
gemma_client.py              # Gemma 4 双后端调用 + Native Function Calling + 统一 Tool Call 解析层
render_wxml.py               # WXML → HTML 渲染器 + WeChat Runtime Shim（Web 侧手机预览）
validators.py                # 静态校验门禁（WXML/WXSS/JS + 安全检查）
scaffold.py                  # 固定小程序脚手架（app.json/project.config.json 等）
zip_exporter.py              # 合并脚手架与页面三件套，打包 ZIP
golden_examples.py           # 黄金样例关键词检索 fallback（自愈兜底）
ci_deployer.py               # 微信官方 miniprogram-ci CLI 集成（可选：扫码预览/部署）
miniprogram_assets.py        # 上传图保存、轻量裁边、asset_list、hero image 兜底插入
assets/library/              # 本地行业图片素材库；导出/预览时只复制当前页面引用到的文件
gemma_core/
  prompt_builder.py          # 需求澄清 / 代码生成 / 自审 / 自愈全套 Prompt 构建（含图片 grounding 库）
  golden_examples/           # 23 个预验证场景语料
  eval_harness.py            # 离线批量评测入口
docs/
  image_asset_audit_report.md       # 本地图片资产与历史远程图片审计记录
  unsplash_grounding_case_study.md   # grounding 问题排查案例研究
tests/                       # 开发期验证脚本（live API 测试、解析单测、AMD 标准 tool_calls 验证等）
requirements.txt
.env.example                 # API Key 配置模板
```

---

## 项目信息

**比赛**：GDG Shanghai · Gemma 4 开发者大赛（赛道 A — 自主 AI Agent / Agentic Code Generation）
**截止**：2026-06-08 23:59
**核心模型**：Gemma 4（Google AI Studio 托管 `gemma-4-27b-it` / `gemma-4-31b-it` + AMD vLLM 自托管 `gemma-4-31b-it`，均为 **Dense** 架构）

**这个项目最想让评委看到的，不是"它能生成代码"，而是**：

1. Gemma 4 的 Native Function Calling 被用作系统可靠性的核心来源，而非装饰性调用——双后端、统一协议、三层解析优先级，都是为了让"结构化输出"这件事在任何环境下都立得住；
2. 一个真正具备"自己发现问题、自己理解错误、自己修正"能力的多步 Agent 闭环（Validator + Self-Correction）；
3. 工程上对"生成内容是否经得起真实环境检验"的较真——grounding 案例研究是最直接的证据；
4. 诚实的工程边界声明：清楚知道现在做到了什么、还差什么——这本身就是技术成熟度的一部分。

---

```text
MiniPilot Agent turns Gemma 4 from a chat model into a small-business software prototyping agent.
通过 MiniPilot Agent，一个小商家的生意想法，可以被 Gemma 4 转化成一个可预览的小程序 MVP。
```

