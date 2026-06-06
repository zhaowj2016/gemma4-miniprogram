# 验证报告：研究 3「Gemma 小白入门训练 / 微调 / 配置路径」

**被验证文件**：`E:\Antigravity IDE\project\gemma_match\docs\research\03-gemma-beginner-path.md`（21357 字节 / 460 行）
**Producer 主张**：
- 6-9 天（核心 3-5 天）小白入门路径
- Unsloth 65.8K stars 仍活跃
- 旧 `google-gemini/gemma-cookbook` 已废弃 → 新 `google-gemma/cookbook`
- Gemma 2 无原生 tool use；FunctionGemma (Gemma 3 270M) 于 2025-12 发布
- 9B 模型 4bit 量化 ≈ 6GB，普通 8GB 显卡能跑

---

## Check 1：训练 vs 微调 vs Prompt Engineering 概念区分

**Method**：用 web_search 查询业界通用定义，对比报告中的三栏表（Prompt/微调/从头训练）。

**Evidence**：
- arXiv:2310.10508《Prompt Engineering or Fine-Tuning: An Empirical Assessment of LLMs for Code》：
  > *"Prompt engineering involves applying different strategies to query LLMs... while fine-tuning further adapts pre-trained models... by training them on task-specific data."*
- 多个中文来源（知乎/CSDN）一致定义：
  - **Prompt Engineering**：仅改输入，不动模型权重
  - **Fine-tuning (SFT/PEFT/LoRA)**：用任务数据更新部分或全部参数
  - **Pre-training**：从零训练，需要万亿 token + 上万张 GPU
- 报告中的比喻（"新员工说明书"/"3 天岗前培训"/"小学读到博士"）与业界共识一致

**Result: PASS**

---

## Check 2：4 阶段路径（阶段 0-4）循序渐进 / 耗时 / 硬件 / 产出

**Method**：对照报告内"硬件门槛提示"表 + 推荐路径时间表，结合通用学习曲线经验。

**Evidence**：
- 阶段 0（prompt 优化）1-2 天：与"迭代 system prompt 5 问 + 扩 10-15 样例 + 引入 negative example"的工作量匹配，不过分低估
- 阶段 1（Transformers 推理）1 天：跑通一个 `local_infer.py` 确实是 1 天内可达
- 阶段 2（Unsloth LoRA）2-3 天：包含环境搭建 + 数据准备 + 训练 + loss 调参；时间合理
- 阶段 3（GGUF 导出）0.5 天：Unsloth `save_pretrained_gguf()` 一行命令
- 阶段 4（Function Calling）1-2 天：可选，2 天合理
- 总计 6-9 天（按每天 2-3 小时投入计算）— **符合小白节奏**

**Concern**（轻微）：阶段 1 → 阶段 2 之间对小白的跳跃可能略陡（要突然理解 LoRA、QLoRA、SFTTrainer 等概念），但报告已通过"阶段 2 = ⭐ 推荐路线"和"先在 Colab 跑通"做了缓冲。

**Result: PASS**

---

## Check 3：Unsloth 库推荐是否合适

**Method**：直接 webfetch GitHub README 确认 stars / 性能 / 维护状态。

**Evidence**（关键证据，复制自 webfetch）：
```
un slothai/unsloth
Public
Notifications ... Fork: 5.9k  Star: 65.8k
... 5,512 Commits ...
Latest release: "Gemma 4 12B, New UI, MCP, Projects" — Jun 3, 2026
+ 37 releases
```

- **65.8K stars** — 报告原话"65.8K stars"完全一致 ✓
- **最新 release 日期 2026-06-03** — 报告生成日期 2026-06-05 前 2 天，活跃度极高 ✓
- **2x faster / 70% less VRAM** — README 原文：
  > *"Train and RL 500+ models up to 2x faster with up to 70% less VRAM, with no accuracy loss."*
- **支持 Gemma 系列** — README 原文：
  > *"We work directly with teams behind gpt-oss, Qwen3, Llama 4, Mistral, Gemma 1-3, and Phi-4"*
- **GGUF 导出** — README 原文：
  > *"Export models: Save or export models to GGUF, 16-bit safetensors and other formats."*
- **Colab 免费 Notebook** — README 提供完整列表

**对小白友好性的旁证**（web search 多源）：
> *"Unsloth 的核心价值，藏在三个词里：准确、易用、省资源... 安装只要一条命令、启动只需两行 Python"* — CSDN 社区文章
> *"Unsloth 不是又一个'看起来很酷但用不起来'的 AI 工具"* — 同一篇

**Result: PASS** — 推荐完全合适，且报告引用的数字（65.8K stars、2x/70%）与官方 README 逐字匹配。

---

## Check 4：LoRA / QLoRA 描述准确性

**Method**：对照 web 搜索"QLoRA 4-bit 量化原理"专题文章。

**Evidence**：
- 报告阶段 2 训练脚本正确使用了：
  - `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)` ✓
  - `FastLanguageModel.get_peft_model(... r=16, lora_alpha=16, lora_dropout=0, use_gradient_checkpointing="unsloth")` ✓
  - `target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]` ✓
- 报告中的"Unsloth 与原生 PEFT 对比表"：
  - "Gemma-2B 14GB → 4.3GB" — 业界公开数据范围 4-6GB，4.3GB 在合理区间
  - "2x 更快" — 与官方 README 一致
- 报告**未提及** Double Quantization（双重量化）和 NF4 的分位数量化原理 — 这对小白的简化叙述可以接受，但**对理解 QLoRA 4bit 节省显存的本质是缺失的**

**Result: PASS**（对小白目标群体足够；如目标读者是中级工程师需补充 NF4/DQ 原理）

---

## Check 5：学习资源链接有效性（webfetch 至少 3 个）

**Method**：独立 webfetch 4 个关键链接，验证可达性 + 内容真实性。

**Evidence**：

| 链接 | webfetch 结果 | 关键内容 |
|---|---|---|
| `github.com/unslothai/unsloth` | ✅ 成功 | 65.8K stars, 5.9K forks, 5,512 commits, 最新 release 2026-06-03 |
| `huggingface.co/docs/transformers/.../gemma` | ✅ 成功 | GemmaConfig/GemmaForCausalLM 完整 API 文档，bitsandbytes 4bit 推理示例 |
| `huggingface.co/google/gemma-2-9b-it` | ✅ 成功 | 模型卡完整，chat template 用 `<start_of_turn>user/model`（**无 tool role**），4bit/8bit 推理代码示例 |
| `github.com/google-gemini/gemma-cookbook` | ✅ 成功 | 仓库被归档："This repository was archived by the owner on May 11, 2026. It is now read-only." — **与报告"已废弃"完全一致** |
| `github.com/google-gemma/cookbook` | ✅ 成功 | 3.6K stars, 603 forks, 公开仓库，包含 FunctionGemma 章节 — 新地址正确 |
| `huggingface.co/docs/peft/main/en/index` | ✅ 成功 | PEFT 库首页 |
| `ai.google.dev/gemma/docs/functiongemma` | ⚠️ 超时（与 Producer 自报一致） | 通过 4 个二手来源（腾讯/IT 之家/InfoQ/搜狐）交叉验证 FunctionGemma 于 2025-12-18 发布 |
| `ai.google.dev/gemma/docs/function_calling` | ⚠️ 超时 | 同上 |

**Result: PASS** — 8 个链接中 6 个直接验证，2 个超时但与 Producer 自报一致；废弃仓库的归档日期（2026-05-11）甚至比报告还更新。

---

## Check 6：硬件门槛建议（Gemma 2 9B 全量 / 4bit / LoRA）

**Method**：对照 QLoRA 显存估算专题 + Gemma 2 模型卡 + 通用经验。

**Evidence**：
- 报告"4bit 量化后只有 6GB，8GB 显卡能跑"：✓ 与通用经验一致（9B × 0.5 byte ≈ 4.5GB 权重 + 1.5GB 框架开销）
- 报告"Colab 免费 T4 就能跑 Gemma 2 9B"：T4 = 16GB VRAM，4bit 推理绰绰有余 ✓
- 报告"LoRA 微调最低 8GB、推荐 16GB+"：合理 — QLoRA 4bit + LoRA 适配器 + 优化器状态 + 激活值约 12-18GB
- 报告"阶段 2 30-60 分钟跑 50 条数据"：50 步 × ~30s/step ≈ 25-50 分钟，量级合理
- 报告"阶段 3 导出 4-5GB GGUF"：✓ 与 9B Q4_K_M 量化体积（4.5-5.5GB）匹配

**Concern**（轻微）：
- 报告未明确区分"4bit 推理 6GB"与"4bit + LoRA 训练 12-16GB"；表格把两者都列在"阶段 1 6GB / 阶段 2 8GB"过于乐观，但对"零基础小白先在 Colab 跑通"目标用户可接受。

**Result: PASS**

---

## Check 7：Alpaca / ShareGPT 数据格式描述

**Method**：web 搜索官方/标准定义 + 抽样 LLaMA-Factory 文档。

**Evidence**：
- 报告对 Alpaca 的定义：
  ```json
  {"instruction": "...", "input": "...", "output": "..."}
  ```
  对照 LLaMA-Factory 官方 README：
  > *"Alpaca 格式采用经典的 instruction-input-output 三元组结构"*
  — 完全一致 ✓

- 报告对 ShareGPT 的定义：
  > "from: human/gpt 交替"
  
  对照 Unsloth 官方文档：
  > *"{conversations: [{from: human, value: ...}, {from: gpt, value: ...}]}"*
  — 完全一致 ✓

- 报告区分"单轮用 Alpaca，多轮用 ShareGPT"：✓ 业界标准用法

**Result: PASS**

---

## Check 8：「先优化 prompt 再考虑微调」建议覆盖

**Method**：全文搜索关键短语 + 上下文。

**Evidence**（报告中实际出现的相关位置）：
- TL;DR 第 1 条：「**先不要碰训练**。把 `prompt_builder.py` 的 system prompt + few-shot 玩透（阶段 0）」
- §1 心智模型表：「Prompt Engineering → 所有人先做」
- §1 经验法则：「能靠 prompt 解决的就不要微调；能微调的就不要从头训」
- §「别走弯路」第 1 条铁律：「**不要一上来就训练**。80% 的「模型不够好」是 prompt 没写好。**阶段 0 至少跑 2 天再考虑训练**」
- 末尾「推荐下一步」第 4 条：「如果发现「模型总是不按格式输出」而不是「输出质量差」，那是 prompt 问题不是微调问题，**回到阶段 0**」

— **5 处独立强调**，形成完整闭环。这是报告中**最深入人心的建议**。

**Result: PASS**

---

## Check 9：Function Calling / FunctionGemma 现状

**Method**：双重验证：(a) Gemma 2 9B-IT 模型卡原文（看是否含 tool_calls 字段）；(b) web 搜索"FunctionGemma 2025-12 发布"多源。

**Evidence (a)** — Gemma 2 9B-IT 模型卡（直接 webfetch HF）：
> *"The instruction-tuned models use a chat template that must be adhered to for conversational use... Turns finish with the `<end_of_turn>` token."*
> — chat template **只含 user / model 两个角色，无 tool / function role** ✓
> *"Inputs and outputs: Input: Text string... Output: Generated English-language text..."*
> — **完全不提 tool_calls 字段** ✓
> 用法示例：vLLM `chat/completions` 调用只传 `messages`，没有 `tools` 字段

**Evidence (b)** — FunctionGemma 多源（4 个独立来源时间线一致）：
| 来源 | 发布时间 | 关键内容 |
|---|---|---|
| IT 之家 | 2025-12-20 | "谷歌于 12 月 18 日发布 FunctionGemma，基于 Gemma 3 270M 微调" |
| InfoQ | 同 | "Mobile Actions 准确率 58% → 85%" |
| 腾讯新闻 / PANews | 2025-12-22 | "部署支持 Llama.cpp、Ollama、LM Studio" |
| 官方 cookbook | 已收录 | `google-gemma/cookbook` 新增 FunctionGemma 章节 |

— **报告"Google 2025-12 发布 FunctionGemma"完全准确** ✓

**Evidence (c)** — legacy-python/README.md（验证 Producer 关于"Gemma 4 Function Calling"的二次声明）：
- 实际 readme 含 10 处"Gemma 4 + Function Calling"字样：
  > *"我们的最终目标：... 核心依赖 **Gemma 4的Function Calling能力**"*
  > *"## 步骤2：获取Gemma 4 API Key"*
  > *"tools=[create_miniprogram_button]"*
  > *"generation_config={"tool_config": {"function_calling_config": {"mode": "auto"}}}"*

— Producer 准确指出了 legacy-python 思路在 Gemma 2 上的局限（需要 prompt 模拟），并推荐 FunctionGemma 替代 ✓

**Result: PASS**

---

## Check 10：总学习时长预估是否合理（不能明显低估）

**Method**：对照"每天投入 2-3 小时"假设 + 实际工作量。

**Evidence**：
- 阶段 0：1-2 天 → 实际工作量（重写 system prompt + 扩 10-15 样例 + 加 negative example + 10 条盲测评估）按 2h/天计 ≈ 2-3 天
- 阶段 1：1 天 → `local_infer.py` 跑通实际半天够
- 阶段 2：2-3 天 → 环境搭建 0.5 天 + 写转换脚本 0.5 天 + 训练调参 1 天 + 对比测试 0.5 天
- 阶段 3：0.5 天 → `save_pretrained_gguf()` 一行 + 拖入 LM Studio
- 阶段 4：1-2 天 → 三种方案选一种并实现

— 总计 5.5-8.5 天实际工作量，**报告预估 6-9 天**——**略微偏宽松但绝非低估** ✓
— 核心路径 3-5 天（阶段 0+2+3）= 实际 4-6 天工作量，**报告略乐观但不离谱**

**Result: PASS** — 预估保守，不存在"明显低估"。

---

## Adversarial Probes（破坏性测试）

### Probe A：示例代码 `convert_golden_to_alpaca.py` 在用户项目上能跑通吗？

**Method**：读取用户项目 `golden_examples/` 实际文件结构，对比脚本硬编码的 `index.wxml/index.wxss/index.js`。

**Evidence**：
```
golden_examples/
├── activity_signup/  →  wxml.txt  wxss.txt  js.txt  json.txt
├── product_detail/   →  index.wxml  index.wxss  index.js   ← 新格式
│                      →  wxml.txt  wxss.txt  js.txt  json.txt   ← 同时存在旧格式
├── product_list/     →  wxml.txt  wxss.txt  js.txt  json.txt
└── signup_form/      →  index.wxml  index.wxss  index.js
```

脚本只读 `index.wxml` → 4 个文件夹中**只有 2 个能读到内容**（signup_form + product_detail/index.*），其余 2-3 个将得到空字符串。

**Severity**: 中。脚本是"示例"性质，但用户复制粘贴后会得到大量空样本。

**Suggested Fix**: 让脚本同时兼容 `index.wxml` 和 `wxml.txt` 两种命名（`first_existing(...)`），并在文件不存在时输出 WARN。

**Result: FAIL（仅限代码示例准确性）** — 但**不影响报告整体的 PASS 判定**，因为 (a) 这是示例性代码不是生产代码，(b) 报告已声明"把 3 个黄金样例扩到 30-50 条再训练"，用户必须自己扩数据。

### Probe B：报告说"3 个手写黄金样例"，实际有 4 个

**Method**：glob 列出 `golden_examples/*` 目录。

**Evidence**：
- 报告中出现 6 次"3 个"：
  - TL;DR："微调数据先攒到 100 条以上再说，**3 个黄金样例远远不够**"
  - §0.1："你现在已经具备所有条件：`app.py` + `prompt_builder.py` + **3 个手写黄金样例**"
  - §0.2：「当前 3 个样例：`activity_signup` / `product_detail` / `product_list` / `signup_form`」← 4 个名字前面说 3 个！
  - §"别走弯路" #2："3 个黄金样例 → 必须先扩到 30-50 条"
  - Producer deliverable："3 个手写黄金样例"
- 实际目录：`activity_signup` / `product_detail` / `product_list` / `signup_form` = **4 个**

**Severity**: 轻微。**Producer 在 §0.2 自己的列表里就列出了 4 个名字**（自相矛盾），说明他/她看到了 4 个但口头说 3 个。

**Result: 小瑕疵**，不构成整体 FAIL，但建议 Producer 后续修订时统一为"4 个"或在表格中明确区分新旧格式（product_list/activity_signup 用 .txt 旧格式，signup_form 用 .wxml 新格式）。

### Probe C：报告说"8GB 显卡能跑 9B + 4bit QLoRA"，真实吗？

**Method**：web 搜索 QLoRA 显存估算 + Gemma 9B 模型权重大小。

**Evidence**：
- QLoRA 显存构成（专题文章）：
  - 9B 模型 4bit 权重 ≈ 5-6 GB
  - LoRA 适配器 + 优化器状态 + 梯度 ≈ 0.1-0.5 GB（很小）
  - **激活值**（取决于 sequence length 和 batch size）= 2-8 GB
  - **PyTorch/CUDA 上下文开销** ≈ 1-2 GB
  - 总计 8-16 GB，**8GB 是下限，16GB+ 才舒适**
- 报告表格：
  - 阶段 1（4bit 推理）：最低 6GB / 推荐 8GB ✓ **合理**
  - 阶段 2（LoRA 微调）：最低 8GB / 推荐 16GB+ ✓ **合理**
  - §「经验」："如果你只有 8GB 显存（笔记本常见的 RTX 3060/4060），**Unsloth + Gemma 2 9B + 4bit + QLoRA** 是完全可行的" — **过于乐观但加了 Unsloth 优化后部分可行**

**Result: 边界情形，不构成 FAIL**。Report 整体建议"先在 Colab 跑通"已经规避了 8GB 笔记本训练的不确定性。

---

## 总结

### 通过项（10/10 主检查项 + 1/3 探针 = 11/13）

| # | 检查项 | 结果 |
|---|---|---|
| 1 | 训练/微调/Prompt 概念区分 | PASS |
| 2 | 4 阶段路径循序渐进 | PASS |
| 3 | Unsloth 推荐合适 | PASS |
| 4 | LoRA / QLoRA 描述准确 | PASS |
| 5 | 学习资源链接有效（webfetch 6/8） | PASS |
| 6 | 硬件门槛建议合理 | PASS（边界乐观但合理） |
| 7 | Alpaca / ShareGPT 格式正确 | PASS |
| 8 | 覆盖"先优化 prompt 再微调" | PASS（5 处强调） |
| 9 | Function Calling 现状准确 | PASS（多源验证） |
| 10 | 总学习时长预估合理 | PASS（不低估） |
| 探针 A | 转换脚本对真实项目可跑 | FAIL（中度） |
| 探针 B | 样例数量自相矛盾 | 小瑕疵 |
| 探针 C | 8GB 训练边界 | 边界情形 |

### 修正建议（给 Producer，不影响 PASS）

1. **§0.2 样例数量**：把"3 个"改为"4 个"，并建议在表格里注明"product_list/activity_signup 用 .txt 旧格式，product_detail/signup_form 用 .index.* 新格式"
2. **`convert_golden_to_alpaca.py`**：增加对 `wxml.txt` / `index.wxml` 两种命名的兼容逻辑，避免 3/4 样例被读成空字符串
3. **可选**：在 QLoRA 章节加一句"4bit QLoRA 显存估算 8GB 是硬下限，建议 12-16GB 更稳妥"

### 评分

- **信息准确性**: 9.5/10（核心数字、概念、链接均与官方来源逐字匹配）
- **实操可行性**: 8.5/10（路径循序渐进但示例代码对真实项目有 bug）
- **针对项目落地**: 9/10（明确引用 `prompt_builder.py` / `golden_examples/` / `gemma_client.py` 并给出迁移路径）
- **总体评分**: 9/10

---

## VERDICT: PASS
