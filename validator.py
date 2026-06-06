# validator.py
import re
import json

# Component Whitelist
WHITELIST_TAGS = {
    "view", "text", "image", "button", "input", "textarea", 
    "form", "scroll-view", "swiper", "swiper-item", "block"
}

# Dangerous APIs to block
DANGEROUS_APIS_REGEX = r"wx\.(login|request|requestPayment|getLocation|cloud)"

def validate_hard(files_dict: dict) -> list:
    """
    Runs hard validation checks. 
    Returns a list of error strings (empty list if validation passes).
    If any errors are returned, the code generation must fail or trigger self-healing.
    """
    errors = []
    
    # 1. Check if files dict is empty or missing necessary files
    if not files_dict:
        errors.append("代码解析失败，未生成任何有效文件。")
        return errors
        
    mandatory_files = [
        "pages/index/index.wxml",
        "pages/index/index.wxss",
        "pages/index/index.js"
    ]
    for path in mandatory_files:
        if path not in files_dict:
            errors.append(f"缺失核心页面文件：{path}")
        elif len(files_dict[path].strip()) < 10:
            errors.append(f"文件内容过短或为空：{path}")
            
    if errors:
        return errors
        
    # 2. Check JSON validity
    for path, content in files_dict.items():
        if path.endswith(".json"):
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(f"JSON 文件语法错误 ({path}): {str(e)}")
                
    # 3. Check for dangerous APIs
    for path, content in files_dict.items():
        if path.endswith(".js"):
            matches = re.findall(DANGEROUS_APIS_REGEX, content)
            if matches:
                errors.append(f"检测到违规/危险 API 调用 ({path}): wx.{', wx.'.join(matches)}")
                
    # 4. Check for path traversals (relative or absolute outside app)
    for path in files_dict.keys():
        if ".." in path or path.startswith("/") or ":" in path:
            errors.append(f"路径中包含非法的相对路径或绝对路径符号: {path}")
            
    # 5. Check for Chinese characters in filenames/paths
    for path in files_dict.keys():
        if re.search(r"[\u4e00-\u9fff]", path):
            errors.append(f"文件名或路径中包含非法中文字符: {path}")
            
    return errors

def validate_warnings(files_dict: dict) -> list:
    """
    Runs soft validation checks.
    Returns a list of warning strings. Does not block Zip generation.
    """
    warnings = []
    
    wxml_content = files_dict.get("pages/index/index.wxml", "")
    wxss_content = files_dict.get("pages/index/index.wxss", "")
    js_content = files_dict.get("pages/index/index.js", "")
    
    # 1. WXML Tag Whitelist Check
    # Find all opening tags (e.g. <view class="..."> -> view)
    tags = re.findall(r"<([a-zA-Z0-9\-]+)", wxml_content)
    invalid_tags = set()
    for tag in tags:
        # Ignore closed tags like </view> (regex doesn't match these anyway)
        if tag.lower() not in WHITELIST_TAGS:
            invalid_tags.add(tag)
    if invalid_tags:
        warnings.append(f"WXML 中使用了非白名单标签: {', '.join(invalid_tags)}（可能无法正常渲染）")
        
    # 2. WXSS Suspicious CSS Units Check
    # Match units like rem, vw, vh (excluding things like 100vw or 100vh)
    suspicious_units = re.findall(r"\b\d+(?:\.\d+)?(rem|vw|vh)\b", wxss_content, re.IGNORECASE)
    # Filter out common safe 100vw/vh values if needed, or flag all for caution
    flagged_units = set([u.lower() for u in suspicious_units])
    if flagged_units:
        warnings.append(f"WXSS 中检测到非标准的移动端单位: {', '.join(flagged_units)}（推荐使用 rpx）")
        
    # 3. WXML Event Handler Missing in JS Check
    # Find bindtap="onSubmit" or catchtap="onSubmit" or bind:tap="onSubmit"
    events = re.findall(r"(?:bind|catch):?[a-zA-Z]+=\"([a-zA-Z0-9_]+)\"", wxml_content)
    missing_handlers = []
    for event_handler in set(events):
        # Check if the handler name is defined in JS (e.g., onSubmit: or onSubmit() )
        handler_pattern = rf"\b{event_handler}\s*(?:\(|:)"
        if not re.search(handler_pattern, js_content):
            missing_handlers.append(event_handler)
    if missing_handlers:
        warnings.append(f"WXML 绑定了事件处理函数，但在 JS 中未定义: {', '.join(missing_handlers)}")
        
    # 4. WXML Variable Missing in JS data Check
    # Extract variables in {{var_name}} (basic property checks)
    variables = re.findall(r"\{\{\s*([a-zA-Z0-9_]+)", wxml_content)
    # Try to extract the data block contents from JS
    data_match = re.search(r"data\s*:\s*\{([^}]*)\}", js_content)
    js_data_keys = set()
    if data_match:
        data_block = data_match.group(1)
        # Find all keys in JS data (e.g. phone: '', or phone: [] )
        js_data_keys = set(re.findall(r"\b([a-zA-Z0-9_]+)\s*:", data_block))
        
    missing_vars = []
    for var in set(variables):
        # Exclude common loops variables or index
        if var in ["item", "index"]:
            continue
        if var not in js_data_keys:
            # Fallback search in entire JS file if data block regex parsing was not perfect
            if not re.search(rf"\b{var}\b", js_content):
                missing_vars.append(var)
    if missing_vars:
        warnings.append(f"WXML 引用了数据绑定变量，但在 JS data 中未声明: {', '.join(missing_vars)}")
        
    return warnings

if __name__ == "__main__":
    # Test validator
    test_files = {
        "pages/index/index.wxml": '<view><icon></icon><button bindtap="onTap">{{title}}</button></view>',
        "pages/index/index.wxss": 'button { width: 10rem; }',
        "pages/index/index.js": 'Page({ data: {} })',
        "pages/index/index.json": '{"navigationBarTitleText": "test"}'
    }
    print("Hard fails:", validate_hard(test_files))
    print("Warnings:", validate_warnings(test_files))
