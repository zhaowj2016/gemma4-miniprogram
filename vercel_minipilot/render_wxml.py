"""
Shared WXML → HTML rendering helpers used by app.py and showcase.py.
"""
import re
import json
import mimetypes
from pathlib import Path

PLACEHOLDER_IMG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='375' height='200'%3E%3Crect width='375' height='200' fill='%23e8eaed'/%3E%3Ctext x='188' y='107' text-anchor='middle' fill='%23aaa' font-size='13' font-family='Arial'%3EImage%3C/text%3E%3C/svg%3E"


def _adapt_wxss_for_html(css: str) -> str:
    """Adapt WeChat Mini Program CSS selectors/properties for HTML rendering."""
    css = re.sub(r'\bpage\b(\s*\{)', r':root, .screen\1', css)
    css = re.sub(r'position\s*:\s*fixed\b', 'position: sticky', css)
    css = re.sub(r'env\([^)]+\)', '0px', css)
    # vh units: phone screen is 640px, so 1vh = 6.4px
    css = re.sub(r'\b(\d+(?:\.\d+)?)vh\b', lambda m: f'{float(m.group(1)) * 6.4:.1f}px', css)
    # Rename swiper component selectors to match the HTML classes we inject
    css = re.sub(r'\bswiper-item\b', '.wx-swiper-item', css)
    css = re.sub(r'\bswiper\b', '.wx-swiper', css)
    return css

PHONE_SHELL_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{background:#e5e5ea;height:100%;display:flex;justify-content:center;padding:12px 0;}
.phone{
  width:375px;background:#1a1a1a;border-radius:50px;
  padding:12px 8px 10px;
  box-shadow:0 20px 60px rgba(0,0,0,.4),inset 0 0 0 1px rgba(255,255,255,.1);
  flex-shrink:0;
}
.status-bar{
  height:26px;display:flex;align-items:center;
  justify-content:space-between;padding:0 18px 6px;
}
.status-bar span{color:#fff;font-size:11px;font-weight:600;}
.notch{width:80px;height:14px;background:#000;border-radius:8px;margin:0 auto;}
.screen{
  width:359px;height:640px;border-radius:38px;
  overflow-y:auto;overflow-x:hidden;background:#F5F7FA;
}
.screen *{
  font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Helvetica,Arial,
              'PingFang SC','Microsoft YaHei',sans-serif;
  font-size:14px;
}
.screen button{display:flex;align-items:center;justify-content:center;width:100%;cursor:pointer;border:none;outline:none;}
.screen input{display:block;width:100%;border:1px solid #eee;border-radius:8px;padding:8px 12px;}
.screen img{max-width:100%;display:block;}
.wx-swiper{position:relative;overflow:hidden;width:100%;min-height:80px;}
.wx-swiper-item{display:none;width:100%;}
.wx-swiper-item:first-child{display:block;}
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
        ternary_m = re.match(r"(.+?)\s*\?\s*'([^']*)'\s*:\s*'([^']*)'", expr)
        if ternary_m:
            cond_expr, true_val, false_val = ternary_m.groups()
            return true_val if _eval_condition(cond_expr.strip(), data) else false_val
        # Route comparison operators through _eval_condition so loop-body
        # conditions like {{item.category === activeCategory}} evaluate correctly.
        if _CMP_RE.search(expr):
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
                    for idx, item in enumerate(section_items[:6]):
                        item_data     = {**data, item_alias: item, "item": item, "index": idx}
                        body_exp      = expand_for_loops(body, item_data)
                        filled        = fill_bindings(body_exp, item_data)
                        filled_open   = fill_bindings(clean_open, item_data)
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
        items = items[:6]  # show up to 6 items for richer preview
        parts = []
        for idx, item in enumerate(items):
            item_data     = {**data, item_alias: item, "item": item, "index": idx}
            body_expanded = expand_for_loops(body, item_data)
            filled        = fill_bindings(body_expanded, item_data)
            filled_open   = fill_bindings(clean_open, item_data)
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

def wxml_to_html(wxml: str, data: dict) -> str:
    h = wxml
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
    h = re.sub(r'<swiper\b([^>]*)>', merge_component_class("div", "wx-swiper"), h)
    h = re.sub(r'</swiper>', r'</div>', h)
    tag_map = [
        ("scroll-view", "div"),
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
        # Inline onerror catches images that fail before the JS event listener attaches.
        onerror = (
            "if(!this.src.startsWith('data:'))"
            f"{{this.onerror=null;this.src='{PLACEHOLDER_IMG}';}}"
        )
        return f'<img{cls} src="{src}" style="display:block;width:100%;object-fit:cover;" onerror="{onerror}" />'

    h = re.sub(r"<image\b([^>]*?)/?>\s*(?:</image>)?", img_sub, h)
    h = expand_for_loops(h, data)
    h = apply_wx_if(h, data)   # evaluate with data before bindings are resolved
    h = fill_bindings(h, data)
    h = apply_wx_if(h)         # clean up any remaining plain-string conditions
    # Convert bindtap → onclick before stripping other event attrs,
    # so the JS runtime can route taps to the embedded page handlers.
    h = re.sub(
        r'\s+bindtap="([^"]*)"',
        lambda m2: f" onclick=\"__wx('{m2.group(1)}', this, event)\"",
        h,
    )
    h = re.sub(r"\s+wx:[\w-]+(?:=\"[^\"]*\")?", "", h)
    h = re.sub(r"\s+(?:bind|catch|mut-bind|capture-bind)\w+=\"[^\"]*\"", "", h)
    h = re.sub(r"\s+(?:indicator-dots|autoplay|interval|circular)=\"[^\"]*\"", "", h)
    h = re.sub(r"\{\{[^}]+\}\}", "", h)
    return h


# ── 完整手机预览 HTML ─────────────────────────────────────────────────────────

def render_phone_html(
    wxml: str, wxss: str, js: str, app_wxss: str = "",
    user_images: list | None = None,
) -> str:
    """Return a self-contained HTML page with phone shell wrapping the miniprogram.

    user_images: list of (bytes, mime_type) — user-uploaded images are injected
    into the preview as base64 data URIs, replacing generated Unsplash URLs.
    """
    import base64 as _b64

    data = extract_js_data(js)
    body = wxml_to_html(wxml, data)

    # Build base64 data URIs from uploaded images
    user_img_uris: list[str] = []
    if user_images:
        for img_bytes, mime_type in user_images[:10]:
            b64 = _b64.b64encode(img_bytes).decode("ascii")
            user_img_uris.append(f"data:{mime_type};base64,{b64}")
    user_imgs_json = json.dumps(user_img_uris)

    if user_img_uris:
        for idx, uri in enumerate(user_img_uris, start=1):
            asset_pattern = rf'(["\'])(/?assets/uploads/user_upload_{idx:03d}\.[A-Za-z0-9]+)\1'
            body = re.sub(asset_pattern, lambda m, u=uri: f'{m.group(1)}{u}{m.group(1)}', body)

    # Inline curated local library assets for the browser preview. Real mini-program
    # builds still reference the project files under assets/library.
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

    body = re.sub(
        r'(["\'])(/?assets/library/[^"\']+\.(?:jpg|jpeg|png|webp|gif|bmp|svg))\1',
        _inline_local_asset,
        body,
        flags=re.IGNORECASE,
    )

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
    {body}
  </div>
</div>
<script>
(function(){{
  // ── WeChat Runtime Shim ────────────────────────────────────────────────────
  var __data = {{}};
  var __handlers = {{}};
  var wx = {{
    showToast:function(o){{console.log('[wx]showToast',o&&o.title);}},
    hideToast:function(){{}},showLoading:function(){{}},hideLoading:function(){{}},
    showModal:function(o){{if(o&&o.success)o.success({{confirm:true}});}},
    navigateTo:function(o){{console.log('[wx]nav',o&&o.url);}},
    navigateBack:function(){{}},switchTab:function(){{}},
    setNavigationBarTitle:function(){{}},
    request:function(o){{if(o&&o.fail)o.fail({{errMsg:'not supported in preview'}});}},
    getSystemInfo:function(o){{if(o&&o.success)o.success({{windowWidth:375,windowHeight:640,pixelRatio:2,platform:'devtools'}});}},
    getStorageSync:function(){{return null;}},setStorageSync:function(){{}},removeStorageSync:function(){{}},
  }};
  function App(c){{if(c&&c.onLaunch)try{{c.onLaunch({{}});}}catch(e){{}}}}
  function getApp(){{return {{}};}}
  function getCurrentPages(){{return [__page];}}
  var module={{exports:{{}}}};

  var __page = {{
    data: __data,
    setData: function(updates, cb) {{
      Object.assign(__data, updates);
      __page.data = __data;
      __updateDOM();
      if (cb) cb();
    }},
    triggerEvent: function() {{}},
    selectComponent: function() {{ return null; }},
  }};

  function Page(cfg) {{
    if (cfg && cfg.data) Object.assign(__data, cfg.data);
    for (var k in cfg) {{
      if (typeof cfg[k] === 'function') __handlers[k] = cfg[k];
    }}
  }}

  window.__wx = function(method, el, event) {{
    var h = __handlers[method];
    if (!h) {{ console.log('[__wx] no handler:', method); return; }}
    var e = {{
      type: 'tap',
      currentTarget: {{ id: el.id, dataset: Object.assign({{}}, el.dataset) }},
      target: {{ id: el.id, dataset: Object.assign({{}}, el.dataset) }},
      detail: {{ x: 0, y: 0 }}, touches: [], changedTouches: [],
    }};
    try {{ h.call(__page, e); }}
    catch (err) {{ console.log('[__wx error]', method, err); }}
  }};

  function __evalExpr(expr) {{
    try {{
      return !!(new Function('data', 'with(data){{return(' + expr + ')}}'))(__data);
    }} catch (e) {{ return true; }}
  }}

  function __updateDOM() {{
    // 1. wx:if conditional elements
    document.querySelectorAll('[data-wx-if]').forEach(function(el) {{
      var expr = el.getAttribute('data-wx-if');
      try {{ el.style.display = __evalExpr(expr) ? '' : 'none'; }} catch (e) {{}}
    }});
    // 2. Pre-rendered tab sections (dict[variable] pattern, e.g. menu[activeTab])
    document.querySelectorAll('[data-tab-section]').forEach(function(el) {{
      var section = el.getAttribute('data-tab-section');
      var varName = el.getAttribute('data-tab-var') || 'activeTab';
      el.style.display = (__data[varName] === section) ? '' : 'none';
    }});
    // 3. Tab button active classes
    document.querySelectorAll('[data-tab]').forEach(function(el) {{
      var tabVal  = el.dataset.tab;
      var varName = 'activeTab';
      if (tabVal !== undefined && __data[varName] !== undefined) {{
        var isActive = (__data[varName] === tabVal);
        if (isActive) el.classList.add('tab-active');
        else el.classList.remove('tab-active');
      }}
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
    var imgs = document.querySelectorAll('.screen img[src*="unsplash"],.screen img[src*="images."],.screen img[src^="/assets/uploads/"],.screen img[src^="assets/uploads/"]');
    if (!imgs.length) imgs = document.querySelectorAll('.screen img');
    imgs.forEach(function(img, i) {{ if (i < uImgs.length) img.src = uImgs[i]; }});
  }})();

  // ── Image Error Fallback ──────────────────────────────────────────────────
  document.querySelectorAll('.screen img').forEach(function(img, i) {{
    var fb = '{PLACEHOLDER_IMG}';
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
    setInterval(function() {{
      items[cur].style.display = 'none';
      cur = (cur + 1) % items.length;
      items[cur].style.display = 'block';
    }}, 2500);
  }});

  // ── Init ─────────────────────────────────────────────────────────────────
  __updateDOM();
}})();
</script>
</body>
</html>"""
