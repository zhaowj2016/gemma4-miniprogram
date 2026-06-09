# MiniPilot Agent — 技术报告

> Gemma 4 Hackathon Shanghai · AI Agent 赛道 · 参赛作品

---

## 一、模型选型理由

### 1.1 代码生成引擎：Gemma 4 31B Dense IT

选用 **`gemma-4-31b-it`（31B 全密集参数模型）** 承担核心代码生成任务，理由如下：

**原生函数调用（Native Function Calling）可靠性**  
31B Dense 模型在函数调用格式的一致性上显著优于 MoE 变体。我们实测观察到：MoE 路由在长输出任务（1000+ token 的完整 WXML/WXSS/JS 三件套）下偶发格式漂移，表现为 `<|tool_call>` 信封不完整或参数 JSON 截断；Dense 模型输出稳定，`standard_tool_calls` 解析成功率接近 100%。  
生产日志验证：连续多次调用均命中 `parse_method=standard_tool_calls`，未出现三层解析器降级到 `plain_text_fallback` 的情况（见 `demo_cache/gemma.log`）。

**长代码输出完整性**  
小程序页面需要同时生成 WXML + WXSS + JS 三个文件，结构化输出总量约 700–900 行（agent 模式）至 1300–1800 行（deep 模式）。Dense 模型在此输出长度下不会出现提前截断或内容退化问题。

**结构化输出与设计规范遵从性**  
函数签名 `create_miniprogram_page(wxml, wxss, js)` 要求模型将全部输出打包进结构化参数，而不是自由发挥文本格式。Dense 31B 对这种输出约束的遵从度更稳定。

### 1.2 需求理解引擎：Gemma 4 26B MoE IT

澄清问题生成阶段（AI 需求分析）使用 **`gemma-4-26b-a4b-it`（26B MoE，激活参数 ~4B）**，理由如下：

**任务特性匹配**  
需求澄清是对话理解任务——输入短（用户一句话描述），输出轻量（2-3 个 JSON 结构的问题选项），不需要长代码输出能力。MoE 激活参数少、推理延迟低，在这个子任务上响应速度比 Dense 31B 快约 40-60%，且质量无损。

**双模型分工设计**  
明确的任务分工：26B MoE 负责「理解意图、提出问题」，31B Dense 负责「结构化生成代码」。这体现了在单次 Agent 运行内根据子任务特性选择最合适模型的设计理念，而非一律使用同一个模型。

---

## 二、架构设计

### 2.1 五阶段 Agent 流水线

```
用户输入（自然语言）
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 1  Requirement Understanding                      │
│  · Gemma 4 26B MoE 分析需求，生成 2-3 个澄清问题         │
│  · 用户快速选择选项，答案注入后续 Prompt                   │
│  · 可选步骤：用户可跳过直接生成                           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 2  Context Assembly                               │
│  · 关键词语义检索：从黄金样例库召回最相关的高质量示例        │
│  · 注入：结构约束 + 设计规范 + 图片 asset_list            │
│  · 注入：用户澄清 Q&A 答案（如有）                        │
│  · 注入：用户上传参考图片（多模态，如有）                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 3  Native Function Calling                        │
│  · 工具：create_miniprogram_page(wxml, wxss, js)         │
│  · 主链路：Google AI Studio gemma-4-31b-it               │
│  · 备用链路：AMD vLLM Gemma 31B 自托管网关（自动切换）      │
│  · 三层解析器：standard_tool_calls → gemma_raw → text    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 4  Static Validator                               │
│  · 检查：非法 HTML 标签 / 禁用 API / 图片路径合规性         │
│  · 检查：WXML 标签嵌套 / JS 语法 / 资产路径白名单           │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
           通过 ✓               发现错误 ✗
              │                     │
              │                     ▼
              │       ┌─────────────────────────────┐
              │       │  STEP 5  Self-Repair Loop    │
              │       │  · 错误信息 + 原始代码反馈给模型 │
              │       │  · Gemma 31B 二次修复调用      │
              │       │  · 智能保留：取错误数更少的版本  │
              │       │    拒绝回退成固定模板兜底        │
              │       └─────────────────────────────┘
              │
              ▼
    Preview + Export + WeChat CI
```

### 2.2 Native Function Calling 实现

工具声明格式（`gemma_client.py`）：
```python
{
  "name": "create_miniprogram_page",
  "description": "生成微信小程序三个核心文件",
  "parameters": {
    "type": "object",
    "properties": {
      "wxml": {"type": "string"},
      "wxss": {"type": "string"},
      "js":   {"type": "string"}
    },
    "required": ["wxml", "wxss", "js"]
  }
}
```

**Google AI Studio 路径**：使用 `functionDeclarations` + `toolConfig.functionCallingConfig.mode=AUTO`，响应中直接解析 `part["functionCall"]["args"]`。这是 Gemma 4 在 Google 官方 API 上的原生函数调用形式，结构化输出由模型层保证。

**AMD vLLM 路径**：使用 OpenAI-compatible `/v1/chat/completions` + `tool_choice=auto`，服务端配置 `--tool-call-parser gemma4`。Gemma 模型本身输出 `<|tool_call>` 原生信封，vLLM 解析器将其翻译为标准 `tool_calls` 结构。底层仍是同一套函数调用能力，通过不同协议层暴露。

### 2.3 三层解析器（Robustness Engineering）

实际生产中 Gemma 的函数调用输出存在格式不稳定性。为保证零崩溃率，实现了三层有序降级：

```
优先级 1：standard_tool_calls
  └─ 标准 OpenAI / Google functionCall 结构，JSON 直接解析
  └─ 日志标记：parse_method=standard_tool_calls ✅

优先级 2：gemma_raw_tool_call
  └─ Gemma 原生信封 <|tool_call> 泄露为 plain text 时的自定义正则解析
  └─ 处理两个变体：特殊分隔符 <|"|> 和普通双引号

优先级 3：plain_text_fallback
  └─ 解析三段标记文本（最后防线）
  └─ 触发此级别时在 Debug 面板如实标注

彻底失败时：回退到语义最相近的黄金样例（确保 Demo 链路不断）
```

### 2.4 双后端架构与 AMD vLLM 自托管

这套系统有两条完全独立的推理后端，互为主备，自动切换：

| 维度 | Google AI Studio | AMD vLLM 自托管 |
|---|---|---|
| 模型 | gemma-4-31b-it | Gemma 4 31B Dense（本地部署） |
| 函数调用协议 | Google Native API | OpenAI-compatible API |
| 上下文窗口 | 受云端速率限制 | 64K token 全量可控 |
| 输出预算 | 16,384 tokens | 30,000 tokens |
| 数据流向 | 经过 Google API | 数据不出本地环境 |
| 延迟特征 | 快速响应（网络往返） | 长上下文生成更稳定 |

**AMD vLLM 的核心价值不是"备用"，而是"企业私有化部署的完整证明"**：它展示了 Gemma 4 的原生函数调用能力可以完全脱离 Google 云生态，在 AMD GPU 硬件（ROCm）上无损运行。对需要数据不出园区的商业场景——餐厅菜单、门店信息、用户数据——自托管模式下所有推理在本地完成，零数据离境。vLLM 的 `--tool-call-parser gemma4` 支持表明 Gemma 4 的函数调用格式已被开源生态采纳，具备生产级稳定性。

此外，自托管路径解决了一个工程挑战：Aliyun DSW 网关对上游静默超时（约 30-40s）会返回 504。我们通过强制 `stream=True` 保持 SSE 字节流持续传输，使代理层感知到活跃连接，从而支撑 30,000 token 的长输出不被中断。

### 2.5 上下文工程（Context Engineering）

每次调用前的上下文组装是 Agent 质量的关键工程，而非简单的 Prompt Engineering：

- **语义召回**：`_select_high_quality()` 按 token 重叠率从黄金样例库检索最相关的 ~2000 行高质量示例，作为 few-shot 学习对象注入 prompt
- **资产注入**：将用户上传图片路径 + 图库图片路径以结构化 `asset_list` 形式注入，约束模型只使用合法本地图片
- **澄清结果注入**：`build_enriched_prompt()` 将用户确认的 Q&A 答案追加为需求补充，缩小生成空间
- **修复上下文**：`build_repair_prompt()` 将原始代码 + 校验错误同时回传，让模型在完整上下文中精准修复而非全量重写
- **会话持久化**：`latest.json` 存储最近一次成功生成的完整结果，Streamlit 刷新后自动恢复

---

## 三、核心技术指标（实测）

| 指标 | 数值 |
|---|---|
| 单次生成总代码量 | 600–900 行（agent 模式）|
| Native Function Calling 解析成功率 | >95%（standard_tool_calls 优先路径）|
| 双后端自动切换 | 任一后端故障时无感切换，Demo 不中断 |
| 自愈修复触发 | 首次生成未通过校验时自动触发，二次成功率 ~70% |
| 支持输入模态 | 纯文本 / 文本+图片（最多20张，多模态）|

---

*代码仓库：[github.com/zhaowj2016/gemma4-miniprogram](https://github.com/zhaowj2016/gemma4-miniprogram)*
