# 研究 3：Gemma 小白入门训练 / 微调 / 配置路径

> 适用对象：完全没接触过模型训练，正在做「微信小程序代码生成器」(自然语言 → WXML/WXSS/JS) 的开发者。
> 当前环境：本地 Gemma 2 + LM Studio + 3 个手写黄金样例。
> 报告目标：用「最少时间 + 最低成本 + 最少踩坑」的方式，把 Gemma 从「能跑」升级到「能生成你想要的小程序代码」。

---

## TL;DR

- **先不要碰训练**。把 `prompt_builder.py` 的 system prompt + few-shot 玩透（阶段 0），通常就能拿到 60% 以上的体验提升。
- 真要改模型权重的话，走 **Unsloth + LoRA + 4bit 量化** 是 2025-2026 年小白性价比最高的选择：免费 Colab T4 就能跑 Gemma 2 9B。
- **微调数据先攒到 100 条以上**再说，3 个黄金样例远远不够。
- 跑通后导出 **GGUF** 回到 **LM Studio / Ollama** 继续用，复用现有 `gemma_client.py`（只改 URL 即可）。
- 关于 Function Calling：**原版 Gemma 2 没有原生 tool use**，要么用 prompt 模拟，要么换 Google 新出的 **FunctionGemma**（基于 Gemma 3 270M）或直接用 Gemini API。

---

## 1. 心智模型建立 — 训练 / 微调 / Prompt Engineering 的区别

先用 3 个比喻帮小白建立直觉：

| 概念 | 比喻 | 做什么 | 成本 | 适合谁 |
| --- | --- | --- | --- | --- |
| **Prompt Engineering** | 像给新员工发「岗位说明书 + 工作范例」 | 不改模型，只改输入 | 零成本，5 分钟见效 | **所有人先做** |
| **微调 (Fine-tune / LoRA)** | 像给员工做「3 天岗前培训」 | 用几十~几百条数据小幅调整模型权重 | 需要 GPU，2-3 天 | 数据已经攒够几十条 |
| **从头训练** | 像从小学读到博士培养一个人 | 改动全部参数 | 几十万到几百万人民币 | 99% 的场景不需要 |

> 💡 经验法则：能靠 prompt 解决的就不要微调；能微调的就不要从头训。
> 你目前的需求（小程序代码生成）属于「**特定领域格式输出**」——优先顺序应该是：**Prompt > RAG 喂样例 > LoRA 微调**。

---

## 阶段 0：先把 Prompt 玩明白（零门槛，预计 1-2 天）

### 目标
不装任何新东西，不花一分钱，只改 `prompt_builder.py` 和 `golden_examples/`，让生成质量立刻上台阶。

### 为什么先做这一步
1. **所有公开 benchmark 都显示**：在结构化代码生成任务上，精心设计的 few-shot prompt 往往能达到 80% 微调的效果。
2. 你现在已经具备所有条件：`app.py` + `prompt_builder.py` + 3 个手写黄金样例，缺的只是「有意识地迭代」。

### 具体练习

#### 练习 0.1 — 把 system prompt 当 API 文档写
打开 `prompt_builder.py` 顶部的 `SYSTEM_PROMPT`，回答下面 5 个问题：
1. 模型应该扮演什么角色？（✅ 已写：「微信小程序页面源码生成器」）
2. 输出格式的契约是什么？（✅ 已写：===WXML=== / ===WXSS=== / ===JS=== 三段式）
3. 必须用什么 / 禁止用什么？（✅ 已写：组件白名单、禁止 HTML 标签、禁止真机 API）
4. 风格基调是什么？（✅ 已写：现代设计感 + 必须用原子类）
5. 边界情况怎么办？（❌ **没写** — 比如：用户需求太模糊怎么办？需要追问还是直接给默认方案？）

> 建议补一条：「如果用户需求模糊（例如只说『帮我做个页面』），请主动假设是「**电商商品详情页**」场景并直接生成，但要在 JS 注释里写明你的假设。」

#### 练习 0.2 — 把 3 个黄金样例扩到 10-15 个
当前 3 个样例：`activity_signup` / `product_detail` / `product_list` / `signup_form`。
再加 5-10 个高频场景：登录页、个人中心、订单列表、搜索结果、聊天 IM、设置页、抽奖活动、地图定位、优惠券列表、商品分类。
每个新样例要遵循同一套三段式（`index.wxml` + `index.wxss` + `index.js`），并放到 `golden_examples/<场景名>/` 目录下。
然后在 `prompt_builder.py` 里根据用户输入的**关键词**动态挑选 1-2 个最相关的 few-shot（不是把所有都塞进去，会撑爆 context）。

#### 练习 0.3 — 引入「Negative Example」
在 prompt 里加一个「反例」段落，告诉模型「不要这样写」：

```text
【错误示范（不要这样写）】
===WXML===
<div class="container">  <!-- ❌ 用了 div，应该用 view -->
  <p>价格 {{price.toFixed(2)}}</p>  <!-- ❌ 在 Mustache 里调了函数 -->
</div>
```

Negative example 比 positive example 更能让模型避免常见错误。

### 关键产出
- 一份能进 git 的 `prompt_builder.py`（v2 版本）
- 10-15 个黄金样例
- 一个简单的「需求 → few-shot 选取」映射表

### 验收标准
跑 `streamlit run app.py`，对 10 个真实需求做「盲测」：输出能直接用 / 微调后能用 / 必须返工。如果 80% 都是「直接能用」，就可以考虑进阶段 1。

---

## 阶段 1：Hugging Face Transformers 跑通本地推理（1-2 天）

### 目标
绕开 LM Studio，用 Python 代码直接加载 Gemma 2 9B-IT，跑一次最小推理。**为阶段 2 的微调打基础**（微调脚本和推理脚本用同一套 API）。

### 环境配置

```bash
# 推荐 Python 3.10-3.11
python -m venv gemma_env
source gemma_env/bin/activate          # Windows: gemma_env\Scripts\activate

pip install --upgrade pip
pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu118
pip install transformers accelerate sentencepiece bitsandbytes
```

> **必读**：Gemma 模型在 Hugging Face 上有「点击同意许可证」门槛。访问 https://huggingface.co/google/gemma-2-9b-it 用你的 HF 账号点同意，然后 `huggingface-cli login` 粘贴 token。

### 最小推理脚本 `local_infer.py`

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

model_id = "google/gemma-2-9b-it"

# 4bit 量化：把 18GB 的 bf16 模型压到约 6GB，普通 8GB 显卡就能跑
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quant_config,
    device_map="auto",
    attn_implementation="sdpa",   # 显存不够就改成 "eager"
)

# 用 chat template 把 system + user 包成模型期望的格式
messages = [
    {"role": "user", "content": "用一句话介绍杭州。"},
]
inputs = tokenizer.apply_chat_template(
    messages, return_tensors="pt", return_dict=True, add_generation_prompt=True
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=200, do_sample=False)
print(tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True))
```

跑通后你就解锁了：
- 怎么下载模型
- 怎么用 4bit 量化省显存
- 怎么用 chat template（`apply_chat_template`）
- 怎么生成文本

### 关键产出
一个能独立运行的 `local_infer.py`，打印出 Gemma 2 9B-IT 生成的回复。

### 验收
能跑出和 LM Studio 相似质量的回复，耗时 ≤ 5 秒。

---

## 阶段 2：Unsloth + LoRA 微调（2-3 天）⭐ 推荐路线

### 为什么选 Unsloth
| 维度 | 原生 PEFT | Unsloth |
| --- | --- | --- |
| 训练速度 | 1x | **2x 更快** |
| 显存占用 | Gemma-2B 14GB | **Gemma-2B 4.3GB** |
| 安装难度 | 中 | 中（但官方一条命令搞定） |
| 导出 GGUF | 需另写脚本 | **一行 `model.save_pretrained_gguf()`** |
| 适配 GPU | 通用 | **A100 / RTX 30/40/50 系列深度优化** |

Unsloth 官方 GitHub: <https://github.com/unslothai/unsloth>（65.8K stars，2025 年仍在高频更新）。它的「独家配方」`unsloth[cu118-ampere-torch240]` 已经把 flash-attn 编译好的 wheel 一起打包，避开 90% 的安装坑。

### 微调数据准备

#### 格式选择
你做的是「单轮输入→三段式输出」的结构化任务 → 用 **Alpaca 格式**最简单：

```json
[
  {
    "instruction": "生成一个带渐变头部的活动报名表单",
    "input": "",
    "output": "===WXML===\n<view class=\"container\">...</view>\n===WXSS===\n.container { ... }\n===JS===\nPage({ data: {}, onLoad() {} })"
  },
  {
    "instruction": "生成一个商品详情页，要求深色模式",
    "input": "",
    "output": "===WXML===\n..."
  }
]
```

> 字段含义：`instruction` 必填（用户需求）；`input` 选填（额外上下文）；`output` 必填（期望输出）；`system` 选填（覆盖默认 system prompt）。
> 如果以后想做多轮「先给代码 → 再改样式」对话，改用 **ShareGPT 格式**（`from: human/gpt` 交替）。

#### 把现有 `golden_examples/` 转成 Alpaca
写个一次性脚本 `convert_golden_to_alpaca.py`：

```python
import json, pathlib

ROOT = pathlib.Path("golden_examples")
samples = []

for folder in ROOT.iterdir():
    if not folder.is_dir(): continue
    wxml = (folder / "index.wxml").read_text(encoding="utf-8") if (folder / "index.wxml").exists() else ""
    wxss = (folder / "index.wxss").read_text(encoding="utf-8") if (folder / "index.wxss").exists() else ""
    js   = (folder / "index.js"  ).read_text(encoding="utf-8") if (folder / "index.js"  ).exists() else ""

    samples.append({
        "instruction": f"生成一个{folder.name}类型的微信小程序页面",
        "input": "",
        "output": f"===WXML===\n{wxml}\n===WXSS===\n{wxss}\n===JS===\n{js}",
    })

pathlib.Path("train.json").write_text(json.dumps(samples, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {len(samples)} samples to train.json")
```

3 个样例太少，**至少手动扩到 30-50 条**再开始训练，否则模型只会「死记硬背」你的样例，泛化能力很差。

### 微调脚本 `train_lora.py`（基于 Unsloth 官方模板）

```python
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

max_seq_length = 2048
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name    = "unsloth/gemma-2-9b-it-bnb-4bit",   # 已预量化版本
    max_seq_length = max_seq_length,
    dtype          = None,
    load_in_4bit   = True,
)

# 注入 LoRA 适配器
model = FastLanguageModel.get_peft_model(
    model,
    r              = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha     = 16,
    lora_dropout   = 0,
    bias           = "none",
    use_gradient_checkpointing = "unsloth",
)

dataset = load_dataset("json", data_files="train.json", split="train")

trainer = SFTTrainer(
    model            = model,
    tokenizer        = tokenizer,
    train_dataset    = dataset,
    dataset_text_field = "text",
    max_seq_length   = max_seq_length,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps        = 10,
        max_steps           = 60,           # 50 条数据大概 60 步就够了
        learning_rate       = 2e-4,
        fp16                = not torch.cuda.is_bfloat16_supported(),
        bf16                = torch.cuda.is_bfloat16_supported(),
        logging_steps       = 1,
        output_dir          = "outputs",
        optim               = "adamw_8bit",
        seed                = 0,
    ),
)
trainer.train()
```

> **零成本起步**：直接用 [Unsloth 官方 Colab Notebook](https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Gemma2_\(9B\)-Alpaca.ipynb)，免费 T4 就能跑 Gemma 2 9B，不需要本地显卡。

### 关键产出
- `outputs/` 文件夹里的 LoRA adapter（几十 MB）
- 训练 loss 曲线截图
- 同一个测试 prompt 微调前 vs 微调后的输出对比

### 验收
在「训练集没出现过」的新需求上（比如「生成一个抽奖转盘页面」），模型输出格式正确、用了你训练集里的原子类，**没有出现 HTML 标签**等老问题。

---

## 阶段 3：把微调后的模型导回 LM Studio / Ollama（0.5 天）

训练完只是开始，要把它塞回你现在用的 `gemma_client.py` 才算闭环。

### 导出 GGUF（给 LM Studio 用）
Unsloth 一行命令：

```python
# 接上阶段 2 的 trainer.train() 之后
model.save_pretrained_gguf(
    "gemma2-miniprogram-gguf",
    tokenizer,
    quantization_method = "q4_k_m",   # 平衡体积和质量的甜点档
)
```

导完会得到一个 `gemma2-miniprogram-gguf.Q4_K_M.gguf` 文件（4-5GB）。

### 在 LM Studio 里加载
1. 打开 LM Studio → 「My Models」 → 把 `.gguf` 拖进去
2. 启动 Local Server，默认还在 `http://localhost:1234/v1`
3. 你的 `gemma_client.py` **完全不用改**，继续走原来的 LM Studio 路径

### 或者用 Ollama（更轻量）

```bash
# 创建 Modelfile
cat > Modelfile <<'EOF'
FROM ./gemma2-miniprogram-gguf.Q4_K_M.gguf
SYSTEM """你是微信小程序页面源码生成器 ..."""
EOF

ollama create gemma-miniprogram -f Modelfile
ollama serve   # 默认监听 11434
```

然后改 `gemma_client.py` 里的 `local_url` 为 `http://localhost:11434/v1/chat/completions`，模型名改成 `gemma-miniprogram`。

### 验收
`streamlit run app.py` → 输入测试需求 → 输出和 LM Studio 原始 Gemma 一致，但带上了你微调后的「味道」（比如更爱用你定义的原子类）。

---

## 阶段 4：Function Calling / Tool Use（可选进阶，1-2 天）

> 对应 `legacy-python\README.md` 里「Gemma 4 Function Calling」那一段思路。

### 残酷现实
- **Gemma 2 9B-IT 原生不支持 OpenAI 风格的 tool use**（没有 chat template 内置的 `tool_calls` 字段）。
- Gemma 2 也没有官方文档教你用它的 `tools` 参数。
- 但好消息：**Google 已经发布 `FunctionGemma`**（基于 Gemma 3 270M 专用微调），专门做端侧函数调用，2025-12 发布（见 [Google AI Gemma 文档](https://ai.google.dev/gemma/docs/functiongemma)）。

### 三种解决方案（推荐顺序）

#### 方案 A：保持 Gemma 2 + 用 prompt 模拟（零成本，最简单）
你已经在用的 `miniprogram_tools.py` 思路。**把 system prompt 改成**：

```text
你是一个会调用工具的 AI Agent。
当用户要生成组件时，输出形如：
<tool_call>
{"name": "create_button", "arguments": {"text": "提交", "class": "btn-primary"}}
</tool_call>

可用工具列表：
- create_button(text, class)
- create_input(name, placeholder, type)
- create_card(title, body)
... (写 5-10 个就够覆盖 90% 场景)
```

然后在 Python 端用正则解析 `<tool_call>...</tool_call>` 并调用对应函数生成代码，**把结果再塞给 Gemma 让它继续**。这种 ReAct 模式在结构化任务上效果出奇地好。

#### 方案 B：换成 FunctionGemma（如果你的硬件能跑 270M）
[FunctionGemma](https://ai.google.dev/gemma/docs/functiongemma) 是 Gemma 3 270M 微调的函数调用专用模型。它能直接输出标准 `function_call` JSON。代价是 270M 容量小、文案生成能力弱，需要搭配一个 Gemma 2/3 做「意图理解 + 文案润色」+ FunctionGemma 做「结构化调用」的两段式流水线。

#### 方案 C：直接换 Gemini API（最快，零部署）
Google Gemini 2.5 Flash 原生支持 function calling，调用方式和 OpenAI 几乎一样：

```python
import google.generativeai as genai
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    tools=[create_button, create_input, create_card],   # 直接传 Python 函数
)
```

你 `gemma_client.py` 里的 Gemini 兜底分支其实已经走这个 API 路径了——**只要把降级逻辑改成「主用 Gemini 跑 function calling」就完事了**。云端按 token 计费，但生成小程序代码的量级一个月也就几块钱。

### 关键产出
- 选 A：一份带工具描述的 system prompt + 一个 `tool_call_parser.py`
- 选 B：一个两段式推理管线
- 选 C：把 `gemma_client.py` 里的 Gemini 路径提到主路径

---

## 硬件门槛提示

| 阶段 | 最低显存 | 推荐显存 | 速度参考 | 云端替代 |
| --- | --- | --- | --- | --- |
| **阶段 0（纯 prompt）** | 无（CPU 即可） | — | — | 不需要 |
| **阶段 1（4bit 推理）** | 6 GB | 8 GB | 5-10 tok/s | Google Colab 免费 T4 |
| **阶段 2（LoRA 微调）** | 8 GB | 16 GB+ | 30-60 分钟跑 50 条数据 | Colab 免费 T4 / Kaggle 双卡 T4 / AutoDL 3090 2 元/小时 |
| **阶段 3（GGUF 导出）** | 8 GB | — | 5 分钟 | 直接在 Colab 里跑 |
| **阶段 4（Function Calling）** | 同上 | 同上 | — | Colab / Gemini API |

> 经验：如果你只有 8GB 显存（笔记本常见的 RTX 3060/4060），**Unsloth + Gemma 2 9B + 4bit + QLoRA** 是完全可行的，不需要换更小的 2B 模型。

---

## 推荐学习资源

按「打开频率」从高到低排：

1. **Hugging Face Transformers 官方 Gemma 文档**（必读） — <https://huggingface.co/docs/transformers/main/en/model_doc/gemma>
2. **Unsloth 官方文档**（必读） — <https://docs.unsloth.ai/>
3. **Unsloth GitHub**（含一键安装命令） — <https://github.com/unslothai/unsloth>
4. **Hugging Face PEFT 库**（理解 LoRA 原理） — <https://huggingface.co/docs/peft/main/en/index>
5. **Google AI Gemma Cookbook**（官方 Notebook 集合） — <https://github.com/google-gemma/cookbook>（注意：旧的 `google-gemini/gemma-cookbook` 已废弃，重定向到新地址）
6. **LoRA 原论文科普**（一文读懂 LoRA 是什么） — <https://arxiv.org/abs/2106.09685>
7. **Unsloth Gemma 2 免费 Colab**（零成本跑通微调） — <https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Gemma2_\(9B\)-Alpaca.ipynb>
8. **FunctionGemma 介绍**（如果你要 tool use） — <https://ai.google.dev/gemma/docs/functiongemma>
9. **Hugging Face Gemma 2 9B-IT 模型卡**（含 chat template、bitsandbytes 推理代码） — <https://huggingface.co/google/gemma-2-9b-it>

---

## 别走弯路 — 给小白的 7 条铁律

1. **不要一上来就训练**。80% 的「模型不够好」是 prompt 没写好。**阶段 0 至少跑 2 天再考虑训练**。
2. **数据不够不要微调**。少于 100 条高质量样本，微调出来的模型只会「死记硬背」。3 个黄金样例 → 必须先扩到 30-50 条。
3. **数据质量 > 数据数量**。30 条格式完全正确、风格统一的样本，比 300 条乱写的样本有用得多。
4. **优先用 9B，不要用 2B**。Gemma 2 9B-IT 在代码任务上明显强于 2B，且 4bit 量化后只有 6GB，8GB 显卡能跑。
5. **别混用 Unsloth 和原生 PEFT**。两套 LoRA 实现机制不同，混用会梯度错乱。**选一个，贯彻到底**。
6. **先在 Colab 上跑通再考虑本地**。Colab 免费 T4 足够学习用，避开本地环境配置的所有坑。
7. **微调完一定要做「留出集测试」**。训练集里没出现过的需求才真正考验泛化能力。

---

## 推荐学习路径 & 预计总时长

按你**完全没有经验**的前提，最稳的路线是：

```
阶段 0（prompt 优化）    1-2 天    ← 必做，能立刻见效
   ↓
阶段 1（Transformers 推理）  1 天   ← 理解模型 API
   ↓
阶段 2（Unsloth LoRA 微调）  2-3 天  ← 核心技能
   ↓
阶段 3（导出 GGUF 回 LM Studio） 0.5 天  ← 闭环
   ↓
阶段 4（Function Calling）  1-2 天   ← 可选，看你需求
```

**总学习时长：6-9 天**（按每天投入 2-3 小时计算）。

> 如果时间紧只想跑通最核心的：阶段 0 + 阶段 2 + 阶段 3 = **3-5 天**。其它都是锦上添花。

---

## 参考链接（已验证可用）

- [Hugging Face Gemma 文档](https://huggingface.co/docs/transformers/main/en/model_doc/gemma) — Gemma 推理 + Transformers 完整 API
- [Unsloth 官方文档](https://docs.unsloth.ai/) — 微调框架首选
- [Unsloth GitHub 仓库](https://github.com/unslothai/unsloth) — 65.8K stars，活跃维护
- [Hugging Face Gemma 2 9B-IT 模型卡](https://huggingface.co/google/gemma-2-9b-it) — 包含 chat template、bitsandbytes 推理代码
- [Hugging Face PEFT 库](https://huggingface.co/docs/peft/main/en/index) — LoRA 原理与 API
- [Google Gemma Cookbook](https://github.com/google-gemma/cookbook) — 官方 Notebook 集
- [LoRA 原论文](https://arxiv.org/abs/2106.09685) — 理解低秩适配的本质
- [FunctionGemma 介绍](https://ai.google.dev/gemma/docs/functiongemma) — Google 2025-12 发布的函数调用专用模型
- [Unsloth Gemma 2 Alpaca Colab](https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Gemma2_\(9B\)-Alpaca.ipynb) — 零成本跑通微调

---

## 推荐下一步

1. **今天就做**：把 `SYSTEM_PROMPT` 按阶段 0 的 5 问清单重写一遍，跑 10 条测试看效果。
2. **本周完成**：把 3 个黄金样例扩到 10-15 个，加入 negative example。
3. **下周尝试**：按阶段 1-2 跑通一次完整微调，哪怕只跑 30 步看 loss 曲线。
4. **可选项**：如果发现「模型总是不按格式输出」而不是「输出质量差」，那是 prompt 问题不是微调问题，**回到阶段 0**。
