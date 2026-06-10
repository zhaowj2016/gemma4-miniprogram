# 运行日志截图指南

> 针对 AI Agent 赛道评审要求：清晰展示 Agent 的 Memory/Context、Tool Calling 逻辑及运行日志。

---

## 优先级排序（含金量从高到低）

### 🥇 第一优先级：Function Calling 成功证明

**截取目标**：`demo_cache/gemma.log` 中以下类型的行组合

```
2026-06-08 18:13:38  [generate][amd_vllm] tool_call(openai)=OK lines={'wxml':124,'wxss':452,'js':94} parse_method=standard_tool_calls provider=amd
2026-06-08 18:13:38  [generate][amd_vllm] ✅ AMD vLLM standard tool_calls parsed successfully
```

或 Google 路径的：
```
2026-06-08 20:16:52  [generate] function_call=OK wxml=106L wxss=410L js=160L total=676L
```

**为什么含金量最高**：这两行是"模型真正使用了函数调用"的直接证据。`standard_tool_calls` 表示 Gemma 4 返回了结构化的函数调用结果（不是文本解析兜底），`tool_call(openai)=OK` 表示 AMD vLLM 端成功解析。这是 Native Function Calling 能力最直接的运行时证明。

**截图建议**：打开 `demo_cache/gemma.log`，找到一段包含下列要素的连续 4-6 行：
1. `=== NEW REQUEST ===`（开始标记）
2. `[clarify] model=gemma-4-26b-a4b-it`（需求理解阶段，MoE 模型）
3. `[generate] === NEW REQUEST ===`（代码生成阶段切换）
4. `function_call=OK` 或 `standard_tool_calls parsed successfully`（成功证明）

这 4 行连在一起截图，完整展示了从 26B MoE 澄清到 31B Dense 生成的双模型流水线。

---

### 🥈 第二优先级：自愈修复循环（已有截图）

**文件位置**：`docs/screenshots/runtime_log_v2/01_trace_data_after_completion.png`

**内容说明**：这张截图展示了 Trace data 中 `STEP 06 Repair Loop WARN` 状态，对应应用内日志里的"启动自愈，重新调用模型修复"流程。这是"Agent 多步规划"在运行时的具体体现——模型生成代码 → 静态校验发现问题 → 自动触发二次修复调用。

**已有，无需重新截**。

---

### 🥉 第三优先级：完整 7 步 Agent Trace（已有截图）

**文件位置**：`docs/screenshots/runtime_log_v2/02_recent_gemma_log_matching_run.png`

**内容说明**：展示 Trace entries 5-6（修复循环 + 预览输出）+ 对应 gemma.log 的真实日志行，证明截图与实际运行一一对应。

**已有，无需重新截**。

---

### 📎 现有截图清单与使用建议

| 文件 | 内容 | 使用场景 |
|---|---|---|
| `docs/screenshots/01_dual_mode_selector.png` | 主页双模式选择器 | 展示产品入口，配文字说明用 |
| `docs/screenshots/02_agent_pipeline_live_multistep.png` | 生成过程中出现"发现 9 个问题 → 启动自愈" | **直接证明自愈流程被触发**，高价值 |
| `docs/screenshots/03_agent_memory_trace_json.png` | Trace data JSON（entries 0-2） | 展示 Context Assembly 步骤的元数据 |
| `docs/screenshots/04_runtime_log_tool_calling.png` | ⚠️ 有内部不一致（Trace 显示"未触发"但 02 截图已触发） | 建议不用或加注说明 |
| `docs/screenshots/runtime_log_v2/01_trace_data_after_completion.png` | ✅ 修正版：STEP 06 Repair Loop WARN + 完整 Trace | 替代 04，使用这张 |
| `docs/screenshots/runtime_log_v2/02_recent_gemma_log_matching_run.png` | ✅ 修正版：Trace 5-6 + 对应 gemma.log 真实行 | 展示日志与截图对应关系 |

---

## 还需要补截的内容（可选，加分项）

### 补截 A：双模型分工证明（最容易加分）

在 `demo_cache/gemma.log` 中，找到 `[clarify] model=gemma-4-26b-a4b-it` 和紧接着的 `[generate] === NEW REQUEST ===` 这两个连续事件，截图。

这直接证明了 Agent 使用了两个不同规格的 Gemma 4 模型完成不同子任务（26B MoE 理解需求 / 31B Dense 生成代码），是双模型分工架构最简洁的证明。

### 补截 B：双后端自动切换（如果现场能复现）

从 log 里找到这段（或现场触发一次 agent 模式 + Google 临时不可用的情况）：
```
[generate][google] FAILED in agent mode, falling back to AMD vLLM: ...
[generate][amd_vllm] === NEW REQUEST (stream) === model=gemm
[generate][amd_vllm] ✅ AMD vLLM standard tool_calls parsed successfully
```

这是"双后端互为主备"最有说服力的实证。

---

## Demo 现场截图脚本（5分钟 Demo 用）

建议按以下顺序展示，每张停留 20-30 秒：

1. **产品功能演示**：现场运行一次生成（选「门店预约页」或「咖啡店点单页」）
2. **Function Calling 证明**：生成完成后，打开 Debug 面板 → 展示 Trace data（STEP 03 Function Calling = OK）
3. **日志证明**：切到终端，`tail -20 demo_cache/gemma.log`，展示 `function_call=OK` 行
4. **自愈能力**（如能触发）：展示截图 02（发现问题 → 启动自愈 → 成功）
5. **双后端架构**：展示 UI 上的模式选择器（agent / deep 两种模式），说明背后是两套不同推理链路
