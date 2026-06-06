import json
from golden_examples import get_golden_example

SYSTEM_PROMPT = """你是微信小程序页面源码生成器，只生成 `pages/index/index` 的 wxml/wxss/js 代码。
你必须将代码严格分为三段，每一段分别用 `===WXML===`, `===WXSS===`, `===JS===` 作为开头。不要使用 JSON 格式！

===WXML===
<view class="container">...</view>
===WXSS===
.container { ... }
===JS===
Page({ data: {}, onLoad() {} })

【约束条件】
- 只能用这些组件: view, text, image, button, input, textarea, form, scroll-view, swiper, swiper-item, block。
- 所有数据用本地 mock，写在 JS 的 data 里。
- 禁止 HTML 标签: 不许出现 <div> <p> <span> <img> <a> <ul> <li> 等，一律用 view/text。
- 禁止在 {{ }} 里调函数: 如 {{price.toFixed(2)}} 不行，必须在 JS 里格式化好，存入 data。
- swiper 用 current，不用 current-index。
- 禁止真实能力 API: wx.login / wx.request / wx.requestPayment / wx.getLocation / wx.cloud 等。
- 图片不要用会失效的远程 URL；用纯色 view 占位或使用 image 的 mode 属性。
- 【极为重要的审美约束】：你必须生成高度复杂、具有设计感的前端界面！绝不能仅仅给出一个基础骨架。
- 全局已经在 app.wxss 为你预置了极其丰富的现代设计原子类，你**必须**大量且合理地使用它们：
  1. 布局基类：`flex-row`, `flex-col`, `flex-center`, `flex-between`
  2. 容器基类：`card` (普通卡片, 带圆角和浅阴影), `glass-card` (毛玻璃卡片, 适合用在彩色背景上)
  3. 按钮基类：`btn-primary` (带渐变和阴影的华丽主按钮)
  4. 文本基类：`text-title` (粗体大标题), `text-desc` (灰色副标题)
  5. 颜色与变量：你可以在自定义 wxss 中使用 `var(--primary)`, `var(--bg-color)`, `var(--border-radius-md)` 等全局变量保持风格统一。
"""

def build_planning_prompt(user_prompt: str) -> str:
    """
    Builds the prompt requesting the model to analyze the requirements and plan the architecture.
    """
    prompt = f"{SYSTEM_PROMPT}\n\n"
    prompt += "【用户需求】\n"
    prompt += f"{user_prompt}\n\n"
    prompt += "请首先详细分析上述需求，规划出该页面的布局结构、所需要的组件、CSS类名设计以及JS的mock数据结构。\n"
    prompt += "注意：此步只需进行推演和思考，输出你的详细计划，暂时不需要输出代码本身。\n"
    
    return prompt

def build_learning_prompt(user_prompt: str) -> str:
    """
    Agent 2: Learns from the golden paradigm before coding.
    """
    few_shot_dict = get_golden_example(user_prompt)
    few_shot_text = f"===WXML===\n{few_shot_dict['wxml']}\n===WXSS===\n{few_shot_dict['wxss']}\n===JS===\n{few_shot_dict['js']}"
    
    prompt = f"{SYSTEM_PROMPT}\n\n"
    prompt += "【黄金范式学习】\n"
    prompt += "为了满足用户的需求，我们匹配到了以下最适合的黄金代码范式：\n"
    prompt += "```example\n" + few_shot_text + "\n```\n\n"
    prompt += "【任务指令】\n"
    prompt += "请作为高级架构解剖师，仔细学习这份黄金代码的底层结构，并输出一份《范式学习指南》。\n"
    prompt += "你需要总结：\n"
    prompt += "1. WXML 的嵌套结构与关键标签组件。\n"
    prompt += "2. WXSS 的原子类搭配规则与页面高难度样式的实现原理（如毛玻璃、渐变）。\n"
    prompt += "3. JS 的数据结构与交互机制。\n"
    prompt += "4. 结合用户的原始需求，说明我们在接下来的代码编写中应该如何**100% 沿用**这种黄金结构的写法。\n"
    
    return prompt

def build_coding_prompt(plan_output: str, learning_output: str) -> str:
    """
    Builds the prompt requesting the code generation based on the previous plan and learning.
    """
    prompt = "【终极指令：全量代码输出】\n"
    prompt += "基于前面的【业务推演】和刚刚的【黄金范式学习指南】，现在进入终极生成阶段。\n\n"
    prompt += "【你的业务骨架推演】\n"
    prompt += f"{plan_output}\n\n"
    prompt += "【你的黄金范式解剖指南】\n"
    prompt += f"{learning_output}\n\n"
    prompt += "【极度重要的核心要求】\n"
    prompt += "1. 深度复刻：你必须完全吸收上一步学习到的黄金结构范式，将原子类、高级布局完美应用到本次需求中。\n"
    prompt += "2. 丰富性与骨肉：绝对不能仅仅给出一个简单的框架骨架！每一个区块都必须有丰富的mock数据填充，WXML结构必须嵌套精细，WXSS样式必须极其华丽。\n"
    prompt += "3. 代码量标准：作为一款商业级产品，实际代码量应极为庞大，请尽情发挥，务必编写至少 500-1000 行的业务级前端代码，不设上限！\n\n"
    prompt += "【格式警告与最终指令】\n"
    prompt += "【极其严格的格式警告：如果你不输出代码，系统将直接崩溃】\n"
    prompt += "绝对禁止重复输出规划内容、分析过程或任何汉字废话！！！\n"
    prompt += "你的回答格式必须且只能是代码，并且必须严格按以下顺序排列：\n"
    prompt += "===WXML===\n<代码>\n===WXSS===\n<代码>\n===JS===\n<代码>\n\n"
    prompt += "你现在是一个没有感情的代码输出机器。请直接以下面的字符串开头，不要带任何前言：\n===WXML==="
    
    return prompt

def build_repair_prompt(user_prompt: str, page_files: dict, errors: list) -> str:
    """
    Builds a prompt requesting self-healing based on validation errors.
    """
    prompt = f"{SYSTEM_PROMPT}\n\n"
    prompt += "【之前生成的代码存在以下严重错误，请根据错误信息修复并严格按照 ===WXML=== 等分割标志重新生成全量代码】\n"
    for err in errors:
        prompt += f"- {err}\n"
        
    prompt += "\n【原始用户需求】\n"
    prompt += f"{user_prompt}\n"
    
    return prompt

def build_incremental_prompt(user_prompt: str, current_page_files: dict) -> str:
    """
    Builds a prompt requesting the model to modify the existing generated code based on new instructions.
    """
    prompt = f"{SYSTEM_PROMPT}\n\n"
    prompt += "【这是当前已经生成的页面代码】\n"
    prompt += json.dumps(current_page_files, ensure_ascii=False, indent=2) + "\n\n"
    
    prompt += "【用户的修改需求】\n"
    prompt += f"{user_prompt}\n\n"
    prompt += "请根据用户的修改需求，在当前代码的基础上进行增量或全量修改，并严格以 ===WXML=== 分割的格式输出修改后的三段代码。"
    
    return prompt
