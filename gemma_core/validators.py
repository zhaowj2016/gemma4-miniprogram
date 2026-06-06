"""
Gemma Match - 静态校验器 (两天版的真正自动门禁)
=================================================

定位: 这不是逻辑证明器, 不模拟运行时, 只在打包出站前拦住"高频、低级、确定能发现"的错误。
它是 Gemma Match 可信度的核心 —— 上一版那个 zip 里的 <div> / toFixed() / current-index /
YOUR_APPID 全都会被这里自动标红, 而不用你肉眼一个个抓。

设计原则 (很重要):
  - HARD 错误 = 一定错、会编译失败或渲染失败 -> 拦下出站, 触发一次自愈重生成。
  - WARNING  = 可能不对但不致命 -> 只展示, 不拦下载。
    理由: 演示时, "能下载的略有瑕疵 Zip" 永远好过 "被误杀拦下的完美 Zip"。
    真正的编译验证是你人工导微信开发者工具那一步, 校验器只做"防蠢"。

用法 (库):
    from validators import validate_project
    result = validate_project({"app.json": "...", "pages/index/index.wxml": "...", ...})
    if result.ok:        # 没有 HARD 错误
        # 打包出站
    else:
        # 把 result.hard_errors 拼进自愈 prompt, 让 Gemma 重生成

用法 (命令行, 直接体检一个项目目录或 zip):
    python validators.py /path/to/project_dir
    python validators.py /path/to/gemma_match_miniprogram.zip
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# 配置: 白名单 / 黑名单
# ---------------------------------------------------------------------------

ALLOWED_SUFFIXES = {".json", ".js", ".wxml", ".wxss", ".wxs"}

# 模型本轮必须生成的三个页面文件 (脚手架其余文件由后端固定写入, 不让模型碰)
REQUIRED_PAGE_FILES = [
    "pages/index/index.wxml",
    "pages/index/index.wxss",
    "pages/index/index.js",
]

# 一个完整可导入项目应有的四件套 (校验整包时用)
PAGE_QUARTET = [".wxml", ".wxss", ".js", ".json"]

# WXML 里绝不合法的 HTML 标签 (LLM 把网页习惯漏进来的经典错误, 高精度黑名单)
HTML_TAGS_FORBIDDEN = [
    "div", "span", "p", "a", "img", "ul", "ol", "li", "table", "tr", "td", "th",
    "thead", "tbody", "br", "hr", "section", "article", "header", "footer", "nav",
    "main", "aside", "h1", "h2", "h3", "h4", "h5", "h6", "strong", "em", "b", "i",
    "u", "small", " s ", "select", "option", "iframe", "figure", "figcaption",
]

# 第一阶段禁止的真实能力 API -> 命中即 HARD, 触发重生成
FORBIDDEN_APIS = [
    r"wx\.login\b",
    r"wx\.getUserProfile\b",
    r"wx\.getUserInfo\b",
    r"wx\.request\b",
    r"wx\.requestPayment\b",
    r"wx\.getLocation\b",
    r"wx\.chooseLocation\b",
    r"wx\.cloud\b",
    r"wx\.openLocation\b",
]

# 密钥 / 凭证特征 -> HARD, 绝不许出站
SECRET_PATTERNS = [
    r"appsecret",
    r"app_secret",
    r"private[_-]?key",
    r"mch[_-]?key",
    r"merchant[_-]?key",
    r"access[_-]?token",
    r"refresh[_-]?token",
    r"session[_-]?key",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
]


@dataclass
class ValidationResult:
    hard_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """没有 HARD 错误就算通过 (warning 不拦)。"""
        return len(self.hard_errors) == 0

    def err(self, msg: str) -> None:
        self.hard_errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def report(self) -> str:
        lines = []
        status = "PASS (可出站)" if self.ok else "FAIL (需自愈重生成)"
        lines.append(f"=== 静态校验结果: {status} ===")
        if self.hard_errors:
            lines.append(f"\n[HARD 错误 x{len(self.hard_errors)}] (拦下出站):")
            for e in self.hard_errors:
                lines.append(f"  ✗ {e}")
        if self.warnings:
            lines.append(f"\n[WARNING x{len(self.warnings)}] (不拦, 仅提示):")
            for w in self.warnings:
                lines.append(f"  ! {w}")
        if not self.hard_errors and not self.warnings:
            lines.append("  干净, 无任何问题。")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 子校验
# ---------------------------------------------------------------------------

def _check_paths(files: dict[str, str], r: ValidationResult) -> None:
    for path in files:
        if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
            r.err(f"路径不允许是绝对路径: {path}")
        if ".." in path.split("/"):
            r.err(f"路径不允许包含 ../ : {path}")
        suffix = "." + path.rsplit(".", 1)[-1] if "." in path else ""
        if suffix not in ALLOWED_SUFFIXES:
            r.err(f"文件后缀不在白名单内: {path}")


def _check_required_files(files: dict[str, str], r: ValidationResult, full_project: bool) -> None:
    for req in REQUIRED_PAGE_FILES:
        if req not in files:
            r.err(f"缺少必需的页面文件: {req}")
    if full_project:
        for req in ("app.json", "app.js", "app.wxss"):
            if req not in files:
                r.err(f"缺少必需的项目文件: {req}")


def _check_json(files: dict[str, str], r: ValidationResult) -> dict | None:
    app_json = None
    for path, content in files.items():
        if path.endswith(".json"):
            try:
                parsed = json.loads(content)
                if path == "app.json":
                    app_json = parsed
            except json.JSONDecodeError as e:
                r.err(f"JSON 无法解析: {path} ({e.msg} @ line {e.lineno})")
    return app_json


def _check_app_json_pages(app_json: dict | None, files: dict[str, str], r: ValidationResult) -> None:
    if app_json is None:
        return  # 整包校验才有 app.json; 只校验三件套时跳过
    pages = app_json.get("pages")
    if not pages or not isinstance(pages, list):
        r.err("app.json 的 pages 为空或不是数组")
        return
    for page in pages:
        for suffix in PAGE_QUARTET:
            expected = f"{page}{suffix}"
            if expected not in files:
                r.err(f"app.json 声明了页面 {page} 但缺少 {expected}")


def _check_wxml(files: dict[str, str], r: ValidationResult) -> None:
    for path, content in files.items():
        if not path.endswith(".wxml"):
            continue

        # 1) HTML 标签混入 (HARD) —— 上一版的 <div> / <p> 就栽在这
        for tag in HTML_TAGS_FORBIDDEN:
            t = tag.strip()
            if re.search(rf"<\s*{t}(\s|>|/)", content):
                r.err(f"{path}: WXML 里出现了非法 HTML 标签 <{t}> (小程序只认 view/text 等组件)")

        # 2) 数据绑定里调用函数 (HARD) —— 上一版的 {{price.toFixed(2)}} 渲染不出来
        for m in re.finditer(r"\{\{(.*?)\}\}", content, re.DOTALL):
            expr = m.group(1)
            if re.search(r"\w+\s*\(", expr):
                snippet = expr.strip()[:40]
                r.err(f"{path}: 数据绑定里有函数调用, WXML 不支持: {{{{ {snippet} }}}} "
                      f"(格式化请在 JS 里做好, 或用 WXS)")

        # 3) swiper 用了 current-index (WARNING) —— 正确属性是 current
        if re.search(r"current-index\s*=", content):
            r.warn(f"{path}: <swiper> 属性应为 current, 不是 current-index (当前绑定会静默失效)")

        # 4) 极简未闭合检查 (WARNING, 启发式, 可能误报, 故只警告)
        for tag in ("view", "text", "swiper", "scroll-view", "form", "swiper-item"):
            opens = len(re.findall(rf"<{tag}(\s|>)", content))
            closes = len(re.findall(rf"</{tag}>", content))
            if opens != closes:
                r.warn(f"{path}: <{tag}> 开合标签数量不一致 (开{opens}/合{closes}), 请人工确认")


def _check_wxss(files: dict[str, str], r: ValidationResult) -> None:
    for path, content in files.items():
        if not path.endswith(".wxss"):
            continue
        if content.count("{") != content.count("}"):
            r.warn(f"{path}: WXSS 大括号数量不匹配 ({content.count('{')}/{content.count('}')})")
        if re.search(r"\bobject-fit\s*:", content):
            r.warn(f"{path}: object-fit 在小程序 image 上无效, 请改用 image 的 mode 属性")


def _check_js_basic(files: dict[str, str], r: ValidationResult) -> None:
    for path, content in files.items():
        if not path.endswith(".js"):
            continue
        if path.endswith("app.js"):
            if "App(" not in content:
                r.warn(f"{path}: 未发现 App( 构造")
            continue
        # 页面 js 至少要有 Page( 或 Component(
        if "Page(" not in content and "Component(" not in content:
            r.err(f"{path}: 未发现 Page( 或 Component( 构造")
        # 大括号 / 圆括号粗配平 (WARNING)
        if content.count("{") != content.count("}"):
            r.warn(f"{path}: JS 花括号数量不匹配, 可能有语法错误")


def _check_event_binding(files: dict[str, str], r: ValidationResult) -> None:
    """把 WXML 里的事件 handler 名跟同页 JS 对账。WARNING 级 —— 同时认 `name(` 和
    `name:` 两种写法, 避免把合法的 `handleTap: function(){}` 误杀。"""
    # 按页面目录分组
    by_dir: dict[str, dict[str, str]] = {}
    for path, content in files.items():
        d = path.rsplit("/", 1)[0] if "/" in path else ""
        by_dir.setdefault(d, {})[path] = content

    for d, group in by_dir.items():
        wxml = next((c for p, c in group.items() if p.endswith(".wxml")), None)
        js = next((c for p, c in group.items() if p.endswith(".js")), None)
        if wxml is None or js is None:
            continue
        handlers = set(re.findall(r"(?:bind|catch)(?:tap|input|change|submit|confirm|blur|focus|scroll)\s*=\s*[\"']([\w]+)[\"']", wxml))
        handlers |= set(re.findall(r"bind:\w+\s*=\s*[\"']([\w]+)[\"']", wxml))
        for h in handlers:
            if not re.search(rf"\b{re.escape(h)}\s*[:(]", js):
                r.warn(f"{d or '<root>'}: WXML 绑定了事件 {h}, 但同页 JS 里没找到对应方法")


def _check_security(files: dict[str, str], r: ValidationResult) -> None:
    for path, content in files.items():
        low = content.lower()
        for pat in SECRET_PATTERNS:
            if re.search(pat, low if not pat.startswith("-----") else content):
                r.err(f"{path}: 命中密钥/凭证特征 ({pat}) —— 绝不许出站, 触发重生成")
        for pat in FORBIDDEN_APIS:
            if re.search(pat, content):
                r.err(f"{path}: 使用了第一阶段禁止的真实能力 API ({pat}) —— 请降级为本地 mock")


def _check_project_config(files: dict[str, str], r: ValidationResult) -> None:
    cfg = files.get("project.config.json")
    if cfg is None:
        return
    if "YOUR_APPID" in cfg or '"appid": ""' in cfg or '"appid":""' in cfg:
        r.warn('project.config.json 的 appid 是占位符 —— 建议改成 "touristappid" 以便无账号干净导入')


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def validate_project(files: dict[str, str], full_project: bool | None = None) -> ValidationResult:
    """
    files: {相对路径: 文件内容字符串}
    full_project: True=按完整项目校验(查 app.json/四件套); None=自动判断(有 app.json 则按整包)
    """
    r = ValidationResult()
    if full_project is None:
        full_project = "app.json" in files

    _check_paths(files, r)
    _check_required_files(files, r, full_project)
    app_json = _check_json(files, r)
    _check_app_json_pages(app_json, files, r)
    _check_wxml(files, r)
    _check_wxss(files, r)
    _check_js_basic(files, r)
    _check_event_binding(files, r)
    _check_security(files, r)
    _check_project_config(files, r)
    return r


def _load_from_path(p: str) -> dict[str, str]:
    path = Path(p)
    files: dict[str, str] = {}
    if path.is_file() and path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.endswith("/"):
                    continue
                files[name] = z.read(name).decode("utf-8", errors="replace")
    elif path.is_dir():
        for f in path.rglob("*"):
            if f.is_file():
                files[str(f.relative_to(path))] = f.read_text("utf-8", errors="replace")
    else:
        raise SystemExit(f"路径不是目录也不是 zip: {p}")
    return files


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("用法: python validators.py <项目目录或 zip>")
    files = _load_from_path(sys.argv[1])
    print(f"载入 {len(files)} 个文件\n")
    print(validate_project(files).report())
