"""
LMStudio 本地适配层
====================
作用：让项目在不修改原有 gemma_client.py 的前提下，接入 LMStudio 本地 Gemma 4 模型。
设计原则：
  - 零侵入：不修改任何现有文件
  - 接口兼容：返回格式与 gemma_client.call_gemma_with_tools 完全一致
  - 可测试：提供独立测试入口，验证通过后再接入 MCP

依赖：
    pip install openai
"""

import json
import openai

# 从现有项目复用：避免重复定义工具 Schema 和消息构建逻辑
from gemma_client import _build_openai_messages, _OPENAI_TOOLS

# 从现有项目复用：文本解析兜底（当模型不输出标准 tool_calls 时）
from parser import parse_triple


def call_lmstudio(
        prompt: str,
        base_url: str = "http://127.0.0.1:1234/v1",
        model: str = "google/gemma-4-e4b",
        image_data: bytes = None,
        image_mime: str = "image/jpeg",
        image_list: list = None,
        temperature: float = 0.7,
        max_tokens: int = 16384,
) -> dict:
    """
    通过 LMStudio 本地 OpenAI 兼容 API 调用 Gemma 4，生成小程序代码。

    返回格式与 gemma_client.call_gemma_with_tools 完全一致：
    {
        "wxml": str,
        "wxss": str,
        "js": str,
        "parse_method": str,  # "standard_tool_calls" 或 "plain_text_fallback"
        "provider": str,     # 固定为 "lmstudio"
    }

    参数：
        prompt: 给模型的指令文本
        base_url: LMStudio Local Server 地址
        model: LMStudio 中加载的模型标识符（如 "google/gemma-4-e4b"）
        image_data / image_mime / image_list: 多模态输入（可选）
        temperature / max_tokens: 生成参数
    """
    # 1. 初始化 OpenAI 兼容客户端
    #    LMStudio 不需要真实 API Key，但 openai 库要求传入非空字符串，所以随便填
    client = openai.OpenAI(base_url=base_url, api_key="lmstudio")

    # 2. 构建消息（复用 gemma_client 的现有逻辑，确保图片/文本格式一致）
    messages = _build_openai_messages(prompt, image_data, image_mime, image_list)

    # 3. 调用模型（强制工具调用 create_miniprogram_page）
    #    tools=_OPENAI_TOOLS 让模型知道可以调用"生成小程序"工具
    #    tool_choice="auto" 让模型自己决定是否调用（通常有需求描述时会调用）
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=_OPENAI_TOOLS,  # 复用 gemma_client 定义的工具 Schema
        tool_choice="auto",  # 让模型自己决定是否调用工具
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # 4. 解析响应
    msg = response.choices[0].message
    tool_calls = msg.tool_calls

    # 5. 标准工具调用路径（最理想情况：模型正确返回了 tool_calls）
    if tool_calls and len(tool_calls) > 0:
        fn = tool_calls[0].function
        if fn.name == "create_miniprogram_page":
            args = json.loads(fn.arguments)
            return {
                "wxml": str(args.get("wxml", "")),
                "wxss": str(args.get("wxss", "")),
                "js": str(args.get("js", "")),
                "parse_method": "standard_tool_calls",
                "provider": "lmstudio",
            }

    # 6. 兜底：文本解析路径（模型没走 tool_calls，直接输出文本）
    #    复用 parser.parse_triple 解析文本中的 WXML/WXSS/JS 标记
    content = msg.content or ""
    if content:
        parsed = parse_triple(content)
        if parsed and all(k in parsed for k in ("wxml", "wxss", "js")):
            return {
                "wxml": parsed["wxml"],
                "wxss": parsed["wxss"],
                "js": parsed["js"],
                "parse_method": "plain_text_fallback",
                "provider": "lmstudio",
            }

    # 7. 都失败了，抛出异常让上层处理（MCP 层会捕获并返回错误 JSON）
    raise ValueError(
        f"LMStudio 未返回有效代码。tool_calls={bool(tool_calls)}, "
        f"content_preview={content[:200]!r}"
    )


def call_lmstudio_text(
        prompt: str,
        base_url: str = "http://127.0.0.1:1234/v1",
        model: str = "google/gemma-4-e4b",
        temperature: float = 0.6,
        max_tokens: int = 2048,
) -> str:
    """
    通过 LMStudio 做纯文本推理（不强制工具调用）。
    用于需求澄清、风格建议等非代码生成场景。

    返回：模型生成的纯文本字符串
    """
    client = openai.OpenAI(base_url=base_url, api_key="lmstudio")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content or ""