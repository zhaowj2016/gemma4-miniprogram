"""
Shared WXML → HTML rendering helpers used by app.py and showcase.py.
"""
import re
import json
import mimetypes
from pathlib import Path

PLACEHOLDER_IMG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='375' height='200'%3E%3Crect width='375' height='200' fill='%23e8eaed'/%3E%3Ctext x='188' y='107' text-anchor='middle' fill='%23aaa' font-size='13' font-family='Arial'%3EImage%3C/text%3E%3C/svg%3E"


def _adapt_wxss_for_html(css: str) -> str:
    """Adapt WeChat Mini Program CSS selectors/properties for HTML rendering.

    Key design decision: We do NOT blindly convert position:fixed to position:sticky.
    Instead, .screen gets transform:translateZ(0) which creates a CSS containing
    block for fixed-position descendants.  This preserves the original layout intent
    (navbar fixed at top, actionbar/tabbar at bottom) while scoping them inside the
    phone screen container rather than the browser viewport.
    """
    css = re.sub(r'\bpage\b(\s*\{)', r':root, .screen\1', css)
    # ── Keep position:fixed as-is (containment handled by .screen transform) ──
    css = re.sub(r'env\([^)]+\)', '0px', css)
    # vh units: phone screen is 640px, so 1vh = 6.4px
    css = re.sub(r'\b(\d+(?:\.\d+)?)vh\b', lambda m: f'{float(m.group(1)) * 6.4:.1f}px', css)
    # Rename swiper component selectors to match the HTML classes we inject.
    # Use negative lookbehind/ahead to avoid corrupting class names like
    # .hero-swiper or .store-swiper — those are user-defined and should stay intact.
    css = re.sub(r'(?<![-\w])swiper-item(?![-\w])', '.wx-swiper-item', css)
    css = re.sub(r'(?<![-\w])swiper(?![-\w])', '.wx-swiper', css)
    # ── Cap page-level padding-bottom to prevent flex container shrinkage ──
    # Original WXSS .page { padding-bottom: 240rpx } → 120px on .screen.
    # In the flex layout, .screen-footer already provides bottom spacing —
    # large padding-bottom steals space from .screen-scroll and causes short pages.
    css = re.sub(
        r'(padding-bottom\s*:\s*)(\d+(?:\.\d+)?)\s*(r?px)',
        lambda m: f'{m.group(1)}{min(float(m.group(2)) * (0.5 if m.group(3) == "rpx" else 1), 16):.1f}px',
        css,
    )
    # ── Scope any bare "page" or "body" selectors that weren't caught above ──
    css = re.sub(r'(?<![-.\w#])page(?![-\w])', '.screen', css)
    return css

PHONE_SHELL_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{background:#e5e5ea;min-height:100%;display:flex;justify-content:center;padding:12px 0;margin:0;}
.phone{
  width:375px;background:#1a1a1a;border-radius:50px;
  padding:12px 8px 10px;
  box-shadow:0 20px 60px rgba(0,0,0,.4),inset 0 0 0 1px rgba(255,255,255,.1);
  flex-shrink:0;
  display:inline-block;
}
.status-bar{
  height:26px;display:flex;align-items:center;
  justify-content:space-between;padding:0 18px 6px;
}
.status-bar span{color:#fff;font-size:11px;font-weight:600;}
.notch{width:80px;height:14px;background:#000;border-radius:8px;margin:0 auto;}
/* ── 新手机壳结构: flex column ──
   .screen = flex容器
     .screen-scroll = flex:1, overflow-y:auto  (滚动内容区)
     .screen-footer = flex-shrink:0  (固定底部, 存放 actionbar + tabbar) */
.screen{
  width:359px;
  min-height:480px;max-height:1200px;
  border-radius:38px;
  overflow:hidden;
  background:#F5F7FA;
  display:flex;
  flex-direction:column;
}
.screen-scroll{
  flex:1;
  overflow-y:auto;overflow-x:hidden;
  -webkit-overflow-scrolling:touch;
}
.screen-footer{
  flex-shrink:0;
  z-index:100;
  background:#fff;
}
/* ── screen-footer: 强制稳定布局, 不依赖 generated WXSS ── */
.screen-footer{
  border-top:1px solid rgba(0,0,0,0.06);
}
.screen-footer .actionbar{
  position:static !important;
  width:100% !important;
  left:auto !important;
  bottom:auto !important;
  top:auto !important;
  /* 确保 actionbar 在 footer 内部正常流 */
}
/* ── tabbar 强制 grid 四栏横排, 绝不竖向堆叠 ── */
.screen-footer .tabbar{
  position:static !important;
  width:100% !important;
  left:auto !important;
  bottom:auto !important;
  top:auto !important;
  display:grid !important;
  grid-template-columns:repeat(4, 1fr);
  height:56px;
  background:#fff;
  border-top:1px solid #eee;
  z-index:100;
}
.screen-footer .tabbar-item{
  display:flex !important;
  flex-direction:column !important;
  align-items:center !important;
  justify-content:center !important;
  flex:0 0 auto !important;  /* 不要 flex:1 在 grid 里撑破 */
  color:#999;
  font-size:10px;
  cursor:pointer;
  user-select:none;
  transition:color .15s;
}
.screen-footer .tabbar-item:hover{color:#1a73e8;}
.screen-footer .tab-active,
.screen-footer .tab-active *{color:#1a73e8 !important;}
.screen-footer .tabbar-label{
  font-size:10px;
  margin-top:2px;
}
/* tabbar icon (nav-ic) */
.screen-footer [class*="nav-ic"]{
  width:22px;height:22px;
  margin-bottom:1px;
}
/* ── page-scroll padding-bottom: 预留底部固定层空间 ── */
.screen-scroll{padding-bottom:16px;}
.screen *{
  font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Helvetica,Arial,
              'PingFang SC','Microsoft YaHei',sans-serif;
  font-size:14px;
}
.screen button{display:flex;align-items:center;justify-content:center;width:100%;cursor:pointer;border:none;outline:none;}
.screen input{display:block;width:100%;border:1px solid #eee;border-radius:8px;padding:8px 12px;font-size:14px;background:#fff;color:#222;}
.screen textarea{display:block;width:100%;border:1px solid #eee;border-radius:8px;padding:8px 12px;font-size:14px;background:#fff;color:#222;font-family:inherit;resize:vertical;min-height:60px;}
.screen img{max-width:100%;display:block;}
/* ── 微信 scroll-view 模拟 ── */
.wx-scroll-x{
  overflow-x:auto;overflow-y:visible;
  white-space:nowrap;
  -webkit-overflow-scrolling:touch;
  scrollbar-width:none;
  display:flex;flex-wrap:nowrap;
  align-items:flex-start;
  /* ── 横向滚动核心规则 ──
     子项不压缩、不换行、固定宽度，溢出部分通过滚动查看。
     这是 HTML 预览中模拟小程序 scroll-view 的关键模式。 */
  padding:4px 24px 14px 0;  /* 右侧留足空间，最后一项完整可见 */
  gap:10px;                  /* 子项之间统一间距 */
}
.wx-scroll-x::-webkit-scrollbar{display:none;}
.wx-scroll-x > *{
  flex:0 0 auto !important;  /* 绝不压缩 */
  white-space:normal;
  vertical-align:top;
  flex-shrink:0 !important;
}
/* ── 日期/卡片类子项：给足最小宽度，不挤压内容 ── */
.wx-scroll-x .date-item,
.wx-scroll-x .sty-card{
  min-width:64px;
  flex-shrink:0 !important;
}
/* 最后一项加额外安全间距 */
.wx-scroll-x > *:last-child{margin-right:8px;}
/* 内层 flex row 撑开到内容全宽 */
.wx-scroll-x > div{flex-shrink:0 !important;min-width:0;}
.wx-scroll-y{overflow-y:auto;overflow-x:hidden;-webkit-overflow-scrolling:touch;}
.wx-swiper{position:relative;overflow:hidden;width:100%;min-height:80px;}
.wx-swiper-item{display:none;width:100%;height:100%;position:relative;}
.wx-swiper-item:first-child{display:block;}
/* ── Swiper image absolute containment ── Images are removed from flow — they can NEVER expand the swiper or pollute layout below. object-fit:cover handles ANY aspect ratio (landscape, portrait, square). */
.wx-swiper-item img{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;}
.screen img{vertical-align:top;}
.screen button{padding:0;}
/* wx-t is a transparent wrapper for rebindable text */
wx-t{display:inline;font:inherit;color:inherit;}
/* ── Image Layout Constraints: prevent oversized/overflow images ── */
/* Avatar safety: limit to sensible sizes, prevent giant circles */
[class*="avatar"],.mine-avatar,.user-avatar,.review-avatar,.sty-avatar{
  width:40px;height:40px;max-width:40px;max-height:40px;
  border-radius:50%;object-fit:cover;flex-shrink:0;
}
/* Larger avatar variants (profile pages) — capped at 72px */
.mine-hero [class*="avatar"],.mine-top [class*="avatar"],
.user-profile [class*="avatar"],.profile [class*="avatar"]{
  width:64px;height:64px;max-width:64px;max-height:64px;
}
/* Review images: constrain to card width, prevent overflow into text */
.review-img,.review-imgs img{max-width:100%;max-height:200px;object-fit:cover;border-radius:8px;}
/* Hero / swiper images: fixed height to prevent variable sizing */
.hero-img,.wx-swiper .wx-swiper-item img{width:100%;height:200px;object-fit:cover;}
/* Card image safety: never overflow card body */
.card-img,.feature-img,.highlight-card img,.bundle-img,.rec-img,.origin-img,.guide-img{
  width:100%;height:140px;object-fit:cover;border-radius:8px 8px 0 0;
}
/* Weight/color/roast selection images: small fixed size */
.color-img,.weight-img{width:72px;height:72px;object-fit:cover;border-radius:8px;flex-shrink:0;}
/* FAQ accordion arrow rotation */
.faq-arrow{display:inline-block;width:8px;height:8px;border-right:2px solid #999;border-bottom:2px solid #999;transform:rotate(45deg);transition:transform .25s;margin-left:auto;}
.arrow-up,.faq-arrow.up{transform:rotate(-135deg);}
/* ── Half-page prevention: minimum content height ── */
.screen-scroll{min-height:380px;}
.pane{min-height:360px;}
/* ── Header/long text overflow prevention ── */
[class*="hero-title"],.hero-title,[class*="nav-title"],.nav-title{
  max-width:100%;overflow-wrap:break-word;word-break:break-word;
  overflow:hidden;text-overflow:ellipsis;
}
/* ── Carousel hero: avoid overriding generated height:100% ── */
/* Let the swiper inherit its parent .hero height (typically 280-350px).
   Only constrain the min-height, not the height itself. */
.wx-swiper.hero-swiper{min-height:200px;}
.wx-swiper.hero-swiper img{height:100%;object-fit:cover;}
/* ── Bottom purchase bar: balanced CTA layout ── */
/* IMPORTANT: Do NOT use !important on display — it prevents the JS runtime
   from hiding the actionbar via style.display='none' when data-wx-if=false.
   The specificity (0,2,0) already beats plain .actionbar (0,1,0). */
.screen-footer .actionbar{
  display:flex;align-items:center;
  height:auto !important;min-height:52px !important;
  padding:8px 12px !important;gap:8px !important;
  background:#fff !important;box-sizing:border-box !important;
}
.screen-footer .action-icons{
  display:flex !important;gap:8px !important;flex-shrink:0 !important;
}
.screen-footer .action-btns{
  display:flex !important;align-items:center !important;
  flex:1 !important;justify-content:flex-end !important;gap:8px !important;
}
.screen-footer .qty-selector{
  display:flex !important;align-items:center !important;
  border-radius:20px !important;background:#f5f5f5 !important;padding:2px !important;
}
.screen-footer .qty-btn{
  width:30px !important;height:30px !important;border-radius:50% !important;
  display:flex !important;align-items:center !important;justify-content:center !important;
  font-weight:600 !important;cursor:pointer !important;border:none !important;background:transparent !important;
}
.screen-footer .btn-cart,.screen-footer .btn-buy{
  height:36px !important;border-radius:18px !important;border:none !important;
  font-size:13px !important;font-weight:600 !important;cursor:pointer !important;
  display:flex !important;align-items:center !important;justify-content:center !important;
}
.screen-footer .btn-cart{background:#f0f0f0 !important;color:#333 !important;padding:0 16px !important;}
.screen-footer .btn-buy{background:linear-gradient(135deg,#1a73e8,#1557b0) !important;color:#fff !important;padding:0 16px !important;}
.screen-footer .btn-buy-main{font-size:13px !important;font-weight:600 !important;}
.screen-footer .btn-buy-sub{font-size:11px !important;opacity:0.85 !important;margin-left:4px !important;}
/* ── Booking summary bar: readable layout ── */
.screen-footer .ab-summary{
  flex:1 !important;display:flex !important;flex-direction:column !important;
  overflow:hidden !important;margin:0 8px !important;
}
.screen-footer .ab-summary-text{
  font-size:12px !important;font-weight:600 !important;
  white-space:nowrap !important;overflow:hidden !important;text-overflow:ellipsis !important;
}
.screen-footer .ab-btn{
  flex-shrink:0 !important;height:38px !important;border-radius:19px !important;
  padding:0 20px !important;font-size:14px !important;font-weight:600 !important;
  border:none !important;cursor:pointer !important;
}
"""


# ── JS data 提取 ─────────────────────────────────────────────────────────────

def _strip_js_comments(s: str) -> str:
    """Strip // and /* */ comments, skipping content inside string literals."""
    result: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        # String literal — copy verbatim until closing quote (handle escapes)
        if c in ('"', "'"):
            q = c
            result.append(c)
            i += 1
            while i < n:
                ch = s[i]
                result.append(ch)
                if ch == '\\':
                    i += 1
                    if i < n:
                        result.append(s[i])
                        i += 1
                    continue
                if ch == q:
                    i += 1
                    break
                i += 1
        elif c == '/' and i + 1 < n:
            nxt = s[i + 1]
            if nxt == '/':
                # Line comment — skip to end of line
                while i < n and s[i] != '\n':
                    i += 1
            elif nxt == '*':
                # Block comment — skip to */
                i += 2
                while i < n - 1:
                    if s[i] == '*' and s[i + 1] == '/':
                        i += 2
                        break
                    i += 1
            else:
                result.append(c)
                i += 1
        else:
            result.append(c)
            i += 1
    return ''.join(result)


def extract_js_data(js: str) -> dict:
    m = re.search(r'\bdata\s*:\s*\{', js)
    if not m:
        return {}
    start = m.end() - 1
    depth, i = 0, start
    while i < len(js):
        if js[i] == '{':
            depth += 1
        elif js[i] == '}':
            depth -= 1
            if depth == 0:
                raw = js[start: i + 1]
                break
        i += 1
    else:
        return {}
    try:
        raw = _strip_js_comments(raw)
        raw = re.sub(
            r"'([^']*)'",
            lambda m2: '"' + m2.group(1).replace('"', '\\"') + '"',
            raw,
        )
        raw = re.sub(r",\s*([\]}])", r"\1", raw)
        raw = re.sub(r"(?m)^(\s+)([a-zA-Z_$][\w$]*)\s*:", r'\1"\2":', raw)
        raw = re.sub(r"([{,]\s*)([a-zA-Z_$][\w$]*)\s*:",
                     lambda m2: m2.group(1) + '"' + m2.group(2) + '":', raw)
        return json.loads(raw)
    except Exception:
        return {}


# ── rpx → px ─────────────────────────────────────────────────────────────────

def rpx(css: str) -> str:
    return re.sub(
        r"([\d.]+)rpx",
        lambda m: f"{float(m.group(1)) * 0.5:.1f}px",
        css,
    )


# ── 绑定求值 helpers ──────────────────────────────────────────────────────────

def _resolve_path(key_path: str, data: dict):
    val = data
    for part in key_path.strip().split("."):
        if "[" in part:
            # Handle bracket notation: menu[activeTab] or items[0]
            base, idx_str = part.split("[", 1)
            idx_str = idx_str.rstrip("]")
            if isinstance(val, dict):
                val = val.get(base)
            else:
                return None
            if val is None:
                return None
            # Resolve the index — it may be a variable name or a literal
            resolved = _resolve_path(idx_str, data)
            if resolved is None:
                try:
                    resolved = int(idx_str)
                except ValueError:
                    resolved = idx_str.strip("'\"")
            if isinstance(val, dict):
                if not isinstance(resolved, (str, int, float, bool)):
                    return None
                val = val.get(resolved) or val.get(str(resolved))
            elif isinstance(val, list):
                try:
                    val = val[int(resolved)]
                except (IndexError, TypeError, ValueError):
                    return None
            else:
                return None
        elif isinstance(val, dict):
            val = val.get(part)
        else:
            return None
    return val


def _to_num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _is_truthy(val) -> bool:
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    s = str(val).strip()
    return s not in ("", "false", "0", "[]", "[数据]") and not re.match(r'^\[[\w.]+\]$', s)


def _eval_condition(expr: str, data: dict) -> bool:
    expr = expr.strip()
    # Logical OR — lowest precedence, evaluate left-to-right
    if " || " in expr:
        return any(_eval_condition(part, data) for part in expr.split(" || "))
    # Logical AND
    if " && " in expr:
        return all(_eval_condition(part, data) for part in expr.split(" && "))
    # Logical NOT prefix  (!expr, but not !== or !=)
    if expr.startswith("!") and not expr.startswith("!="):
        return not _eval_condition(expr[1:], data)
    # Comparison operators (must check multi-char ops before single-char)
    for op, fn in [
        ("===", lambda a, b: str(a) == str(b)),
        ("!==", lambda a, b: str(a) != str(b)),
        (">=",  lambda a, b: _to_num(a) >= _to_num(b)),
        ("<=",  lambda a, b: _to_num(a) <= _to_num(b)),
        (">",   lambda a, b: _to_num(a) > _to_num(b)),
        ("<",   lambda a, b: _to_num(a) < _to_num(b)),
        ("==",  lambda a, b: str(a) == str(b)),
        ("!=",  lambda a, b: str(a) != str(b)),
    ]:
        if op in expr:
            left, right = expr.split(op, 1)
            lv = _resolve_path(left.strip(), data)
            if lv is None:
                lv = left.strip().strip("'\"")
            rv = _resolve_path(right.strip(), data)
            if rv is None:
                rv = right.strip().strip("'\"")
            try:
                return fn(lv, rv)
            except Exception:
                return False
    return _is_truthy(_resolve_path(expr, data))


# ── Class 表达式提取 (setData 后可重算) ──────────────────────────────────────────

def _html_attr(value: str) -> str:
    return (
        (value or "")
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _extract_class_expr(class_attr_value: str) -> str:
    """从 class="X {{ expr }} Y" 提取 expr 部分。

    - 把字面量 base class 放进 data-wx-class-base
    - 把每个 expr 分别放进 data-wx-class-expr-N, 避免多个三元表达式被拼成错误的 JS
    - 返回重写后的 class="X Y" + data-* 属性
    """
    parts = re.split(r'(\{\{[^}]+\}\})', class_attr_value)
    base_parts = []
    expr_parts = []
    for p in parts:
        if p.startswith('{{') and p.endswith('}}'):
            expr_parts.append(p[2:-2].strip())
        else:
            base_parts.append(p)
    base_class = ''.join(base_parts).strip()
    if not expr_parts:
        return f'class="{class_attr_value}"'
    expr_attrs = " ".join(
        f'data-wx-class-expr-{idx}="{_html_attr(expr)}"'
        for idx, expr in enumerate(expr_parts)
    )
    return (
        f'class="{_html_attr(base_class)}" '
        f'data-wx-class-base="{_html_attr(base_class)}" '
        f'data-wx-class-expr-count="{len(expr_parts)}" '
        f'{expr_attrs}'
    )


# ── 模板插值 ──────────────────────────────────────────────────────────────────

_CMP_RE = re.compile(r'===|!==|>=|<=|\s[<>]\s')


def fill_bindings(text: str, data: dict) -> str:
    def resolve(m):
        expr = m.group(1).strip()
        if expr in ("true", "false"):
            return expr
        if expr in ("null", "undefined"):
            return ""
        if re.match(r'^-?\d+(\.\d+)?$', expr):
            return expr
        # ── Class toggle guard: expressions like "activeTab === item.key ? 'on' : ''"
        # must pass through as raw {{...}} so _extract_class_expr can capture them
        # for the JS runtime to re-evaluate after setData.
        if '?' in expr and _CMP_RE.search(expr):
            return "{{" + expr + "}}"
        ternary_m = re.match(r"(.+?)\s*\?\s*'([^']*)'\s*:\s*'([^']*)'", expr)
        if ternary_m:
            cond_expr, true_val, false_val = ternary_m.groups()
            return true_val if _eval_condition(cond_expr.strip(), data) else false_val
        # Route comparison operators through _eval_condition so loop-body
        # conditions like {{item.category === activeCategory}} evaluate correctly.
        # BUT: ternary class toggles (X === Y ? 'A' : 'B') must pass through
        # untouched so _extract_class_expr can capture them for JS runtime.
        if _CMP_RE.search(expr) and '?' not in expr:
            return "true" if _eval_condition(expr, data) else "false"
        if any(c in expr for c in "?|&!+-*/"):
            return ""
        val = _resolve_path(expr, data)
        if val is None:
            return f"[{expr.split('.')[-1].strip()}]"
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, list):
            return "[数据]"
        return str(val)
    return re.sub(r"\{\{([^{}]+)\}\}", resolve, text)


# ── wx:for 展开 ───────────────────────────────────────────────────────────────

def _find_matching_close(html: str, tag: str, from_pos: int) -> tuple:
    depth = 1
    pos = from_pos
    open_re  = re.compile(rf'<{tag}\b',  re.IGNORECASE)
    close_re = re.compile(rf'</{tag}>', re.IGNORECASE)
    while depth > 0 and pos < len(html):
        nxt_open  = open_re.search(html, pos)
        nxt_close = close_re.search(html, pos)
        if nxt_close is None:
            return len(html), len(html)
        if nxt_open and nxt_open.start() < nxt_close.start():
            depth += 1
            pos = nxt_open.end()
        else:
            depth -= 1
            if depth == 0:
                return nxt_close.start(), nxt_close.end()
            pos = nxt_close.end()
    return pos, pos


def expand_for_loops(html: str, data: dict) -> str:
    open_pat = re.compile(r'<(div|span)\b[^>]*\s+wx:for="\{\{([^}]+)\}\}"[^>]*>')
    result = []
    pos = 0
    for m in open_pat.finditer(html):
        if m.start() < pos:
            continue
        tag      = m.group(1)
        list_key = m.group(2).strip()
        open_tag = m.group(0)
        body_end, close_end = _find_matching_close(html, tag, m.end())
        body      = html[m.end(): body_end]
        close_tag = html[body_end: close_end]
        result.append(html[pos: m.start()])
        pos = close_end
        alias_m    = re.search(r'wx:for-item="([^"]+)"', open_tag)
        item_alias = alias_m.group(1) if alias_m else "item"
        clean_open = re.sub(r'\s+wx:[\w-]+(?:="[^"]*")?', "", open_tag)

        # ── dict[variable] pattern: pre-render all Tab sections ──────────────
        # e.g. wx:for="{{menu[activeTab]}}" → render menu.tasting + menu.alacarte
        bracket_m = re.match(r'^(\w+)\[(\w+)\]$', list_key)
        if bracket_m:
            dict_name, var_name = bracket_m.groups()
            dict_val    = _resolve_path(dict_name, data)
            current_val = _resolve_path(var_name, data)
            if isinstance(dict_val, dict) and len(dict_val) > 1:
                all_sections = []
                for section_key, section_items in dict_val.items():
                    if not isinstance(section_items, list):
                        continue
                    is_active = str(section_key) == str(current_val)
                    hidden = "" if is_active else ' style="display:none"'
                    item_parts = []
                    for idx, item in enumerate(section_items[:8]):
                        item_data     = {**data, item_alias: item, "item": item, "index": idx}
                        body_exp      = expand_for_loops(body, item_data)
                        filled        = fill_bindings(body_exp, item_data)
                        item_json = _html_attr(json.dumps(item, ensure_ascii=False, separators=(',', ':')))
                        tagged_open = clean_open[:-1] + f' data-wx-item="{item_json}" data-wx-index="{idx}">'
                        filled_open   = fill_bindings(tagged_open, item_data)
                        item_parts.append(filled_open + filled + close_tag)
                    all_sections.append(
                        f'<div data-tab-section="{section_key}" data-tab-var="{var_name}"{hidden}>'
                        + "".join(item_parts) + "</div>"
                    )
                result.append("".join(all_sections))
                continue  # skip normal processing

        # ── Normal list rendering ─────────────────────────────────────────────
        items = _resolve_path(list_key, data)
        if not isinstance(items, list):
            items = []
        items = items[:8]  # show up to 8 items (scrollable area needs enough items)
        parts = []
        for idx, item in enumerate(items):
            item_data     = {**data, item_alias: item, "item": item, "index": idx}
            body_expanded = expand_for_loops(body, item_data)
            filled        = fill_bindings(body_expanded, item_data)
            # ── Inject data-wx-item so JS runtime can re-evaluate class exprs ──
            item_json = _html_attr(json.dumps(item, ensure_ascii=False, separators=(',', ':')))
            tagged_open = clean_open[:-1] + f' data-wx-item="{item_json}" data-wx-index="{idx}">'
            filled_open = fill_bindings(tagged_open, item_data)
            parts.append(filled_open + filled + close_tag)
        result.append("".join(parts))
    result.append(html[pos:])
    return "".join(result)


# ── wx:if 条件显隐 ────────────────────────────────────────────────────────────

def apply_wx_if(html: str, data: dict | None = None) -> str:
    """Evaluate wx:if conditions using proper nested-tag matching."""

    def _process(html: str, pat: re.Pattern, handler) -> str:
        result = []
        pos = 0
        for m in pat.finditer(html):
            if m.start() < pos:
                continue
            tag = m.group(1)
            body_end, close_end = _find_matching_close(html, tag, m.end())
            body = html[m.end():body_end]
            result.append(html[pos:m.start()])
            pos = close_end
            result.append(handler(m, tag, body))
        result.append(html[pos:])
        return "".join(result)

    # Pattern A: still has {{expr}} — evaluate against data, keep in DOM
    if data is not None:
        pat_raw = re.compile(
            r'<(div|span)\b([^>]*?)\s+wx:if="\{\{([^}]+)\}\}"([^>]*?)>'
        )
        def handle_raw(m, tag, body):
            pre, expr, post = m.group(2), m.group(3), m.group(4)
            try:
                show = _eval_condition(expr.strip(), data)
            except Exception:
                show = True
            safe_expr = expr.strip().replace('"', '&quot;')
            hidden = '' if show else ' style="display:none"'
            return f'<{tag}{pre}{post} data-wx-if="{safe_expr}"{hidden}>{body}</{tag}>'
        for _ in range(4):
            new = _process(html, pat_raw, handle_raw)
            if new == html:
                break
            html = new

    # Pattern B: after fill_bindings — plain-string condition
    pat_plain = re.compile(
        r'<(div|span)\b([^>]*?)\s+wx:if="([^"]*)"([^>]*?)>'
    )
    def handle_plain(m, tag, body):
        pre, cond, post = m.group(2), m.group(3), m.group(4)
        c = cond.strip()
        is_falsy = not c or c in ("false", "0") or re.match(r'^\[[\w.]+\]$', c)
        if is_falsy:
            return ""
        return f"<{tag}{pre}{post}>{body}</{tag}>"
    for _ in range(3):
        new = _process(html, pat_plain, handle_plain)
        if new == html:
            break
        html = new
    return html


# ── WXML → HTML ──────────────────────────────────────────────────────────────

def _handle_scroll_view(match) -> str:
    """Convert <scroll-view ...> to <div> with scroll-x/y classes."""
    attrs = match.group(1)
    has_scroll_x = bool(re.search(r'scroll-x\s*=\s*"(?:true|1|yes)"', attrs, re.IGNORECASE))
    has_scroll_y = bool(re.search(r'scroll-y\s*=\s*"(?:true|1|yes)"', attrs, re.IGNORECASE))
    # Default: scroll-view without explicit scroll-x scrolls vertically
    if not has_scroll_x and not has_scroll_y:
        has_scroll_y = True

    css_classes = []
    if has_scroll_x:
        css_classes.append("wx-scroll-x")
    if has_scroll_y:
        css_classes.append("wx-scroll-y")

    cls_m = re.search(r'\sclass="([^"]*)"', attrs)
    if cls_m:
        existing = cls_m.group(1).split()
        for c in css_classes:
            if c not in existing:
                existing.append(c)
        attrs = attrs[:cls_m.start()] + f' class="{" ".join(existing)}"' + attrs[cls_m.end():]
    elif css_classes:
        attrs = f' class="{" ".join(css_classes)}"{attrs}'

    # Strip scroll-x/scroll-y attrs (no HTML equivalents)
    attrs = re.sub(r'\s+scroll-[xy]\s*=\s*"[^"]*"', '', attrs, flags=re.IGNORECASE)
    attrs = re.sub(r'\s+scroll-into-view\s*=\s*"[^"]*"', '', attrs, flags=re.IGNORECASE)
    attrs = re.sub(r'\s+scroll-with-animation\s*=\s*"[^"]*"', '', attrs, flags=re.IGNORECASE)
    attrs = re.sub(r'\s+enable-flex\s*=\s*"[^"]*"', '', attrs, flags=re.IGNORECASE)
    return f"<div{attrs}>"


def wxml_to_html(wxml: str, data: dict) -> str:
    h = wxml
    # ── Step 0: scroll-view → div with scroll-x/y classes (before generic tag_map) ──
    h = re.sub(r'<scroll-view\b([^>]*)>', _handle_scroll_view, h)
    h = re.sub(r'</scroll-view>', r'</div>', h)

    # Handle swiper before the generic tag_map so they get identifying classes
    def merge_component_class(html_tag: str, wx_class: str):
        def repl(m):
            attrs = m.group(1)
            cls_m = re.search(r'\sclass="([^"]*)"', attrs)
            if cls_m:
                classes = cls_m.group(1).split()
                if wx_class not in classes:
                    classes.insert(0, wx_class)
                attrs = attrs[:cls_m.start()] + f' class="{" ".join(classes)}"' + attrs[cls_m.end():]
            else:
                attrs = f' class="{wx_class}"{attrs}'
            return f"<{html_tag}{attrs}>"
        return repl

    h = re.sub(r'<swiper-item\b([^>]*)>', merge_component_class("div", "wx-swiper-item"), h)
    h = re.sub(r'</swiper-item>', r'</div>', h)
    # Custom swiper handler: detect indicator-dots and inject data-has-dots
    def _handle_swiper(match):
        attrs = match.group(1)
        has_dots = bool(re.search(r'\bindicator-dots\b', attrs))
        cls_m = re.search(r'\sclass="([^"]*)"', attrs)
        if cls_m:
            classes = cls_m.group(1).split()
            if 'wx-swiper' not in classes:
                classes.insert(0, 'wx-swiper')
            attrs = attrs[:cls_m.start()] + f' class="{" ".join(classes)}"' + attrs[cls_m.end():]
        else:
            attrs = f' class="wx-swiper"{attrs}'
        if has_dots:
            attrs += ' data-has-dots="true"'
        return f"<div{attrs}>"
    h = re.sub(r'<swiper\b([^>]*)>', _handle_swiper, h)
    h = re.sub(r'</swiper>', r'</div>', h)
    tag_map = [
        ("block",       "div"),
        ("text",        "span"),
        ("view",        "div"),
    ]
    for wx_tag, html_tag in tag_map:
        h = re.sub(rf"<{wx_tag}\b", f"<{html_tag}", h)
        h = re.sub(rf"</{wx_tag}>", f"</{html_tag}>", h)

    def img_sub(m):
        attrs = m.group(1)
        src_m = re.search(r'src="([^"]*)"', attrs)
        src = (src_m.group(1) if src_m else "") or PLACEHOLDER_IMG
        if src.startswith("[") or not src:
            src = PLACEHOLDER_IMG
        cls_m = re.search(r'class="([^"]*)"', attrs)
        cls = f' class="{cls_m.group(1)}"' if cls_m else ""
        # ── image mode → CSS object-fit mapping ──
        mode_m = re.search(r'mode="([^"]*)"', attrs)
        mode = (mode_m.group(1) or "").strip() if mode_m else ""
        if mode == "aspectFill":
            fit = "cover"
        elif mode == "aspectFit":
            fit = "contain"
        elif mode == "widthFix":
            fit = "scale-down"  # width:100%; height:auto via additional style
        elif mode == "scaleToFill":
            fit = "fill"
        else:
            fit = "cover"  # default: aspectFill-like
        # Build style string — don't force width:100% on images that have explicit
        # size classes (avatar-style images, icons, etc.)
        styles = [f"object-fit:{fit}"]
        if mode == "widthFix":
            styles.append("width:100%;height:auto")
        style_str = ";".join(styles)
        # Inline onerror catches images that fail before the JS event listener attaches.
        fallback_js = json.dumps(PLACEHOLDER_IMG)
        onerror = (
            "if(!this.src.startsWith('data:'))"
            f"{{this.onerror=null;this.src={fallback_js};}}"
        )
        return (
            f'<img{cls} src="{src}"'
            f' style="display:block;{style_str}"'
            f' loading="lazy"'
            f' onerror="{_html_attr(onerror)}" />'
        )

    h = re.sub(r"<image\b([^>]*?)/?>\s*(?:</image>)?", img_sub, h)
    h = expand_for_loops(h, data)
    h = apply_wx_if(h, data)   # evaluate with data before bindings are resolved
    # ── 提取 class 三元表达式 (顶层字段) → data-wx-class-expr ──
    # 注意:循环内 item.* 字段在 __data 中无对应,重算会失败(被 try/catch 兜底),
    #       所以只对顶层字段(如 activeTab)有效
    h = re.sub(
        r'class="([^"]*\{\{[^}]+\}\}[^"]*)"',
        lambda m: _extract_class_expr(m.group(1)),
        h,
    )
    h = fill_bindings(h, data)
    # ── Targeted text rebinding: only for specific top-level elements ──
    # Uses class-based targeting, NOT text-value matching.
    # Text-value matching would incorrectly wrap loop-item text that happens
    # to match a top-level data field value (e.g. "14:00" matching selectedSlotName).
    _TEXT_REBIND_MAP = {
        'block-extra': 'selectedServiceName',
        'ab-value': 'summary',
    }
    # ── Dynamically discover additional selected*Name fields from JS data ──
    # e.g. selectedRoastName, selectedWeightName, selectedGrindName, etc.
    # Build an ordered list: each block-extra span in DOM order gets the next field.
    _discovered_names = [k for k in data if k.startswith('selected') and k.endswith('Name')]
    # Use only actually-discovered fields. Falls back to selectedServiceName if none found.
    _ordered_fields = _discovered_names if _discovered_names else ['selectedServiceName']
    # Process block-extra: assign a different field to each occurrence by position
    _be_idx = [0]  # mutable counter for block-extra positions
    def _bind_by_position(m):
        idx = _be_idx[0]
        _be_idx[0] += 1
        fn = _ordered_fields[idx] if idx < len(_ordered_fields) else _ordered_fields[-1]
        return m.group(1) + m.group(2) + '<wx-t data-wx-text="' + _html_attr(fn) + '">' + m.group(3) + '</wx-t>' + m.group(4)
    h = re.sub(
        rf'(<span\b[^>]*class="[^"]*\bblock-extra\b[^"]*"[^>]*)(/?>)([^<]+)(</span>)',
        _bind_by_position,
        h,
        flags=re.DOTALL,
    )
    # Process ab-value with its own binding
    h = re.sub(
        rf'(<span\b[^>]*class="[^"]*\bab-value\b[^"]*"[^>]*)(/?>)([^<]+)(</span>)',
        lambda m: (
            m.group(1) + m.group(2) + '<wx-t data-wx-text="summary">' + m.group(3) + '</wx-t>' + m.group(4)
        ),
        h,
        flags=re.DOTALL,
    )
    h = apply_wx_if(h)         # clean up any remaining plain-string conditions
    # Convert bindtap → onclick before stripping other event attrs,
    # so the JS runtime can route taps to the embedded page handlers.
    h = re.sub(
        r'\s+bindtap="([^"]*)"',
        lambda m2: f" onclick=\"__wx('{m2.group(1)}', this, event)\"",
        h,
    )
    # catchtap = bindtap + stopPropagation, 用于嵌套点击场景(如 profile 的 order-entry)
    h = re.sub(
        r'\s+catchtap="([^"]*)"',
        lambda m2: f" onclick=\"__wx('{m2.group(1)}', this, event, true)\"",
        h,
    )
    # bindinput → oninput, 让表单输入框可用
    h = re.sub(
        r'\s+bindinput="([^"]*)"',
        lambda m2: f" oninput=\"__wx_input('{m2.group(1)}', this, event)\"",
        h,
    )
    # bindchange → onchange (picker / switch)
    h = re.sub(
        r'\s+bindchange="([^"]*)"',
        lambda m2: f" onchange=\"__wx_change('{m2.group(1)}', this, event)\"",
        h,
    )
    # bindsubmit / bindreset (form)
    h = re.sub(
        r'\s+bindsubmit="([^"]*)"',
        lambda m2: f" onsubmit=\"__wx_form('{m2.group(1)}', this, event, true);return false;\"",
        h,
    )
    h = re.sub(
        r'\s+bindreset="([^"]*)"',
        lambda m2: f" onreset=\"__wx_form('{m2.group(1)}', this, event, false)\"",
        h,
    )
    h = re.sub(r"\s+wx:[\w-]+(?:=\"[^\"]*\")?", "", h)
    h = re.sub(r"\s+(?:bind|catch|mut-bind|capture-bind)\w+=\"[^\"]*\"", "", h)
    h = re.sub(r"\s+(?:indicator-dots|autoplay|interval|circular)=\"[^\"]*\"", "", h)
    # ── Carousel counter text binding: wrap 'N / M' text with data-wx-text=galleryLabel ──
    # This allows the JS runtime's __updateSwiperCounter() to update the counter text.
    h = re.sub(
        r'(<span\b[^>]*class="[^"]*\b(?:hero-counter-cur|gallery-counter|swiper-counter|hero-counter)\b[^"]*"[^>]*)(/?>)\s*(\d+)\s*/\s*(\d+)\s*(</span>)',
        r'\1\2<wx-t data-wx-text="galleryLabel">\3 / \4</wx-t>\5',
        h,
        flags=re.IGNORECASE,
    )
    h = re.sub(r"\{\{[^}]+\}\}", "", h)
    return h


# ── Footer extraction (extract actionbar + tabbar from body) ──────────────────

def _find_element_by_class(html: str, class_name: str, start: int = 0) -> tuple[int, int] | None:
    """Find a top-level <div class="...CLASS_NAME..."> element using depth-based
    matching (NOT fragile non-greedy regex). Returns (start, end) or None."""
    # Find opening tag with the target class
    pat = re.compile(
        rf'<div\b[^>]*\bclass="([^"]*\b{class_name}\b[^"]*)"[^>]*>',
        re.IGNORECASE | re.DOTALL
    )
    m = pat.search(html, start)
    if not m:
        return None

    tag_start = m.start()
    depth = 1
    pos = m.end()

    # Walk forward counting <div...> and </div>
    open_re = re.compile(r'<div\b', re.IGNORECASE)
    close_re = re.compile(r'</div>', re.IGNORECASE)

    while depth > 0 and pos < len(html):
        next_open = open_re.search(html, pos)
        next_close = close_re.search(html, pos)

        if next_close is None:
            return None  # unclosed

        if next_open and next_open.start() < next_close.start():
            depth += 1
            pos = next_open.end()
        else:
            depth -= 1
            if depth == 0:
                return (tag_start, next_close.end())
            pos = next_close.end()

    return None  # never found closing tag


def _extract_footer(body: str) -> tuple[str, str]:
    """Extract .actionbar and .tabbar divs from body for fixed footer placement.

    Uses depth-based matching to correctly handle nested divs.

    Returns (clean_body, footer_html).  If no footer elements found,
    footer_html is empty string.
    """
    footer_parts = []
    body_chars = list(body)  # mutable for deletion

    # Extract .actionbar first (appears above tabbar in source)
    actionbar_pos = _find_element_by_class(body, "actionbar")
    if actionbar_pos:
        footer_parts.append(body[actionbar_pos[0]:actionbar_pos[1]])

    # Extract .tabbar
    tabbar_pos = _find_element_by_class(body, "tabbar")
    if tabbar_pos:
        footer_parts.append(body[tabbar_pos[0]:tabbar_pos[1]])

    # Remove extracted elements from body (in reverse order to preserve positions)
    positions = sorted([p for p in [actionbar_pos, tabbar_pos] if p], reverse=True)
    clean_body = body
    for start, end in positions:
        clean_body = clean_body[:start] + clean_body[end:]

    footer_html = "\n".join(footer_parts)
    return clean_body.strip(), footer_html


# ── 完整手机预览 HTML ─────────────────────────────────────────────────────────

def render_phone_html(
    wxml: str, wxss: str, js: str, app_wxss: str = "",
    user_images: list | None = None,
    prompt: str = "",
) -> str:
    """Return a self-contained HTML page with phone shell wrapping the miniprogram.

    The phone shell uses flex layout:
      .screen = flex column
        .screen-scroll = flex:1, overflow-y:auto (scrollable content)
        .screen-footer = flex-shrink:0 (fixed bottom: actionbar + tabbar)

    user_images: list of (bytes, mime_type) — user-uploaded images are injected
    into the preview as base64 data URIs.
    prompt: business description used for semantic image matching.
    """
    import base64 as _b64

    data = extract_js_data(js)
    body = wxml_to_html(wxml, data)

    # ── Extract actionbar + tabbar for fixed footer placement ──
    body_scroll, footer_html = _extract_footer(body)

    # ── Build base64 data URIs from uploaded images ──
    user_img_uris: list[str] = []
    if user_images:
        for img_bytes, mime_type in user_images[:10]:
            b64 = _b64.b64encode(img_bytes).decode("ascii")
            user_img_uris.append(f"data:{mime_type};base64,{b64}")
    user_imgs_json = json.dumps(user_img_uris)

    if user_img_uris:
        for idx, uri in enumerate(user_img_uris, start=1):
            asset_pattern = rf'(["\'])(/?assets/uploads/user_upload_{idx:03d}\.[A-Za-z0-9]+)\1'
            body_scroll = re.sub(asset_pattern, lambda m, u=uri: f'{m.group(1)}{u}{m.group(1)}', body_scroll)

    # ── Inline curated local library assets for the browser preview ──
    root = Path(__file__).resolve().parent

    def _inline_local_asset(match):
        quote = match.group(1)
        rel = match.group(2).lstrip("/").replace("\\", "/")
        fpath = root / rel
        if not fpath.is_file():
            return match.group(0)
        mime_type = mimetypes.guess_type(str(fpath))[0] or "image/jpeg"
        uri = "data:" + mime_type + ";base64," + _b64.b64encode(fpath.read_bytes()).decode("ascii")
        return f"{quote}{uri}{quote}"

    body_scroll = re.sub(
        r'(["\'])(/?assets/library/[^"\']+\.(?:jpg|jpeg|png|webp|gif|bmp|svg))\1',
        _inline_local_asset,
        body_scroll,
        flags=re.IGNORECASE,
    )
    footer_html = re.sub(
        r'(["\'])(/?assets/library/[^"\']+\.(?:jpg|jpeg|png|webp|gif|bmp|svg))\1',
        _inline_local_asset,
        footer_html,
        flags=re.IGNORECASE,
    )

    # ── Semantic image assignment (replace Unsplash URLs with local assets) ──
    # Discover slots from RENDERED body (after wx:for expansion) for accurate count
    try:
        from smart_image_assigner import assign_images, discover_image_slots_from_html, apply_assignments_to_body
        slots = discover_image_slots_from_html(body_scroll)
        if slots:
            report = assign_images(prompt, slots)
            body_scroll = apply_assignments_to_body(body_scroll, report)
            footer_html = apply_assignments_to_body(footer_html, report)
    except ImportError:
        pass

    # Escape </script> in the embedded page JS to prevent early tag close
    safe_js = js.replace("</script>", r"<\/script>")

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<style>
{PHONE_SHELL_CSS}
{rpx(_adapt_wxss_for_html(app_wxss))}
{rpx(_adapt_wxss_for_html(wxss))}
</style>
</head>
<body>
<div class="phone">
  <div class="status-bar">
    <span>9:41</span>
    <div class="notch"></div>
    <span>●●●</span>
  </div>
  <div class="screen">
    <div class="screen-scroll" id="screen-scroll">
      {body_scroll}
    </div>
    <div class="screen-footer" id="screen-footer">
      {footer_html}
    </div>
  </div>
</div>
<script>
(function(){{
  // ── WeChat Runtime Shim ────────────────────────────────────────────────────
  var __data = {{}};
  var __handlers = {{}};
  var __toastEl = null;
  var __toastTimer = null;

  function __showToast(o){{
    var title = (o && o.title) ? o.title : '';
    var icon  = (o && o.icon)  ? o.icon  : 'none';
    var dur   = (o && o.duration) ? o.duration : 1500;
    if (!__toastEl) {{
      __toastEl = document.createElement('div');
      __toastEl.style.cssText = (
        'position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);' +
        'background:rgba(0,0,0,.78);color:#fff;padding:14px 22px;border-radius:10px;' +
        'font-size:14px;z-index:9999;pointer-events:none;opacity:0;transition:opacity .18s;' +
        'max-width:80%;text-align:center;white-space:pre-wrap;box-shadow:0 6px 20px rgba(0,0,0,.3);'
      );
      var screen = document.querySelector('.screen');
      if (screen) {{ screen.appendChild(__toastEl); }}
      else document.body.appendChild(__toastEl);
    }}
    var text = (icon === 'success' ? '✓ ' : icon === 'error' ? '✗ ' : icon === 'loading' ? '⏳ ' : '') + title;
    __toastEl.textContent = text;
    __toastEl.style.opacity = '1';
    if (__toastTimer) clearTimeout(__toastTimer);
    __toastTimer = setTimeout(function(){{ __toastEl.style.opacity = '0'; }}, dur);
  }}

  var wx = {{
    showToast: __showToast,
    hideToast: function(){{ if (__toastEl) __toastEl.style.opacity = '0'; }},
    showLoading: function(o){{ __showToast({{title:(o&&o.title)||'加载中...',icon:'loading',duration:99999}}); }},
    hideLoading: function(){{ if (__toastEl) __toastEl.style.opacity = '0'; }},
    showModal: function(o){{
      var title = (o && o.title) || '提示';
      var content = (o && o.content) || '';
      var showCancel = o ? (o.showCancel !== false) : true;
      var msg = title + (content ? '\\n' + content : '');
      try {{
        if (showCancel) {{
          var ok = window.confirm(msg);
          if (ok) {{ if (o && o.success) o.success({{confirm:true, cancel:false}}); }}
          else {{ if (o && o.fail) o.fail({{errMsg:'cancel'}}); if (o && o.cancel) o.cancel(); }}
        }} else {{
          window.alert(msg);
          if (o && o.success) o.success({{confirm:true, cancel:false}});
        }}
      }} catch (e) {{
        if (o && o.success) o.success({{confirm:true, cancel:false}});
      }}
    }},
    navigateTo: function(o){{ console.log('[wx]nav', o && o.url); __showToast({{title:'跳转: ' + (o && o.url), icon:'none'}}); }},
    navigateBack: function(){{}},
    switchTab: function(){{}},
    setNavigationBarTitle: function(){{}},
    request: function(o){{ if (o && o.fail) o.fail({{errMsg:'not supported in preview'}}); }},
    getSystemInfo: function(o){{ if (o && o.success) o.success({{windowWidth:375,windowHeight:640,pixelRatio:2,platform:'devtools'}}); }},
    getStorageSync: function(){{ return null; }},
    setStorageSync: function(){{}},
    removeStorageSync: function(){{}},
  }};
  function App(c){{if(c&&c.onLaunch)try{{c.onLaunch({{}});}}catch(e){{}}}}
  function getApp(){{return {{}};}}
  function getCurrentPages(){{return [__page];}}
  var module={{exports:{{}}}};

  var __page = {{
    data: __data,
    setData: function(updates, cb) {{
      // Support nested paths like 'form.bloodType' by deeply assigning
      for (var key in updates) {{
        if (updates.hasOwnProperty(key)) {{
          var val = updates[key];
          var parts = key.split('.');
          if (parts.length > 1) {{
            // Walk/create nested path: 'form.bloodType' → __data.form.bloodType = val
            var obj = __data;
            for (var i = 0; i < parts.length - 1; i++) {{
              if (!(parts[i] in obj) || typeof obj[parts[i]] !== 'object') {{
                obj[parts[i]] = {{}};
              }}
              obj = obj[parts[i]];
            }}
            obj[parts[parts.length - 1]] = val;
          }} else {{
            __data[key] = val;
          }}
        }}
      }}
      __page.data = __data;
      __updateDOM();
      __checkPageEmpty();  // show placeholder if empty, never revert
      if (cb) cb();
    }},
    triggerEvent: function() {{}},
    selectComponent: function() {{ return null; }},
  }};

  function Page(cfg) {{
    if (cfg && cfg.data) {{
      Object.assign(__data, cfg.data);
    }}
    for (var k in cfg) {{
      if (typeof cfg[k] === 'function') __handlers[k] = cfg[k];
    }}
  }}

  // ── Tab switch safety: show placeholder instead of blank page ──
  var __emptyPlaceholder = null;

  function __showEmptyPlaceholder(tabLabel) {{
    var scroll = document.getElementById('screen-scroll');
    if (!scroll) return;
    if (__emptyPlaceholder && __emptyPlaceholder.parentNode) {{
      __emptyPlaceholder.parentNode.removeChild(__emptyPlaceholder);
    }}
    var label = tabLabel || '该页面';
    __emptyPlaceholder = document.createElement('div');
    __emptyPlaceholder.className = 'pane';
    __emptyPlaceholder.style.cssText = (
      'display:flex;flex-direction:column;align-items:center;justify-content:center;' +
      'padding:50px 24px;text-align:center;flex:1;min-height:360px;box-sizing:border-box;' +
      'width:100%;'
    );
    __emptyPlaceholder.innerHTML = (
      '<div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#e8f0fe,#f0e8fe);' +
      'display:flex;align-items:center;justify-content:center;margin-bottom:22px;font-size:32px;">📋</div>' +
      '<div style="font-size:18px;font-weight:700;color:#1a1a1a;margin-bottom:8px;">' + label + '页即将接入</div>' +
      '<div style="font-size:13px;color:#888;line-height:1.7;max-width:260px;margin-bottom:24px;">' +
      '当前 demo 仅生成了预约主流程，该页面尚未配置独立内容。<br/>后续可通过多页面生成能力自动补齐。</div>' +
      '<button id="__ph-back-btn" style="background:#1a73e8;color:#fff;border:none;border-radius:22px;' +
      'padding:10px 32px;font-size:14px;font-weight:600;cursor:pointer;' +
      'box-shadow:0 4px 14px rgba(26,115,232,.3);">' +
      '← 返回预约页</button>'
    );
    scroll.appendChild(__emptyPlaceholder);
    // Attach click handler via DOM (avoids JS-in-HTML quote escaping hell)
    var backBtn = document.getElementById('__ph-back-btn');
    if (backBtn) {{
      backBtn.addEventListener('click', function() {{
        __data.activeTab = 'home';
        __page.data = __data;
        __updateDOM();
        __checkPageEmpty();
      }});
      // Remove ID to avoid duplicates on next placeholder creation
      backBtn.removeAttribute('id');
    }}
  }}

  function __hideEmptyPlaceholder() {{
    if (__emptyPlaceholder && __emptyPlaceholder.parentNode) {{
      __emptyPlaceholder.parentNode.removeChild(__emptyPlaceholder);
      __emptyPlaceholder = null;
    }}
  }}

  function __checkPageEmpty() {{
    var scroll = document.getElementById('screen-scroll');
    if (!scroll) return;
    __hideEmptyPlaceholder();
    // Check if scroll area has any visible content (exclude navbar and placeholder)
    var children = scroll.querySelectorAll('div, span, img, button, input, textarea');
    var hasVisible = false;
    for (var i = 0; i < children.length; i++) {{
      var el = children[i];
      if (el === __emptyPlaceholder) continue;
      var style = window.getComputedStyle(el);
      if (style.display !== 'none' && style.visibility !== 'hidden' && el.offsetHeight > 0) {{
        if (el.className && el.className.indexOf && el.className.indexOf('navbar') >= 0) continue;
        hasVisible = true;
        break;
      }}
    }}
    if (!hasVisible) {{
      // Find current tab label
      var tabLabel = '功能';
      if (__data.tabs) {{
        for (var j = 0; j < __data.tabs.length; j++) {{
          if (__data.tabs[j].key === __data.activeTab) {{
            tabLabel = __data.tabs[j].label;
            break;
          }}
        }}
      }}
      __showEmptyPlaceholder(tabLabel);
    }}
  }}

  function __buildEvent(type, el, valueOverride) {{
    // Build dataset with numeric coercion (WeChat dataset is always string)
    var rawDs = Object.assign({{}}, el.dataset);
    var ds = {{}};
    for (var k in rawDs) {{
      var v = rawDs[k];
      if (v === 'true') ds[k] = true;
      else if (v === 'false') ds[k] = false;
      else if (/^\\d+$/.test(v)) ds[k] = parseInt(v, 10);
      else if (/^\\d+\\.\\d+$/.test(v)) ds[k] = parseFloat(v);
      else ds[k] = v;
    }}
    return {{
      type: type,
      currentTarget: {{ id: el.id || '', dataset: ds }},
      target: {{ id: el.id || '', dataset: ds }},
      detail: type === 'input' || type === 'change' ? {{ value: valueOverride !== undefined ? valueOverride : (el.value || '') }} : {{ x:0, y:0 }},
      touches: [], changedTouches: [],
    }};
  }}

  window.__wx = function(method, el, event, doStop) {{
    var h = __handlers[method];
    if (!h) {{ console.log('[__wx] no handler:', method); return; }}
    if (doStop && event && typeof event.stopPropagation === 'function') {{
      event.stopPropagation();
    }}
    var e = __buildEvent('tap', el);
    try {{ h.call(__page, e); }}
    catch (err) {{ console.log('[__wx error]', method, err); }}
  }};

  window.__wx_input = function(method, el, event) {{
    var h = __handlers[method];
    if (!h) return;
    var e = __buildEvent('input', el);
    try {{ h.call(__page, e); }}
    catch (err) {{ console.log('[__wx_input error]', method, err); }}
  }};

  window.__wx_change = function(method, el, event) {{
    var h = __handlers[method];
    if (!h) return;
    var e = __buildEvent('change', el);
    try {{ h.call(__page, e); }}
    catch (err) {{ console.log('[__wx_change error]', method, err); }}
  }};

  window.__wx_form = function(method, el, event, isSubmit) {{
    var h = __handlers[method];
    if (!h) return;
    var detail = isSubmit ? {{ value: __collectFormData(el) }} : {{}};
    var e = {{ type: isSubmit ? 'submit' : 'reset', currentTarget: el, target: el, detail: detail }};
    try {{ h.call(__page, e); }}
    catch (err) {{ console.log('[__wx_form error]', method, err); }}
  }};

  function __collectFormData(formEl) {{
    var data = {{}};
    var inputs = formEl.querySelectorAll('input,textarea');
    inputs.forEach(function(inp) {{
      var name = inp.getAttribute('name') || inp.id || '';
      if (name) data[name] = inp.value || '';
    }});
    return data;
  }}

  function __evalExpr(expr) {{
    try {{
      return !!(new Function('data', 'with(data){{return(' + expr + ')}}'))(__data);
    }} catch (e) {{ return true; }}
  }}

  function __updateDOM() {{
    document.querySelectorAll('[data-wx-if]').forEach(function(el) {{
      var expr = el.getAttribute('data-wx-if');
      try {{ el.style.display = __evalExpr(expr) ? '' : 'none'; }} catch (e) {{}}
    }});
    document.querySelectorAll('[data-tab-section]').forEach(function(el) {{
      var section = el.getAttribute('data-tab-section');
      var varName = el.getAttribute('data-tab-var') || 'activeTab';
      el.style.display = (__data[varName] === section) ? '' : 'none';
    }});
    document.querySelectorAll('[data-tab]').forEach(function(el) {{
      var tabVal  = el.dataset.tab;
      var varName = 'activeTab';
      if (tabVal !== undefined && __data[varName] !== undefined) {{
        var isActive = (__data[varName] === tabVal);
        if (isActive) el.classList.add('tab-active');
        else el.classList.remove('tab-active');
      }}
    }});
    // ── 动态 class 表达式 (支持 item 作用域) ──
    document.querySelectorAll('[data-wx-class-expr-count]').forEach(function(el) {{
      var classes = [];
      var base = el.getAttribute('data-wx-class-base') || '';
      if (base) classes.push(base);
      // Build evaluation context: merge __data with item from data-wx-item
      var ctx = __data;
      var itemRaw = el.getAttribute('data-wx-item');
      if (itemRaw) {{
        try {{
          var itemData = JSON.parse(itemRaw);
          var indexVal = parseInt(el.getAttribute('data-wx-index') || '0', 10);
          ctx = Object.assign({{}}, __data, {{item: itemData, index: indexVal}});
          // Also inject item keys at top level for simple {{item.xxx}} access
          for (var k in itemData) {{
            if (!(k in ctx)) ctx[k] = itemData[k];
          }}
        }} catch(e) {{}}
      }}
      var count = parseInt(el.getAttribute('data-wx-class-expr-count') || '0', 10);
      for (var i = 0; i < count; i++) {{
        var expr = el.getAttribute('data-wx-class-expr-' + i);
        if (!expr) continue;
        try {{
          var v = new Function('data', 'with(data){{return(' + expr + ')}}')(ctx);
          if (v) classes.push(String(v));
        }} catch (e) {{}}
      }}
      el.className = classes.join(' ').trim();
    }});
    // ── 动态文本绑定 ──
    document.querySelectorAll('[data-wx-text]').forEach(function(el) {{
      var expr = el.getAttribute('data-wx-text');
      if (!expr) return;
      var ctx = __data;
      var itemRaw = el.closest('[data-wx-item]');
      if (itemRaw) {{
        try {{
          var itemData = JSON.parse(itemRaw.getAttribute('data-wx-item'));
          ctx = Object.assign({{}}, __data, {{item: itemData}});
          for (var k in itemData) {{ if (!(k in ctx)) ctx[k] = itemData[k]; }}
        }} catch(e) {{}}
      }}
      try {{
        var v = new Function('data', 'with(data){{return(' + expr + ')}}')(ctx);
        if (v !== undefined && v !== null) {{
          el.textContent = String(v);
        }}
      }} catch(e) {{}}
    }});
  }}

  // ── Generated Page JS ─────────────────────────────────────────────────────
  try {{
    {safe_js}
  }} catch (e) {{ console.log('[page JS error]', e); }}

  // ── User Images Injection ─────────────────────────────────────────────────
  (function() {{
    var uImgs = {user_imgs_json};
    if (!uImgs.length) return;
    var imgs = document.querySelectorAll('.screen-scroll img[src*="unsplash"],.screen-scroll img[src*="images."],.screen-scroll img[src^="/assets/uploads/"],.screen-scroll img[src^="assets/uploads/"]');
    if (!imgs.length) imgs = document.querySelectorAll('.screen-scroll img');
    imgs.forEach(function(img, i) {{ if (i < uImgs.length) img.src = uImgs[i]; }});
  }})();

  // ── Image Error Fallback ──────────────────────────────────────────────────
  var __allImgs = document.querySelectorAll('.screen-scroll img, .screen-footer img');
  __allImgs.forEach(function(img, i) {{
    var fb = "{PLACEHOLDER_IMG}";
    if (img.complete && img.naturalWidth === 0) {{
      img.src = fb;
    }} else {{
      img.addEventListener('error', function() {{
        if (!this.src.startsWith('data:')) {{
          this.onerror = null; this.src = fb;
        }}
      }});
    }}
  }});

  // ── Swiper Carousel ───────────────────────────────────────────────────────
  document.querySelectorAll('.wx-swiper').forEach(function(s) {{
    var items = Array.from(s.querySelectorAll('.wx-swiper-item'));
    if (items.length < 2) return;
    var cur = 0;
    var total = items.length;
    // Inject indicator dots if the swiper had indicator-dots attribute
    if (s.getAttribute('data-has-dots') === 'true') {{
      var dots = document.createElement('div');
      dots.className = 'wx-swiper-dots';
      dots.style.cssText = 'position:absolute;bottom:8px;left:50%;transform:translateX(-50%);display:flex;gap:6px;z-index:10;';
      for (var d = 0; d < total; d++) {{
        var dot = document.createElement('span');
        dot.style.cssText = 'width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.5);transition:background .3s;';
        if (d === 0) dot.style.background = '#fff';
        dots.appendChild(dot);
      }}
      s.style.position = 'relative';
      s.appendChild(dots);
    }}
    function __updateSwiperCounter(newIdx) {{
      // Update __data fields so text bindings re-evaluate
      if (typeof __data !== 'undefined') {{
        __data.galleryCurrent = newIdx;
        __data.heroCurrent = newIdx;
        __data.swiperCurrent = newIdx;
        __data.galleryLabel = (newIdx + 1) + '/' + total;
        // Also update hero-counter text if present
        var counterEls = s.parentElement ? s.parentElement.querySelectorAll('[data-wx-text*="gallery"], [data-wx-text*="heroCurrent"], [data-wx-text*="swiperCurrent"]') : [];
      }}
      // Re-evaluate all data-wx-text bindings in the page
      if (typeof __updateDOM === 'function') __updateDOM();
    }}
    setInterval(function() {{
      items[cur].style.display = 'none';
      cur = (cur + 1) % items.length;
      items[cur].style.display = 'block';
      // Update indicator dots
      var dotsContainer = s.querySelector('.wx-swiper-dots');
      if (dotsContainer) {{
        var dotSpans = dotsContainer.querySelectorAll('span');
        dotSpans.forEach(function(d, i) {{
          d.style.background = i === cur ? '#fff' : 'rgba(255,255,255,.5)';
        }});
      }}
      __updateSwiperCounter(cur);
    }}, 2500);
    // Also hook click-based swiper navigation (manual image taps call __wx_change)
    var oldChange = s.onchange;
    s.addEventListener('click', function(e) {{
      // Let the next tick handle any __wx_change that fires first
      setTimeout(function() {{
        // Find current visible item
        for (var i = 0; i < items.length; i++) {{
          if (items[i].style.display !== 'none') {{
            cur = i;
            __updateSwiperCounter(cur);
            break;
          }}
        }}
      }}, 100);
    }});
  }});

  // ── Init ─────────────────────────────────────────────────────────────────
  __updateDOM();
}})();
</script>
</body>
</html>"""
