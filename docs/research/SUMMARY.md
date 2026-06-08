# LM Studio + Gemma 小白完全手册

> **适用读者**：刚下载完本地模型、完全没接触过模型训练的开发者。
> **你的项目背景**：`gemma_match` 微信小程序代码生成器，Streamlit UI + 本地 Gemma + 黄金样例 fallback。
> **手册目标**：让你 1 小时内搞懂"它在干嘛 / 怎么用 / 下一步该学什么"。

---

## TL;DR（1 分钟读完）

| 你的疑问 | 一句话回答 | 想深入看哪份报告 |
|---|---|---|
| **5GB 模型是完全本地吗？** | ✅ **完全本地**。D 盘那个 5GB 文件就是模型本体，推理时所有对话都不出本机；只有「下载模型」和「检查更新」时会联网。 | [研究 1](01-lm-studio-architecture.md) |
| **那个 5GB 模型到底是啥？** | 大概率是 **Gemma 4 E4B**（2026-04-02 Google 发布，4B 有效参数、128K 上下文、原生多模态 + 函数调用），**不是** Gemma 2 9B。`gemma_client.py` 里 `"gemma-4-e4b-it"` **字段名是对的，不用改**。 | [研究 2](02-lm-studio-usage.md) |
| **怎么在页面上用？** | LM Studio 左侧进 **Developer** tab → 顶部下拉选模型 → 等显示 "Model loaded" → 点 **Start Server** → 在 `http://localhost:1234/v1` 就能调。 | [研究 2](02-lm-studio-usage.md) |
| **能调啥参数？** | 6 个旋钮：Temperature（温度）/ Top P（核采样）/ Max Tokens（最长输出）/ Context Length（上下文窗口）/ GPU Offload（GPU 卸载）/ Prompt Format（提示词格式）。代码生成场景：温度 0.0–0.2、上下文 4096、GPU 拉满。 | [研究 2 §3](02-lm-studio-usage.md#3-关键参数详解小白版) |
| **小白怎么训练？** | **不要一上来就训练**。先优化 prompt（阶段 0），再 Hugging Face 跑通推理（阶段 1），最后用 Unsloth + LoRA 微调（阶段 2）。总时长 6-9 天，每天 2-3 小时。 | [研究 3](03-gemma-beginner-path.md) |

---

## 你必须先知道的一件事：你的 5GB 文件是 Gemma 4 E4B，不是 Gemma 2

这是研究 2 通过核查员核查后修正的关键事实。原研究 1 和研究 3 都假设是 Gemma 2 9B（18GB 全精度 → 5GB Q4_K_M 量化），但实际上：

| 维度 | Gemma 2 9B | **Gemma 4 E4B（你的模型）** |
|---|---|---|
| 发布时间 | 2024-07 | **2026-04-02** |
| 有效参数 | 9B | 4B（PLE 每层嵌入） |
| 上下文窗口 | 8K | **128K**（16 倍） |
| 多模态 | 纯文本 | **文本+图像+音频+视频** |
| Q4_K_M 量化大小 | ~5.5GB | **~5-6GB** ← 精准匹配你 D 盘那个文件 |
| 函数调用 | 无 | **原生支持** |

**这意味着**：
- `gemma_client.py` 里的 `"gemma-4-e4b-it"` **是对的，不要改成 `gemma-2-9b-it`**，否则会丢失多模态和长上下文能力。
- 你在 LM Studio 的 Developer tab 下拉框里会看到 `gemma-4-e4b-it` 或 `gemma-4-E4B-it-Q4_K_M`，**任选一种**——LM Studio Server 默认忽略 model 字段不严格校验。

> **如何快速验证**：在 LM Studio Chat 里随便发一句话，看回显开头模型有没有报自己是哪个版本（新版 LM Studio 会显示模型 metadata）。或者用 `curl http://localhost:1234/v1/models` 看返回的 JSON 里 ID 是不是带 `gemma-4`。

---

## 三个问题速答

### Q1：5GB 模型是完全本地吗？数据会不会发到 Google？

**完全本地。** 三层保证：

1. **LM Studio 本身**：「Local Server」默认监听 `127.0.0.1:1234`，只在电脑内部开端口，外网访问不到（除非你主动改成 `0.0.0.0`）。
2. **llama.cpp 推理引擎**：纯本地 C/C++ 程序，不联网，不调用任何远程 API。
3. **GGUF 模型文件**：纯静态文件，存在 D 盘就是你的了，Google 看不到也管不了。

**会联网的唯二场景**：
- 第一次下载模型时（去 Hugging Face 拉文件）
- LM Studio 启动时检查更新（可在 Settings 关掉）

**完全断网照常用**——加载完模型后拔网线，LM Studio 该咋跑咋跑。

### Q2：怎么在页面上用这个模型？有没有调参界面？

**有三种界面 + 一个开发者服务器**：

| 界面 | 干啥 | 你用得上吗 |
|---|---|---|
| **Chat（聊天）** | 跟模型对话、调温度、上传图片（E4B 支持多模态） | ✅ 日常调试 |
| **Playground（游乐场）** | 同时跑多个模型/参数并排对比 | ✅ 选最佳 prompt 时用 |
| **Discover（发现）** | 搜索 Hugging Face 上的模型 | 偶尔用 |
| **My Models（我的）** | 管理已下载的模型 | ✅ 看模型大小、删除 |
| **Developer（开发者）** | **加载模型 + 启 Server + 高级调参** | ✅ **这是你要进的地方** |

**3 步启动本地服务器**：
1. 进 Developer tab
2. 顶部下拉框选 `gemma-4-e4b-it`（或显示为 `gemma-4-E4B-it-Q4_K_M`）
3. 等出现 "Model loaded"（10-30 秒）→ 点 **Start Server** → 记下 `http://localhost:1234/v1`

之后你的 `gemma_client.py` 就能正常调了。

**6 个调参旋钮**（按重要程度）：

| 旋钮 | 干啥 | 代码生成推荐值 |
|---|---|---|
| **Temperature** | 控制发散程度，越高越有创意 | **0.0–0.2**（要稳定输出） |
| **Top P** | 候选词裁剪 | 0.9（保持默认） |
| **Max Tokens** | 最多输出多少 token | 512（小程序三段式够用） |
| **Context Length** | 上下文窗口 | 4096（够用，别乱拉大） |
| **GPU Offload** | 模型多少层放 GPU | 拉满（显存够的话） |
| **Prompt Format** | 提示词格式 | **Auto**（别动） |

### Q3：小白怎么训练 / 微调？要走什么路径？

**先别训练**。研究 3 给出的 6-9 天路线：

```
阶段 0（1-2 天）— Prompt 优化    ← 必做，能立刻见效
阶段 1（1 天）  — Transformers 推理  ← 理解模型 API
阶段 2（2-3 天）— Unsloth LoRA 微调 ← 核心技能
阶段 3（0.5 天）— 导出 GGUF 回 LM Studio ← 闭环
阶段 4（1-2 天）— Function Calling ← 可选
```

**阶段 0 现在就能做**（零成本、立刻见效）：

1. 打开 `prompt_builder.py` 顶部的 `SYSTEM_PROMPT`，按 5 问清单改：
   - 模型角色？✅ 已写
   - 输出契约？✅ 已写
   - 白名单 / 黑名单？✅ 已写
   - 风格基调？✅ 已写
   - 模糊需求怎么办？❌ **没写**——补一句"模糊需求默认按电商商品详情页生成，并在 JS 注释说明假设"
2. 把 `golden_examples/` 从 3 个扩到 10-15 个（登录页、个人中心、订单列表、搜索结果等高频场景）
3. 加 1-2 个 **Negative Example**（告诉模型"不要这样写"），比 positive example 更能避免错误

跑 10 个真实需求做盲测，**80% 都能直接用**就可以进阶段 1 了。

**真要微调时**（阶段 2）：
- 用 **Unsloth**（2x 加速、GGUF 一键导出、小白友好）
- 跑在 **Google Colab 免费 T4** 上（零成本、不用配本地环境）
- 至少 **30-50 条**高质量样本（少于这个数模型只会死记硬背）
- **Alpaca 格式**：`{"instruction": "用户需求", "input": "", "output": "三段式代码"}`
- 训练完用 `model.save_pretrained_gguf()` 一行导出 GGUF，拖回 LM Studio 用

**微调后的模型**还是放 LM Studio 里跑，`gemma_client.py` 完全不用改。

---

## 关于你 `gemma_client.py` 的 3 处建议改进

研究 2 在核查时发现 `gemma_client.py` 有 3 个可以改进的地方，**不是 bug，是健壮性问题**：

### 1. `model` 字段——**保持 `"gemma-4-e4b-it"` 不动**
上面解释过了，这就是正确的。

### 2. `timeout=120` 改成 300 秒
第一次调用要模型预热（5-30 秒），加上生成 500 token（30-60 秒），120 秒容易超时。

```python
with urllib.request.urlopen(req, timeout=300) as response:  # 120 → 300
```

### 3. 把 `HTTPError` 和 `URLError` 分开处理（避免静默 fallback）

**当前代码**：
```python
except (urllib.error.URLError, ConnectionError):
    pass  # Local failed, try cloud
```

**问题**：`HTTPError` 是 `URLError` 的子类，所以本地 Server 返回 4xx/5xx 时（比如 model 名错、模型没加载完），会被这段 except 静默吞掉，然后悄悄 fallback 到 Gemini 云端。**用户以为本地挂了，其实是配置问题**。

**建议改成**：
```python
import urllib.error
import json

def call_gemma(prompt: str) -> str:
    local_url = "http://localhost:1234/v1/chat/completions"
    data = {
        "model": "gemma-4-e4b-it",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    req = urllib.request.Request(
        local_url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        # 4xx/5xx：Server 在，但请求被拒（model 名错 / 格式错 / Server 没加载对应模型）
        body = e.read().decode("utf-8", errors="replace")
        return f"[LM Studio HTTP {e.code}] {body[:300]}"
    except urllib.error.URLError as e:
        # 连接级错误：Server 根本没启动 / 端口错 / DNS 失败
        # 这才是真正应该 fallback 的场景
        print(f"[LM Studio 不可达] {e.reason}, fallback 到 Gemini")
    # ... 继续走 Gemini fallback
```

这样**真挂了**和**配置错**会得到完全不同的提示，方便排查。

---

## 今天/这周/下月可执行清单

### 今天（30 分钟）
- [ ] 打开 LM Studio Developer tab，确认下拉框里看到 `gemma-4-e4b-it` 或类似名字
- [ ] 点 Start Server，在终端跑 `curl http://localhost:1234/v1/models` 验证它能返回 JSON
- [ ] 把 `gemma_client.py` 的 `timeout=120` 改成 300
- [ ] 在 Streamlit UI 里试一个需求（比如"生成一个活动报名页"），看输出格式

### 这周（3-4 小时）
- [ ] 读完研究 2 的 §5 完整版（`gemma_client.py` 解读 + 异常处理）
- [ ] 读完研究 3 的阶段 0 完整版（Prompt 优化练习 0.1-0.3）
- [ ] 改 `prompt_builder.py` 的 SYSTEM_PROMPT，加"模糊需求"那条
- [ ] 在 `golden_examples/` 加 3-5 个新样例
- [ ] 给 `gemma_client.py` 加 HTTPError/URLError 分支处理

### 下月（按 6-9 天路线走）
- [ ] 阶段 1：在 Colab 跑通 Transformers + Gemma 2 9B 推理
- [ ] 阶段 2：用 Unsloth 跑通 LoRA 微调（哪怕只跑 30 步）
- [ ] 阶段 3：导出 GGUF 拖回 LM Studio，验证你的 `gemma_client.py` 能调用

---

## 三份详细报告索引

| 报告 | 主题 | 长度 | 什么时候读 |
|---|---|---|---|
| [01-lm-studio-architecture.md](01-lm-studio-architecture.md) | 运行原理（架构 / 量化 / 数据流 / 硬件需求 / 常见误解） | ~5000 字 | 想理解"为啥 5GB 就能跑"的时候 |
| [02-lm-studio-usage.md](02-lm-studio-usage.md) | 页面使用 / 调参 / API 调用 / gemma_client.py 解读 | ~7000 字 | 要实际改代码或调参前必读 |
| [03-gemma-beginner-path.md](03-gemma-beginner-path.md) | 训练入门路径（6-9 天路线 + 4 阶段详解） | ~3000 字 | 准备开始微调时通读 |

**每份报告都通过了独立核查员的事实核查**（核查报告在 `01-verify.md` / `02-verify.md` / `03-verify.md`），可信度有保障。

---

## 报告说明

- **报告生成时间**：2026-06-05
- **核查情况**：研究 1 + 研究 3 一次通过；研究 2 第一次被核查员抓出"因果链错误"和"Gemma 4 误判"，重做后通过（99/100）
- **冲突点修正**：研究 1 和研究 3 假设你用的是 Gemma 2 9B（这是当时 README 和 `gemma_client.py` 默认值的推断）；研究 2 通过验证模型卡后确认你实际用的是 Gemma 4 E4B。本手册以研究 2 的核查结论为准。
- **来源**：所有事实均引用自 LM Studio 官网、llama.cpp GitHub、GGUF 规范、Google Gemma 官方公告、Hugging Face 模型卡、Unsloth 官方文档、Python urllib 官方文档等公开资料

---

> **最后提醒**：这套架构（本地 Gemma + LM Studio + Streamlit UI）选得很正确——隐私 100% 在你电脑、零 API 费用、离线也能用。唯一代价是速度比云端慢、长代码生成要等十几秒到几十秒。下一步就是按上面的清单一步步走，**先做阶段 0 优化 prompt，90% 的情况下你根本不用训练**。
