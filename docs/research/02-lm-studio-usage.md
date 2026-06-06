# LM Studio 页面使用 + 调参 + 接入外部应用 — 小白向操作指南

> 适用对象：刚下载完 5GB Gemma 4 E4B 模型、不知道怎么在 LM Studio 页面上用的小白用户
> 你的项目背景：`gemma_client.py` 已通过 `http://localhost:1234/v1` 调用 LM Studio 的 OpenAI 兼容 API

---

## TL;DR

- 你的 5GB 文件**大概率是 Gemma 4 E4B**（2026-04-02 Google 发布，4B 有效参数 + 128K 上下文 + 多模态，Q4_K_M 量化约 5-6GB），**不是** Gemma 2 9B。`gemma_client.py` 里的 `"gemma-4-e4b-it"` 字段名**是对的，不用改**。
- LM Studio = 「启动器 + 聊天界面 + API 服务器」三合一。装好模型后，先到 **Developer** tab 点 **Start Server**，才能在外部代码里调 `localhost:1234`。
- 三种界面分工：**Chat** 用来跟模型聊、**Playground** 用来对比多个模型、**Server** 才是给外部程序用的 API 入口。
- 调参记住 6 个旋钮：**Temperature** / **Top P** / **Max Tokens** / **Context Length** / **GPU Offload** / **Prompt Format**。
- 你 `gemma_client.py` 里的 `model: "gemma-4-e4b-it"` **就是正确的**，保持不变。LM Studio 默认会忽略 model 字段（用当前加载的模型响应），所以"model 字段名错"在小概率场景下也不崩。**真正要修的是 timeout 和静默 fallback 这两点**。
- 第一次调用要等 5–30 秒（模型预热），这是正常现象。

---

## 1. 启动 LM Studio 本地服务器（Developer → Start Server）

> 目标：让你的电脑在 `http://localhost:1234/v1` 跑起一个 OpenAI 兼容的 HTTP 接口，`gemma_client.py` 就能调它。

### 步骤 1：打开 LM Studio，左侧进 **Developer** tab

LM Studio 左侧边栏从上到下依次是：**Chat（聊天）**、**Playground（游乐场）**、**Discover（发现模型）**、**My Models（我的模型）**、**Developer（开发者）**。我们要进的是 **Developer**。

### 步骤 2：在 Developer 页顶部加载模型

- 中间顶部有个 **Model** 下拉框，选你下载的 Gemma 4 E4B（LM Studio 里可能显示为 `gemma-4-e4b-it`、`gemma-4-E4B-it-Q4_K_M` 或带命名空间的形式如 `unsloth/gemma-4-e4b-it-GGUF`）。
- 选中后，下方会自动出现模型配置参数（温度、Top P、Context Length、GPU Offload 等），先保持默认。
- 等页面状态显示 **"Model loaded"**（约 10–30 秒，加载完才能响应请求）。

### 步骤 3：点 **Start Server** 按钮

- 页面中部或右上的 **Start Server** 开关（绿色）。点一下，开关变红/显示运行中。
- 启动后，下方会出现三个关键信息，**记下来**：

  | 信息 | 作用 | 示例 |
  |---|---|---|
  | **Server URL / Endpoint** | API 根地址 | `http://localhost:1234/v1` |
  | **API Key** | 鉴权用（本地一般不校验） | `lm-studio`（默认占位符） |
  | **Port** | 端口号 | `1234`（默认） |

- LM Studio 默认监听 `127.0.0.1:1234`，**只能在**本机访问。局域网其他机器调不到，除非在 Settings 里改成 `0.0.0.0` 监听（不安全，仅限开发环境）。

### 步骤 4：快速自测 Server 是否正常

```bash
curl http://localhost:1234/v1/models
```

返回 JSON 列出已加载的模型名，说明 Server 跑起来了。

> **小贴士**：Start Server 后**不需要保持 Developer tab 开着**，LM Studio 在后台跑，关窗口也不影响 API 接收请求。

---

## 2. 三种使用界面：Chat / Playground / Server

LM Studio 左侧栏的三种「主界面」各有定位。

### 2.1 Chat（聊天）— 最常用

**界面长啥样**：左侧对话列表，中间是当前对话气泡（你的输入 + 模型的回复），右侧是「模型参数面板」和「系统提示词（System Prompt）」输入框。底部输入框支持附件（图片、PDF、音频——Gemma 4 E4B 支持多模态）。

**典型场景**：
- 跟模型闲聊，测试它能不能跑通
- 调 Temperature 看模型性格变化（冷=温度低、热情=温度高）
- 上传图片让 E4B 识别内容（多模态测试）

**何时用**：日常调试、体验模型能力、临时验证 prompt。

### 2.2 Playground（游乐场）— 横向对比

**界面长啥样**：屏幕被切成两半或四块，每块独立显示一个模型的回复。同一个 prompt 喂给多个模型，**并排对比**谁答得更好。

**典型场景**：
- 横向对比 Gemma 4 E4B 不同量化版本（Q4_K_M vs Q8_0 谁更快、谁更准）
- 对比 Gemma 4 E4B vs Qwen 2.5 在同一 prompt 下的输出
- 调参 A/B 测试（温度 0.2 vs 0.8 效果差多少）

**何时用**：选模型、调参数、批量评估输出质量。

### 2.3 Developer / Server — 给程序用的

**界面长啥样**：上面是模型加载配置（Context Length、GPU Offload、Prompt Format 等高级旋钮），下面就是 **Start Server** 开关 + 显示当前 API 端点和 API Key。

**典型场景**：
- 启动 HTTP API，让 Python / JS / curl 能调
- 改高级参数（Prompt Format、Batch Size、Flash Attention）
- 查看请求日志

**何时用**：你要把模型接入自己代码的时候（包括 `gemma_client.py`）。

> **三者的关系**：Chat 和 Playground 是「人用」的，Server 是「程序用」的。Server 启动后，前两个界面也能继续用，互不冲突。

---

## 3. 关键参数详解（小白版）

下面 6 个旋钮是你日常会动的，按重要程度排序。

### 3.1 Temperature（温度）— 控制「发散程度」

- **是什么**：决定模型选下一个字时的「冒险程度」。
- **范围**：0.0 – 2.0（默认 0.7 或 1.0）
- **怎么工作**：
  - **低（0.0 – 0.3）**：每次都选概率最高的字，回答「确定、保守、可重复」。适合事实问答、代码生成、JSON 提取。
  - **中（0.5 – 0.9）**：平衡创造性和稳定性。日常聊天的甜区。
  - **高（1.0 – 2.0）**：允许选概率低的字，回答「天马行空、可能跑偏」。适合创意写作、头脑风暴、诗歌。
- **建议值**：
  - 代码 / 提取结构化数据：**0.0 – 0.2**
  - 一般聊天 / 摘要：**0.5 – 0.7**
  - 写故事 / 起名：**0.9 – 1.3**
- **小白口诀**：要稳就低，要花就高。

### 3.2 Top P（核采样）— 「候选词表」裁剪

- **是什么**：模型选下一个字时，只在累计概率达到 P 的「头部候选词」里挑。
- **范围**：0.0 – 1.0（默认 0.95）
- **怎么工作**：
  - `top_p = 0.1`：只在概率最高的 10% 词里挑 = 几乎确定性的输出。
  - `top_p = 0.95`：在概率累计达 95% 的词里挑 = 主流选项里随机。
  - `top_p = 1.0`：考虑全部词（实际受 Temperature 影响）。
- **建议值**：日常用 **0.9 – 0.95** 就行。
- **⚠️ 官方建议**：Temperature 和 Top P **不要同时大改**——会失去对模型行为的精准控制。一般动一个就够。

### 3.3 Max Tokens（最大输出长度）— 控制「最长能说多少」

- **是什么**：单次回复最多生成多少个「token」（token ≈ 半个汉字或 0.75 个英文单词）。
- **范围**：1 到 Context Length（默认 2048 左右）
- **怎么工作**：模型生成到这个数就会**强制停止**，不管有没有写完。
- **建议值**：
  - 短回答 / 分类：**64 – 256**
  - 段落 / 邮件：**256 – 512**
  - 长文章 / 报告：**1024 – 4096**
- **⚠️ 注意**：调大这个会让单次请求**变慢且占更多显存**，别无脑拉到最大。

### 3.4 Context Length（上下文窗口）— 「能塞多少输入」

- **是什么**：模型一次能「看到」的最大 token 数（输入 + 输出加起来算）。
- **范围**：512 到模型硬上限（Gemma 4 E4B 支持 **128K**，Gemma 2 9B 只支持 8K——差 16 倍）
- **怎么工作**：
  - 上下文越大，模型能「记住」的历史对话越多、能处理的长文档越长。
  - **代价**：占显存、变慢。E4B 在 128K 上下文下需要约 12-16GB 显存。
- **建议值**：
  - 短对话：**4096 – 8192**
  - 长文档问答 / 代码库分析：**32K – 128K**（E4B 完全够用）
- **⚠️ 注意**：超过模型硬上限它会自动报错或截断。

### 3.5 GPU Offload（GPU 卸载层数）— 显存吃紧时的救命旋钮

- **是什么**：把模型多少层放到 GPU 上跑，剩余层放 CPU。
- **范围**：0（全部 CPU）到模型总层数（全部 GPU）
- **怎么工作**：
  - **全 GPU（拉满）**：速度最快，但需要大显存（5GB 模型至少 6GB 显存）。
  - **混合（推荐）**：部分层 GPU + 部分层 CPU，平衡速度和显存。
  - **全 CPU**：慢但稳，16GB 内存也能跑。
- **建议值**：
  - 有 8GB+ 显存：直接拉满。
  - 显存不够 / 报 OOM：调到总层数的 70%–80%。
  - 没有任何独显：保持 0，纯 CPU 跑（10-30 tokens/秒）。
- **小贴士**：Windows 上如果在 Hardware 页看不到显卡，需要去 Settings → Runtime 安装 CUDA 12 引擎。

### 3.6 Prompt Format（提示词格式）— ChatML / Gemma Template

- **是什么**：把「messages 数组」转成模型能理解的纯文本格式（包含 `<start_of_turn>` 这类特殊标记）。
- **常见格式**：
  - **Gemma Chat Template**：Gemma 系列官方格式，用 `<start_of_turn>user\n...<end_of_turn>` 标记
  - **ChatML**：OpenAI / Qwen 等用的格式
- **怎么工作**：LM Studio 会**根据模型自动检测**最合适的 format。**手动选错会导致模型表现下降**（把 ChatML 喂给 Gemma 模型会大幅掉质量）。
- **建议值**：**保持 Auto / 自动检测**，只在模型表现异常时手动改。
- **小白口诀**：别动这个，Auto 就好。

---

## 4. 如何在外部页面 / 程序中调用 LM Studio

LM Studio 暴露的是 **OpenAI 兼容 API**，所以任何能调 OpenAI 的工具都能无缝切过来。改的只有 `base_url` 一个参数。

### 4.1 curl（最快验证）

```bash
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-4-e4b-it",
    "messages": [
      {"role": "user", "content": "用一句话介绍 LM Studio"}
    ],
    "temperature": 0.7
  }'
```

返回 JSON 里 `choices[0].message.content` 就是模型回答。

### 4.2 Python urllib（你的项目用的方式，重点看）

`gemma_client.py` 已经在用 urllib，**零依赖**，Python 自带。三个关键点：

1. **URL**：`http://localhost:1234/v1/chat/completions`
2. **method**：必须是 `POST`（不是 GET）
3. **headers**：`Content-Type: application/json`
4. **body**：用 `json.dumps()` 序列化后 `.encode('utf-8')`

完整可运行示例：

```python
import urllib.request
import urllib.error
import json

def call_lm_studio(prompt: str) -> str:
    url = "http://localhost:1234/v1/chat/completions"
    payload = {
        "model": "gemma-4-e4b-it",          # ← 写 LM Studio 下拉框里显示的 ID
        "messages": [
            {"role": "system", "content": "你是一个简洁的助手，回答不超过50字。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 256
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            return f"[API 返回异常] {result}"
    except urllib.error.HTTPError as e:
        # 4xx/5xx 时会到这里：e.code / e.reason / e.read() 可读
        body = e.read().decode("utf-8", errors="replace")
        return f"[HTTP {e.code}] {e.reason} | body={body[:200]}"
    except urllib.error.URLError as e:
        return f"[网络错误] {e.reason}"

print(call_lm_studio("什么是大模型？"))
```

> **⚠️ 关键点**：`"model"` 字段填的不是文件名，而是 **LM Studio Developer tab 顶部下拉框显示的「模型标识」**。打开 Developer tab，鼠标悬停模型名会显示完整 ID。LM Studio Server 通常**不严格校验** model 字段——即使填错也经常能响应（用当前加载的模型返回结果），但**填对**能保证你调的是想要的模型。

### 4.3 OpenAI Python SDK（最省事）

```bash
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",   # 唯一改的就是这行
    api_key="lm-studio"                    # 随便填，LM Studio 本地不校验
)

resp = client.chat.completions.create(
    model="gemma-4-e4b-it",
    messages=[{"role": "user", "content": "你好"}],
    temperature=0.7
)
print(resp.choices[0].message.content)
```

> **优势**：自动重试、流式输出、tool calling 都是开箱即用。

---

## 5. 接入你的 `gemma_client.py`（解读本地调用逻辑）

读了一下 `gemma_client.py`，逻辑是：**先试本地 LM Studio，失败再 fallback 到 Gemini 云端**。重点解读第 11–33 行。

### 5.1 关键代码段回顾

```python
# gemma_client.py:11-19
local_url = "http://localhost:1234/v1/chat/completions"
data = {
    "model": "gemma-4-e4b-it",   # ← 这个 model 名是**对的**！
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7
}
```

### 5.2 三处需要核对的点

#### 点 1（重要）：`model` 字段 — **保持 `"gemma-4-e4b-it"` 不动**

**你的 5GB 文件**大概率是 **Gemma 4 E4B**，不是 Gemma 2 9B。理由：

| 维度 | Gemma 2 9B | Gemma 4 E4B（你的模型） |
|---|---|---|
| 发布时间 | 2024-07 | **2026-04-02** |
| 有效参数 | 9B | 4B（PLE 每层嵌入技术） |
| 总参数 | 9B | ~8B（4B 激活） |
| 上下文窗口 | 8K | **128K**（16 倍于 Gemma 2 9B） |
| 多模态 | 纯文本 | **文本+图像+视频+音频** |
| Q4_K_M 量化大小 | ~5.5GB | **~5-6GB** ← 精准匹配 5GB |
| 函数调用 | 无 | **原生支持** |

**结论**：
- `gemma_client.py` 里写的 `"gemma-4-e4b-it"` **是正确的**，对应 Google DeepMind 2026-04-02 发布的 Gemma 4 E4B。
- LM Studio 下拉框里可能显示为 `gemma-4-e4b-it`、`gemma-4-E4B-it-Q4_K_M`、`unsloth/gemma-4-e4b-it-GGUF` 等不同形式，**任一种都行**——Server 通常不严格校验 model 字段。
- **不要**把它改成 `gemma-2-9b-it`！那会让你损失多模态能力（无法识别图片/音频）且上下文窗口从 128K 降到 8K。

#### 点 2：超时时间 — 120 秒可能不够

`urlopen(req, timeout=120)` 给的是 120 秒。**第一次调用**模型预热要 5–30 秒，加上生成 500 token 大约再 30–60 秒。如果是长输入 + 长输出，可能超时。**建议改成 300 秒**：

```python
with urllib.request.urlopen(req, timeout=300) as response:
```

#### 点 3（关键）：fallback 静默吞错的真实机制

你的 `gemma_client.py:32-33`：

```python
except (urllib.error.URLError, ConnectionError):
    pass # Local failed, try cloud
```

**这段代码的因果链是这样的**（Python 3 的真实行为）：

1. `urllib.error.HTTPError` **是** `urllib.error.URLError` 的**子类**（类层级：HTTPError → URLError → OSError）。
2. 当 Server 返回 4xx/5xx 时，`urlopen` **会抛 `HTTPError`**，但因为 HTTPError 是 URLError 子类，`except URLError` **能捕获到**。
3. 捕获后**静默 `pass`**，控制流**直接走到 line 35 的 Gemini fallback**。
4. **不会**触发 KeyError——line 31 根本不会执行（因为 urlopen 没正常返回就被异常打断了）。

**真正的问题是**：本地调用**其实失败了**（4xx/5xx = model 名错、Server 没加载对应模型、请求格式有问题等），但代码把它当作「网络挂了」一样静默走云端。**你以为 fallback 是因为 LM Studio 没启动，其实是 model 名错或 Server 配置问题**，而 Gemini 会响应一个跟本地无关的回答——你的程序在「看似成功」时悄悄走云端，**用户完全察觉不到**。

**建议改进**（区分「真连不上」和「API 错误」两种情况）：

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

## 6. 常见坑 & 排查清单

按踩坑频率排序：

### 坑 1：Server 没启动 / 端口被占

- **症状**：调用 `localhost:1234` 报 `ConnectionRefusedError` 或 `URLError`
- **排查**：
  1. 打开 LM Studio，进 Developer tab，看 **Start Server** 开关是不是开着的
  2. 看 Server URL 是不是 `http://localhost:1234`，不是的话以 Server 页面显示的为准
  3. 端口被占：在 Developer tab 把 Port 改成 `1235` 或其他空闲端口，然后 `gemma_client.py` 里 URL 同步改

### 坑 2：模型没加载完

- **症状**：Server 开了，但第一次调用报 `Model not loaded` 或超时
- **排查**：Developer tab 中间顶部，看模型状态是不是「Model loaded」。**5GB 模型冷启动要 10–30 秒**，磁盘慢的机器可能要 1 分钟。

### 坑 3：第一次调用很慢（模型预热）

- **症状**：第一个请求要等 10–60 秒，之后请求变快（每个 2–10 秒）
- **解释**：第一次调用时 llama.cpp 要做 JIT 编译、KV cache 预分配，**这不是 bug**。后续请求会快很多。
- **优化**：在 Server 设置里把 `Idle TTL` 调高（默认 5 分钟），避免空闲后被自动卸载再预热。

### 坑 4：`model` 字段写错名字 — 不会崩但会误导

- **症状**：API 返回 4xx，但你之前的代码 `except URLError: pass` 静默吞掉、直接 fallback 到 Gemini，**程序不报错，用户不知道本地其实没成功**
- **关键事实**：**LM Studio Server 通常忽略 `model` 字段**——只要 Server 加载了任意模型，它就用那个模型响应，根本不校验你发过来的 `model` 名是什么。所以**大多数情况下 model 字段填错也不崩**。但如果你想**精确控制**调用哪个模型（比如在多模型场景），应该确保 model 字段与下拉框显示的 ID 一致。
- **解决**：用 §5.2 点 3 改进版的代码，把 `HTTPError` 和 `URLError` 分开处理。

### 坑 5：Windows 看不到显卡（GPU Offload 永远是 0）

- **症状**：Developer tab 里 Hardware 显示「No GPU」或 `GPU Offload` 滑块拉不动
- **解决**：去 LM Studio 的 `Settings → Runtime → Install`，装 `llama.cpp (Windows) Nvidia CUDA 12` 引擎。装完重启 LM Studio。

### 坑 6：Context Length 调太大导致 OOM

- **症状**：调大 Context Length 后模型加载失败或推理中途崩溃
- **解决**：降回 8192 或 16384。Gemma 4 E4B 在 128K 上下文需要约 12-16GB 显存；如果你只有 8GB 显存，Context 别超过 32K。

### 坑 7：中文输出乱码 / 截断

- **症状**：中文回复到一半出现乱码方块或突然结束
- **解决**：
  - 确认 `Prompt Format` 是 `Gemma`（不要选 `ChatML`）
  - 把请求里的 `max_tokens` 调大
  - 如果是 `gemma_client.py` 解析问题，检查 `result['choices'][0]['message']['content']` 取值路径是否正确

### 坑 8（E4B 特有）：多模态调用方式

- **症状**：想用 E4B 识别图片，但只发了文本请求
- **解决**：E4B 是**多模态**模型，可以发图像/音频。但要通过 OpenAI 兼容 API 发送多模态内容，需要用结构化 `content` 数组（不是纯字符串）：

```python
# 多模态请求示例（图像 + 文本）
payload = {
    "model": "gemma-4-e4b-it",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "描述这张图"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
    }]
}
```

注意：这是 OpenAI 多模态格式，LM Studio 0.3.18+ 支持。

---

## 7. 进阶玩法：让模型输出更靠谱

### 7.1 System Prompt（系统提示词）— 给模型一个「人设」

System Prompt 是放在 `messages` 数组最开头、`role: "system"` 的那条消息。**模型会把它当作不可动摇的指令**，优先级最高。

```python
messages = [
    {"role": "system", "content": """你是一个资深的 Python 后端工程师。
回答要求：
1. 只回答 Python 相关问题，其他话题礼貌拒绝
2. 给出代码时必须包含类型注解
3. 解释不超过 3 句话
"""},
    {"role": "user", "content": "如何在 FastAPI 里做依赖注入？"}
]
```

**编写原则**：

1. **明确定义角色**：「你是 XXX」开头，第二人称
2. **给出具体行为准则**：列点 1/2/3，比「请认真回答」有效 100 倍
3. **提供边界**：明确说「不知道就说不知道」「不相关问题拒绝回答」
4. **示例最有力**：给一个输入/输出对，比描述效果更好
5. **避免冗长**：精炼准确 > 冗长描述

### 7.2 Few-shot Prompting（少样本提示）— 给模型「看几个例子」

在 user 消息前塞 1–5 组「输入→输出」示例，模型会**模仿示例的格式和风格**回答。

```python
messages = [
    {"role": "system", "content": "你是数据提取助手，从商品描述里提取结构化字段。"},
    # 示例 1
    {"role": "user", "content": "iPhone 15 Pro 256GB 钛原色 9999元"},
    {"role": "assistant", "content": '{"product":"iPhone 15 Pro","storage":"256GB","color":"钛原色","price":9999}'},
    # 示例 2
    {"role": "user", "content": "小米14 12+256 黑色 4299"},
    {"role": "assistant", "content": '{"product":"小米14","storage":"12+256GB","color":"黑色","price":4299}'},
    # 真实问题
    {"role": "user", "content": "华为Mate60 Pro 12+512 白色 6999元"}
]
```

**最佳实践**：

- **示例数量**：3 个左右最划算。超过 5–7 个收益递减，反而吃 token 拖慢速度。
- **示例质量 > 数量**：1 个高度相关的例子 > 10 个泛泛的例子
- **格式统一**：所有示例用同样的分隔符和结构
- **动态选择**（进阶）：用向量检索找出与当前问题最相似的 3 个示例塞进去

### 7.3 E4B 专属：利用 128K 上下文 + 多模态

- **128K 上下文**：可以一次塞进一整本中等长度的书（约 30-40 万汉字），适合长文档问答、代码库全局分析。
- **多模态**：发图片让它识别、读 PDF、OCR 文字——通过 `image_url` 字段发 base64 即可。
- **函数调用（Function Calling）**：E4B 原生支持，可以定义工具让模型自主决定调用时机（适合 Agent 场景）。

### 7.4 其他常用技巧

- **Temperature 0 + 多次采样**：让模型跑 3–5 次（OpenAI SDK 的 `n=5` 参数或循环调用），然后人工挑最好的。适合「需要确定性 + 又怕偶发错误」的场景。
- **结构化输出**：要 JSON 的话，在 System Prompt 里加「必须返回合法 JSON，不要任何解释文字」，把 temperature 降到 0.0–0.2。

---

## 参考链接

- LM Studio 官方文档（API & Server）：https://lmstudio.ai/docs
- LM Studio Developer Server 文档：https://lmstudio.ai/docs/developer/core/server
- LM Studio OpenAI 兼容性参考：https://lmstudio.ai/docs/developer/openai-compat
- LM Studio GitHub（最新 changelog & issue）：https://github.com/lmstudio-ai/lmstudio
- Google Gemma 4 发布公告（2026-04-02）：https://blog.google/technology/developers/google-gemma-4/
- Gemma 4 E4B 模型卡：https://huggingface.co/google/gemma-4-e4b-it
- OpenAI Chat Completions API 规范：https://platform.openai.com/docs/api-reference/chat
- Python `urllib.error` 官方文档（HTTPError / URLError 关系）：https://docs.python.org/3/library/urllib.error.html
- Anthropic Prompt 工程最佳实践：https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
- LangChain Few-shot Prompt 指南：https://python.langchain.com/docs/how_to/few_shot_examples/

---

**报告路径**：`E:\Antigravity IDE\project\gemma_match\docs\research\02-lm-studio-usage.md`
**核心要点**：
1. 你的 5GB 文件是 **Gemma 4 E4B**（2026-04-02 Google 发布，4B 参数 + 128K 上下文 + 多模态），`gemma_client.py` 里的 `model: "gemma-4-e4b-it"` **保持原样，不要改**。
2. Server 启动流程：Developer tab → 选模型 → Start Server → 记下 `http://localhost:1234/v1`。
3. **404/HTTPError 行为正解**：HTTPError 是 URLError 子类 → 被 `except URLError: pass` 静默吞掉 → 直接走 Gemini fallback → **不会**触发 KeyError（但会**误导**你以为本地挂了）。
4. gemma_client.py 三处改进：(a) `model` 字段**不动**；(b) `timeout=120` 改成 300 秒；(c) 把 `HTTPError` 和 `URLError` 分开处理，4xx 时给出本地 API 错误详情而不是静默 fallback。
