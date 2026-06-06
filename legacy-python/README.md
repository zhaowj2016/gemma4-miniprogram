### 前置说明

我们的最终目标：做一个能听懂自然语言（比如“我要一个带红色提交按钮的登录页”），并自动生成可运行的小程序代码的AI工具，核心依赖 **Gemma 4的Function Calling能力**（简单说就是让AI像程序员一样“调用工具函数”生成代码，而不是瞎编代码）。

## 步骤1：准备基础账号与环境（1-2小时）

### 1.1 注册Google账号（必须）

Gemma 4是Google的模型，需要先有Google账号才能用：

- 打开 [Google账号注册页](https://accounts.google.com/signup)，按提示完成注册（如果有梯子/科学上网环境更顺畅，没有的话可查“Google账号注册 国内”教程）。
- 注册后登录 [Google AI Studio](https://aistudio.google.com/)（Gemma模型的开发控制台），首次登录会让你同意条款，全部勾选即可。

### 1.2 安装Python（小白友好版）

我们的后端代码用Python写，先装Python：

- 打开 [Python官网](https://www.python.org/downloads/)，下载对应系统的Python（选3.9-3.11版本，兼容性最好）。
- 安装时**务必勾选“Add Python to PATH”**（Windows），Mac直接装即可。
- 验证是否装成功：打开电脑的“终端”（Mac）/“命令提示符”（Windows），输入 `python --version`，能显示版本号（比如Python 3.10.0）就是成功。

### 1.3 安装代码编辑器（选VS Code）

- 下载 [VS Code](https://code.visualstudio.com/)，安装后打开，在扩展商店搜“Python”，安装微软官方的Python插件（方便写代码、运行代码）。

## 步骤2：获取Gemma 4 API Key（10分钟）

API Key是调用Gemma模型的“钥匙”，必须拿到：

1. 登录 [Google AI Studio](https://aistudio.google.com/)，点击页面右上角的“☰”（菜单）→“API Keys”。
2. 点击“Create API Key”，会生成一串字符（比如 `AIzaSyxxxxxx`），**复制下来保存到记事本**（丢了要重新生成）。
   ⚠️ 注意：这个Key是你的私密信息，不要分享给任何人！

## 步骤3：搭建Python依赖环境（5分钟）

打开终端/命令提示符，依次输入以下命令（输完一行按回车，等待安装完成）：

```bash
# 安装Google官方的Gemma SDK
pip install google-generativeai
# 安装辅助构建Agent工作流的工具（可选，但推荐）
pip install langchain-google-genai
# 安装极速搭建前端的工具（后续做可视化用）
pip install streamlit
```

✅ 验证：如果没有红色报错，只是一堆“Successfully installed xxx”，就是安装成功。

## 步骤4：定义第一个“代码生成工具函数”（30分钟）

核心逻辑：先写好“生成小程序组件”的Python函数（比如生成按钮、输入框），让Gemma 4调用这个函数生成代码（而不是让AI直接编代码）。

### 4.1 新建代码文件

打开VS Code，点击“文件”→“新建文件”，保存为 `miniprogram_tools.py`（文件名别乱改）。

### 4.2 写第一个工具函数（生成按钮组件）

把下面的代码复制到文件里（我加了详细注释，小白也能看懂）：

```python
def create_miniprogram_button(props: list, text_content: str):
    """
    生成小程序的按钮组件代码（WXML格式）
    :param props: 按钮的属性，比如样式、点击事件，示例：['class="red-btn"', 'bindtap="handleSubmit"']
    :param text_content: 按钮上显示的文字，比如“提交”“登录”
    :return: 生成好的按钮代码和状态
    """
    # 把属性列表拼接成字符串（比如['class="red-btn"']变成'class="red-btn"'）
    props_str = " ".join(props)
    # 拼接成小程序的按钮代码
    button_code = f"<button {props_str}>{text_content}</button>"
    # 返回成功状态和代码
    return {"status": "success", "code": button_code}

# 测试函数是否能用（小白可以先跑一下看效果）
if __name__ == "__main__":
    # 调用函数生成“红色提交按钮”
    test_button = create_miniprogram_button(
        props=['class="red-btn"', 'bindtap="handleSubmit"'],
        text_content="提交"
    )
    print("生成的按钮代码：", test_button["code"])
```

### 4.3 运行测试

在VS Code中打开终端（点击顶部“终端”→“新建终端”），输入：

```bash
python miniprogram_tools.py
```

如果终端输出：`生成的按钮代码： <button class="red-btn" bindtap="handleSubmit">提交</button>`，说明函数写对了！

## 步骤5：让Gemma 4绑定并调用这个工具函数（40分钟）

这一步是核心：让Gemma模型知道“你有这个生成按钮的工具”，并能主动调用它。

### 5.1 新建Agent主文件

在VS Code中新建文件，保存为 `ai_agent.py`，复制以下代码（记得替换你的API Key）：

```python
# 导入Google的Gemma SDK
import google.generativeai as genai

# 导入我们写的工具函数
from miniprogram_tools import create_miniprogram_button

# 第一步：配置API Key（替换成你自己的Key！）
genai.configure(api_key="你的Gemma API Key")

# 第二步：把工具函数绑定给Gemma模型
# model_name按大赛要求改，目前先用水晶的gemma-2b-it
model = genai.GenerativeModel(
    model_name='gemma-2b-it',
    # 告诉模型：你可以调用这个生成按钮的工具
    tools=[create_miniprogram_button],
    # 开启自动工具调用（让模型自己决定要不要调用函数）
    generation_config={"tool_config": {"function_calling_config": {"mode": "auto"}}}
)

# 第三步：初始化对话（让AI记住上下文）
chat = model.start_chat(enable_automatic_function_calling=True)

# 第四步：给AI设定角色（System Prompt）
# 告诉AI：你是小程序开发专家，要调用我们的工具生成代码
system_prompt = """
你是一个资深的微信小程序开发专家AI Agent，你的唯一任务是：
1. 理解用户的小程序需求；
2. 主动调用create_miniprogram_button工具生成对应的按钮组件代码；
3. 每次调用工具前，先告诉用户你的规划；
4. 只输出清晰、可运行的代码和简单的解释，不要说无关的话。
"""

# 把角色设定发给AI
chat.send_message(system_prompt)

# 第五步：和用户交互（测试）
def chat_with_agent(user_input):
    # 把用户需求发给AI
    response = chat.send_message(user_input)
    # 打印AI的回复（包括思考过程和生成的代码）
    print("AI的回复：\n", response.text)
    # 如果AI调用了工具，打印工具返回的结果
    if response.candidates[0].content.parts[0].function_call:
        func_result = response.candidates[0].content.parts[0].function_call.response
        print("\n工具生成的代码：\n", func_result["code"])

# 测试：让AI生成“红色提交按钮”
if __name__ == "__main__":
    user_need = "帮我生成一个红色的提交按钮，点击后触发提交事件"
    print("用户需求：", user_need)
    chat_with_agent(user_need)
```

### 5.2 运行测试

在终端输入：

```bash
python ai_agent.py
```

✅ 预期效果：

- AI会先告诉你“我要调用生成按钮的工具，参数是xxx”；
- 然后输出工具生成的按钮代码：`<button class="red-btn" bindtap="handleSubmit">提交</button>`。
  ⚠️ 如果报错：先检查API Key是否填对，再检查网络是否能访问Google。


  本地启动前端：
  cd D:\VSWorkSpace\gemma4\gemma4-miniprogram\Frontend
   $env:PYTHONPATH="D:\soft\PythonPackages"; python -m streamlit run frontend_LMStudio.py
