"""
MiniPilot MCP Server
====================
将 MiniPilot Agent 的核心能力封装为 MCP (Model Context Protocol) 标准工具，
任何兼容 MCP 的客户端（Claude Desktop、Cursor、LangChain Agent 等）均可调用。

运行方式：
    python mcp_server.py              # stdio 模式（本地 AI 客户端直连）
    python mcp_server.py --transport sse --port 8001   # SSE 模式（HTTP 服务）

依赖：
    pip install fastmcp>=3.2.4
"""

import argparse
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# 复用现有项目模块（零侵入原则：只导入，不修改）
# ---------------------------------------------------------------------------

# 1. LMStudio 适配层（已验证通过测试）
from gemma_client_lmstudio import call_lmstudio, call_lmstudio_text

# 2. 静态校验器（现有文件，团队已写好）
from validators import validate_project

# 3. 渲染器（可选，如果团队已有该文件）
try:
    from render_wxml import render as render_wxml_html
except ImportError:
    render_wxml_html = None

# 4. 脚手架（可选，如果团队已有该文件）
try:
    from scaffold import build_scaffold
except ImportError:
    build_scaffold = None

# ---------------------------------------------------------------------------
# MCP Server 初始化
# ---------------------------------------------------------------------------

mcp = FastMCP("MiniPilot")


# ---------------------------------------------------------------------------
# Tool 1: 生成小程序页面（核心能力）
# ---------------------------------------------------------------------------

@mcp.tool()
def generate_miniprogram_page(
        description: str,
        style: str = "默认",
        features: Optional[list] = None,
        mode: str = "auto",
) -> dict:
    """
    根据自然语言描述生成微信小程序 pages/index/index 页面的 WXML/WXSS/JS 三件套。

    Args:
        description: 页面需求描述，例如"帮我生成一个咖啡店点单小程序页面，要有商品列表、购物车和底部结算按钮"
        style: 设计风格，如"简约风"、"卡通风"、"商务风"
        features: 功能列表，如["商品列表", "购物车", "结算按钮"]
        mode: 保留参数（兼容接口），实际通过 LMStudio 本地调用

    Returns:
        {
            "wxml": str,           # 页面结构代码
            "wxss": str,           # 样式代码
            "js": str,             # 逻辑代码
            "provider": str,       # 固定为 "lmstudio"
            "parse_method": str,   # "standard_tool_calls" 或 "plain_text_fallback"
            "validation_passed": bool,
            "validation_report": str,
        }
    """
    # 1. 组装 Prompt（与现有 app_demo.py 逻辑保持一致）
    prompt_parts = [description]
    if style and style != "默认":
        prompt_parts.append(f"设计风格：{style}")
    if features:
        prompt_parts.append(f"必须包含的功能：{', '.join(features)}")
    prompt = "\n".join(prompt_parts)

    # 2. 调用 LMStudio 本地模型（已验证的链路）
    try:
        result = call_lmstudio(prompt=prompt)
    except Exception as e:
        return {
            "error": f"Gemma 4 (LMStudio) 生成失败: {str(e)}",
            "wxml": "",
            "wxss": "",
            "js": "",
            "provider": "",
            "parse_method": "",
            "validation_passed": False,
            "validation_report": "",
        }

    # 3. 静态校验（复用团队已有的 validators.py）
    files = {
        "pages/index/index.wxml": result.get("wxml", ""),
        "pages/index/index.wxss": result.get("wxss", ""),
        "pages/index/index.js": result.get("js", ""),
    }
    validation = validate_project(files, full_project=False)

    # 4. 组装返回
    return {
        "wxml": result.get("wxml", ""),
        "wxss": result.get("wxss", ""),
        "js": result.get("js", ""),
        "provider": result.get("provider", ""),
        "parse_method": result.get("parse_method", ""),
        "validation_passed": validation.ok,
        "validation_report": validation.report(),
    }


# ---------------------------------------------------------------------------
# Tool 2: 校验小程序代码
# ---------------------------------------------------------------------------

@mcp.tool()
def validate_miniprogram_code(
        wxml: str,
        wxss: str,
        js: str,
        json_str: str = "",
) -> dict:
    """
    对小程序页面三件套进行静态校验（HARD 错误拦截 + WARNING 提示）。

    Args:
        wxml: WXML 结构代码
        wxss: WXSS 样式代码
        js: JS 逻辑代码
        json_str: 可选的页面 JSON 配置

    Returns:
        {
            "passed": bool,           # 无 HARD 错误则通过
            "hard_errors": list[str], # 必须修复的错误
            "warnings": list[str],    # 建议修复的警告
            "report": str,            # 完整校验报告文本
        }
    """
    files = {
        "pages/index/index.wxml": wxml,
        "pages/index/index.wxss": wxss,
        "pages/index/index.js": js,
    }
    if json_str:
        files["pages/index/index.json"] = json_str

    result = validate_project(files, full_project=False)

    return {
        "passed": result.ok,
        "hard_errors": result.hard_errors,
        "warnings": result.warnings,
        "report": result.report(),
    }


# ---------------------------------------------------------------------------
# Tool 3: 预览小程序页面
# ---------------------------------------------------------------------------

@mcp.tool()
def preview_miniprogram(
        wxml: str,
        wxss: str,
        js: str,
) -> dict:
    """
    将 WXML/WXSS/JS 三件套渲染为 Web 侧手机预览 HTML。

    Args:
        wxml: WXML 结构代码
        wxss: WXSS 样式代码
        js: JS 逻辑代码

    Returns:
        {
            "html": str,              # 可直接在浏览器中打开的完整 HTML
            "preview_available": bool, # 是否成功生成预览
            "error": str,             # 若失败，错误信息
        }
    """
    if render_wxml_html is None:
        return {
            "html": "",
            "preview_available": False,
            "error": "render_wxml.py 未找到，预览功能不可用。",
        }

    try:
        html = render_wxml_html(wxml=wxml, wxss=wxss, js=js)
        return {
            "html": html,
            "preview_available": True,
            "error": "",
        }
    except Exception as e:
        return {
            "html": "",
            "preview_available": False,
            "error": f"预览渲染失败: {str(e)}",
        }


# ---------------------------------------------------------------------------
# Tool 4: 导出小程序 ZIP 工程包
# ---------------------------------------------------------------------------

@mcp.tool()
def export_miniprogram_zip(
        wxml: str,
        wxss: str,
        js: str,
        page_json: str = "",
        project_name: str = "miniprogram_mvp",
) -> dict:
    """
    将页面三件套打包为可导入微信开发者工具的完整 ZIP 工程包。

    Args:
        wxml: WXML 结构代码
        wxss: WXSS 样式代码
        js: JS 逻辑代码
        page_json: 可选的页面 JSON 配置（如 {"usingComponents":{}}）
        project_name: 导出项目名称

    Returns:
        {
            "zip_path": str,          # 生成的 ZIP 文件绝对路径
            "zip_size_kb": float,     # ZIP 文件大小（KB）
            "files_included": list,   # 包内包含的文件列表
            "export_success": bool,
            "error": str,
        }
    """
    # 1. 构建临时项目目录
    tmp_dir = Path(tempfile.mkdtemp(prefix="minipilot_mcp_"))
    project_dir = tmp_dir / project_name
    pages_dir = project_dir / "pages" / "index"
    pages_dir.mkdir(parents=True, exist_ok=True)

    # 2. 写入页面三件套
    (pages_dir / "index.wxml").write_text(wxml, encoding="utf-8")
    (pages_dir / "index.wxss").write_text(wxss, encoding="utf-8")
    (pages_dir / "index.js").write_text(js, encoding="utf-8")
    (pages_dir / "index.json").write_text(page_json or "{}", encoding="utf-8")

    # 3. 写入脚手架（app.json / app.js 等）
    if build_scaffold is not None:
        try:
            build_scaffold(project_dir)
        except Exception:
            _write_minimal_scaffold(project_dir)
    else:
        _write_minimal_scaffold(project_dir)

    # 4. 打包 ZIP
    zip_path = tmp_dir / f"{project_name}.zip"
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in project_dir.rglob("*"):
                if f.is_file():
                    arcname = str(f.relative_to(project_dir))
                    zf.write(f, arcname)

        zip_size = zip_path.stat().st_size / 1024
        files_included = [
            str(f.relative_to(project_dir))
            for f in project_dir.rglob("*")
            if f.is_file()
        ]

        return {
            "zip_path": str(zip_path.resolve()),
            "zip_size_kb": round(zip_size, 2),
            "files_included": files_included,
            "export_success": True,
            "error": "",
        }
    except Exception as e:
        return {
            "zip_path": "",
            "zip_size_kb": 0,
            "files_included": [],
            "export_success": False,
            "error": f"ZIP 导出失败: {str(e)}",
        }


def _write_minimal_scaffold(project_dir: Path) -> None:
    """写入最小脚手架（兜底）"""
    (project_dir / "app.json").write_text(
        json.dumps({"pages": ["pages/index/index"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    (project_dir / "app.js").write_text("App({})\n", encoding="utf-8")
    (project_dir / "app.wxss").write_text("/* global app styles */\n", encoding="utf-8")
    (project_dir / "project.config.json").write_text(
        json.dumps(
            {
                "description": "MiniPilot generated project",
                "packOptions": {"ignore": []},
                "setting": {},
                "compileType": "miniprogram",
                "appid": "touristappid",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Tool 5: 需求澄清（文本推理，不生成代码）
# ---------------------------------------------------------------------------

@mcp.tool()
def clarify_requirement(description: str) -> dict:
    """
    对模糊的小程序需求进行澄清和结构化，提炼场景、风格与功能方向。
    不生成代码，仅返回需求分析结果。

    Args:
        description: 用户的原始需求描述

    Returns:
        {
            "clarified_prompt": str,   # 优化后的结构化需求
            "suggested_style": str,    # 推荐设计风格
            "suggested_features": list, # 推荐功能列表
            "scene_category": str,     # 场景分类
        }
    """
    system_prompt = (
        "你是一位小程序产品经理。请分析用户的需求描述，提炼出：\n"
        "1. 结构化需求描述（用于直接输入代码生成）\n"
        "2. 推荐设计风格\n"
        "3. 推荐功能列表\n"
        "4. 场景分类\n\n"
        "请用 JSON 格式返回，不要包含 markdown 代码块标记：\n"
        '{"clarified_prompt": "...", "suggested_style": "...", '
        '"suggested_features": ["..."], "scene_category": "..."}'
    )

    full_prompt = f"{system_prompt}\n\n用户需求：{description}"

    try:
        raw = call_lmstudio_text(prompt=full_prompt)

        # 尝试提取 JSON（模型可能输出 markdown 代码块 ```json ... ```）
        text = raw.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        parsed = json.loads(text)
        return {
            "clarified_prompt": parsed.get("clarified_prompt", description),
            "suggested_style": parsed.get("suggested_style", "默认"),
            "suggested_features": parsed.get("suggested_features", []),
            "scene_category": parsed.get("scene_category", "通用"),
        }
    except Exception:
        # 兜底：返回原始需求，确保接口不崩
        return {
            "clarified_prompt": description,
            "suggested_style": "默认",
            "suggested_features": [],
            "scene_category": "通用",
        }


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MiniPilot MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="通信协议：stdio（本地客户端直连）或 sse（HTTP 服务）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="SSE 模式下的监听端口（默认 8001）",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        print(f"[MiniPilot MCP] SSE 模式启动于 http://0.0.0.0:{args.port}")
        mcp.run(transport="sse", port=args.port)
    else:
        print("[MiniPilot MCP] stdio 模式启动，等待 MCP 客户端连接...")
        mcp.run(transport="stdio")