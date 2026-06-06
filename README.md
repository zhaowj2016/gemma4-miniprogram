# Gemma Match 黑客松最终执行方案（Agent 完整版）

## 一、项目目标（一句话）

用户输入自然语言 → Gemma 生成三段式代码 → 系统合并固定脚手架 → 静态校验 → （可选一次自愈）→ 打包 Zip → 用户下载。

## 二、技术栈（固定）

- Python 3.9+
- Streamlit（UI）
- 本地 Gemma（通过 LM Studio 或 Ollama）或 云端 Gemma API（自动适配）
- 仅使用标准库：`json`, `re`, `tempfile`, `zipfile`, `pathlib`, `shutil`
- **不引入**：Docker, Node.js, miniprogram-ci, React, 复杂前端框架

## 三、项目结构（Agent 创建）

```
gemma_match_hackathon/
├── app.py                 # Streamlit 主程序
├── gemma_client.py        # 调用 Gemma（自动适配本地/云端）
├── prompt_builder.py      # 构建 system + user prompt
├── parser.py              # 解析三段式输出（+ 可选 XML CDATA 兜底）
├── validator.py           # 静态校验（硬失败 + warnings）
├── scaffold.py            # 固定脚手架文件内容
├── zip_exporter.py        # 打包 Zip
├── golden_examples/       # 手写黄金样例（供 fallback）
│   ├── activity_signup/   # 活动报名页
│   ├── product_detail/    # 商品详情页
│   └── product_list/      # 列表页
├── demo_cache/            # 预生成缓存（可选）
└── README.md              # 本文件
```

## 四、固定脚手架（模型不生成，系统提供）

| 文件 | 内容（固定） |
|------|-------------|
| `app.json` | `{"pages":["pages/index/index"], "window":{"navigationBarTitleText":"Gemma Match"}, "style":"v2"}` |
| `app.js` | `App({})` |
| `app.wxss` | `page { background: #f7f8fa; font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif; }` |
| `project.config.json` | 见下方 **4.1 节** |
| `pages/index/index.json` | `{"navigationBarTitleText":"Gemma Match"}`（可被模型扩展） |

### 4.1 `project.config.json`（安全写法）

```json
{
  "appid": "YOUR_APPID",
  "projectname": "gemma-match-generated",
  "compileType": "miniprogram",
  "miniprogramRoot": "./",
  "setting": {
    "es6": true,
    "postcss": true,
    "minified": false,
    "urlCheck": false
  }
}
```

**UI 中必须提示**：下载后请用你自己的小程序 AppID 替换 `YOUR_APPID`，否则微信开发者工具无法预览。

## 五、输出协议（核心：三段式裸代码）

模型**只输出**三个标记块，不输出路径、不输出 JSON、不输出解释文字。

```
===WXML===
<view class="page">
  <text>活动报名</text>
  <input placeholder="手机号" bindinput="onPhoneInput" />
  <button bindtap="onSubmit">报名</button>
</view>

===WXSS===
.page { padding: 32rpx; }
.input { margin: 16rpx 0; }

===JS===
Page({
  data: { phone: '' },
  onPhoneInput(e) { this.setData({ phone: e.detail.value }); },
  onSubmit() { wx.showToast({ title: '报名成功' }); }
})
```

**可选扩展**：若模型输出 `===JSON===` 块，内容将合并到 `pages/index/index.json`（覆盖导航栏标题等字段）。

**解析规则**（`parser.py`）：
- 按 `===WXML===`、`===WXSS===`、`===JS===` 分割。
- 若缺少任一块 → 解析失败，触发重生成。
- 解析前需清理模型可能包裹的 Markdown 代码块（见下方实现细节）。

## 六、System Prompt 模板（`prompt_builder.py`）

```python
SYSTEM_PROMPT = """
你是微信小程序页面代码生成器。
你只生成 pages/index/index 页面的代码。
你必须严格按照以下格式输出三段内容，不要输出其他任何解释文字：

===WXML===
<view>...</view>

===WXSS===
...

===JS===
Page({...})

组件白名单：view, text, image, button, input, textarea, form, scroll-view, swiper, swiper-item
禁止使用：map, canvas, video, camera, web-view, open-data, live-player
禁止调用：wx.login, wx.request, wx.requestPayment, wx.getLocation, wx.cloud
所有数据使用本地 mock，不要真实网络请求。
不要输出路径或文件名。
"""
```

**Few-shot 增强**：在 user prompt 前可附上一个黄金样例的完整三段式代码作为示例（从 `golden_examples/` 读取）。

## 七、静态校验器（`validator.py`）

### 7.1 硬失败（Hard Fail）—— 触发重生成或 fallback

| 检查项 | 实现方式 |
|--------|----------|
| 三段式解析失败（缺少任一块） | `parse_triple` 返回 None |
| `pages/index/index.wxml` / .wxss / .js 任一为空 | 内容长度 < 10 字符 |
| 任一 JSON 文件（包括合并后的 index.json）解析失败 | `json.loads()` 异常 |
| 出现危险 API | 正则 `wx\.(login\|request\|requestPayment\|getLocation\|cloud)` |
| 路径包含 `..` 或绝对路径（如 `/etc`） | 字符串匹配 |
| 文件名或路径包含中文字符 | 正则 `[\u4e00-\u9fff]` |

### 7.2 警告（Warning）—— 仅 UI 显示，不阻断，Zip 照常生成

| 检查项 | 说明 |
|--------|------|
| WXML 中存在非白名单标签 | 列出标签名，提醒用户手动检查 |
| WXSS 中存在可疑单位（`rem`, `vw`, `vh` 非 `100%`） | 正则匹配，建议改为 rpx |
| 事件绑定 `bindtap="x"` 但 JS 中无 `x(` 或 `x:` | 正则提取，JS 中查找（warning，不阻断） |
| WXML 中 `{{ }}` 变量在 JS 的 `data` 中未定义 | 解析 `data` 对象 keys，对比（warning） |

## 八、自愈流程（`app.py` 中实现）

```python
def generate_with_repair(user_prompt, max_attempts=2):
    for attempt in range(max_attempts):
        raw_output = call_gemma(build_prompt(user_prompt, attempt))
        parsed = parse_triple(clean_model_output(raw_output))
        if not parsed:
            continue
        merged_files = merge_with_scaffold(parsed)   # 加入固定脚手架
        hard_errors = validate_hard(merged_files)
        if not hard_errors:
            return merged_files   # 成功
        # 构造自愈 prompt
        error_msg = "; ".join(hard_errors)
        user_prompt = f"之前生成的代码有错误：{error_msg}\n请重新生成完整的三段式代码。\n原始需求：{user_prompt}"
    # 失败后 fallback
    return fallback_by_keywords(original_user_prompt)
```

**UI 要求**：显示“正在进行第 X 次自愈重试...”，缓解等待焦虑。

## 九、Fallback 策略（关键词匹配）

```python
FALLBACK_MAP = {
    "活动|报名|表单|预约": "golden_examples/activity_signup",
    "商品|详情|购买|价格": "golden_examples/product_detail",
    "列表|瀑布流|商品列表": "golden_examples/product_list",
    "门店|地址|电话": "golden_examples/store_info",   # 可选
}

def fallback_by_keywords(prompt):
    for pattern, path in FALLBACK_MAP.items():
        if re.search(pattern, prompt):
            return load_golden_example(path)
    return load_golden_example("golden_examples/activity_signup")  # 默认
```

**黄金样例存储格式**：每个文件夹下存放 `wxml.txt`、`wxss.txt`、`js.txt`（纯文本，不含标记）。`load_golden_example` 返回与正常生成完全一致 of `files_dict`（包含固定脚手架 + 页面三件套）。

## 十、Demo 预缓存策略

- 在 `demo_cache/` 下预存 2~3 个成功生成的 Zip 文件及对应 prompt。
- Streamlit UI 中增加一个复选框：`使用预缓存（演示模式）`。
  - 勾选时，直接从 `demo_cache/` 读取对应 prompt 的 zip，不调用模型。
  - 不勾选时，实时调用模型。
- 提前截好导入微信开发者工具的截图（含 prompt 和生成物），放入演示 slides。

## 十一、补充实现细节（必须遵守）

### 1. 模型输出预处理
```python
def clean_model_output(raw: str) -> str:
    lines = raw.split('\n')
    if lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
    return '\n'.join(lines)
```

### 2. XML CDATA 作为兜底（可选但推荐）
如果三段式解析失败，可尝试解析 XML CDATA 格式。此部分为可选，若三段式不稳定可用 30 分钟补上。

### 3. 文件编码与临时目录清理
所有文件读写统一 `encoding='utf-8'`。使用 `tempfile.TemporaryDirectory()` 确保自动清理：
```python
with tempfile.TemporaryDirectory() as tmpdir:
    # 写入文件...
    # 打包 zip...
    # 返回 zip 二进制数据后，目录自动销毁
```

### 4. 模型调用超时与重试
- 设置 API 调用超时（例如 60 秒），超时后视为失败，触发自愈或 fallback。
- 网络类错误（连接失败、超时）可额外重试 1 次，不计入“自愈次数”。

### 5. 黄金样例的预验证（Day 1 上午必须完成）
- 手写 3 个黄金样例（活动报名、商品详情、列表页），每个样例文件夹包含完整小程序结构。
- 用占位符 `YOUR_APPID` 配置 `project.config.json`，手动导入微信开发者工具，确认可以编译预览。
- 截图保存。

### 6. UI 中的 AppID 提示
在下载按钮旁醒目提示：
> ⚠️ 下载后请用你自己的小程序 AppID 替换 `project.config.json` 中的 `YOUR_APPID`，否则微信开发者工具可能无法预览。

### 7. 警告展示
校验结束后，在 UI 中清晰显示：
- 硬失败数量（若为 0 则显示“通过”）
- 警告列表（如果有）
- Zip 下载按钮仅在无硬失败时启用（或永远启用但标注风险，推荐仅在无硬失败时启用）

### 8. 自愈进度提示
在重试过程中，UI 明确显示：`⏳ 正在进行第 1 次自愈重试...`

## 十二、环境准备清单（Agent 执行前确认）

```markdown
## 环境要求
- Python 3.9+ （推荐 3.10）
- 安装依赖：`pip install streamlit requests` （若使用本地 Gemma，无需 requests）
- 微信开发者工具（用于手动验证，下载地址：https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html）
- Gemma 模型调用方式二选一：
  A. 本地 LM Studio / Ollama：启动本地服务，地址如 `http://localhost:1234/v1`
  B. 云端 API：配置环境变量 `GEMINI_API_KEY` 和 `GEMINI_API_URL`
```

## 十三、调试排错指南（供现场快速定位）

| 现象 | 可能原因 | 解决方法 |
|------|----------|----------|
| 模型输出为空或乱码 | Gemma 服务未启动或超时 | 检查本地 LM Studio 是否运行，或 API key 是否有效 |
| 解析失败（缺少 ===WXML===） | 模型未遵守输出格式 | 查看原始输出（打印 raw_text），调整 system prompt 增加 few-shot |
| 微信开发者工具报“appid 无效” | 未替换 YOUR_APPID | 提示用户手动替换，或改用自己已注册 of appid |
| Zip 下载后解压失败 | 临时目录权限问题 | 使用 `tempfile` 确保可写，或换用固定目录并手动清理 |
| 自愈循环无限重试 | 错误信息未正确传给模型 | 检查 `hard_errors` 列表是否非空，且自愈 prompt 中包含具体错误 |

## 十四、执行清单（按顺序完成）

**阶段 1（黄金样例 + 脚手架验证）**
- [x] 手写 3 个黄金样例（活动报名、商品详情、列表页），每个样例文件夹包含完整小程序结构。
- [x] 用占位符 `YOUR_APPID` 配置 `project.config.json`，手动导入微信开发者工具，确认可以编译预览。
- [x] 截图保存。

**阶段 2（核心链路开发）**
- [x] 实现 `gemma_client.py`（自动适配本地/云端，支持超时重试）。
- [x] 实现 `prompt_builder.py` (system prompt + few-shot)。
- [x] 实现 `parser.py`（三段式解析 + `clean_model_output`，支持可选 `===JSON===`）。
- [x] 实现 `scaffold.py`（固定脚手架文件字典）。
- [x] 实现 `zip_exporter.py`（使用 `tempfile.TemporaryDirectory` 打包）。
- [x] 实现 `app.py` 基础 UI（文本框、示例按钮、生成按钮、下载按钮、状态显示）。

**阶段 3（校验器 + 自愈 + Fallback）**
- [x] 实现 `validator.py` 的硬失败检查（7.1 清单）。
- [x] 实现自愈循环（最多 2 次尝试，第 1 次带错误信息重生成）。
- [x] 实现关键词 fallback（加载黄金样例）。
- [x] 增加 warning 检查（7.2 清单），UI 中显示但不阻断下载。
- [x] 测试 5 个 prompt 的手动成功率。

**阶段 4（预缓存 + Demo 打磨）**
- [x] 预跑 2~3 个 prompt，将结果 Zip 存入 `demo_cache/`，截图导入开发者工具。
- [x] 完善 UI 文案（AppID 提示、自愈进度、警告列表）。
- [x] 最终全流程手工测试（至少 3 个 prompt，每个都下载并快速目测代码）。

## 十五、成功标准

- [x] 至少一个黄金样例可手动导入开发者工具并运行。
- [x] 输入示例 prompt，能生成三段式代码并成功合并为完整项目。
- [x] 硬失败场景（如故意包含 `wx.login`）能触发重生成或 fallback。
- [x] 最终可下载 Zip，解压后目录结构正确。
- [x] UI 清晰显示校验结果（通过 / 警告）。

## 十六、最终交付物

- 完整的 GitHub 仓库（或 zip）包含上述所有代码。
- 本文件作为 `README.md`。
- 演示录屏链接（或截图）以及手动导入开发者工具的截图。
