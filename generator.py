# generator.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re
import scaffold
import validator
import parser
import prompt_builder
import gemma_client

# Mapping keywords to golden examples
FALLBACK_MAP = {
    r"活动|报名|表单|预约": "golden_examples/activity_signup",
    r"商品|详情|购买|价格|单品": "golden_examples/product_detail",
    r"列表|瀑布流|商品列表|展示列表": "golden_examples/product_list"
}

def load_golden_example(folder_path: str) -> dict:
    """
    Loads WXML, WXSS, JS, JSON from the golden example folder
    and merges them with the fixed scaffold.
    """
    files = scaffold.get_scaffold_files()
    
    # Standard names in golden_examples
    wxml_path = os.path.join(folder_path, "wxml.txt")
    wxss_path = os.path.join(folder_path, "wxss.txt")
    js_path = os.path.join(folder_path, "js.txt")
    json_path = os.path.join(folder_path, "json.txt")
    
    try:
        if os.path.exists(wxml_path):
            with open(wxml_path, "r", encoding="utf-8") as f:
                files["pages/index/index.wxml"] = f.read()
        if os.path.exists(wxss_path):
            with open(wxss_path, "r", encoding="utf-8") as f:
                files["pages/index/index.wxss"] = f.read()
        if os.path.exists(js_path):
            with open(js_path, "r", encoding="utf-8") as f:
                files["pages/index/index.js"] = f.read()
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                files["pages/index/index.json"] = f.read()
    except Exception as e:
        print(f"[Generator] Error loading golden example {folder_path}: {e}")
        
    return files

def fallback_by_keywords(user_query: str) -> tuple:
    """
    Matches keywords in user_query and returns (files_dict, example_name).
    """
    for pattern, folder in FALLBACK_MAP.items():
        if re.search(pattern, user_query):
            print(f"[Generator] Fallback matched pattern '{pattern}' -> {folder}")
            return load_golden_example(folder), os.path.basename(folder)
            
    # Default fallback
    print("[Generator] Fallback default -> activity_signup")
    return load_golden_example("golden_examples/activity_signup"), "activity_signup"

def merge_with_scaffold(parsed_sections: dict) -> dict:
    """
    Merges parsed segments with the fixed scaffold.
    """
    files = scaffold.get_scaffold_files()
    
    files["pages/index/index.wxml"] = parsed_sections.get("wxml", "")
    files["pages/index/index.wxss"] = parsed_sections.get("wxss", "")
    files["pages/index/index.js"] = parsed_sections.get("js", "")
    
    # If JSON block is generated, merge it
    if "json" in parsed_sections and parsed_sections["json"].strip():
        files["pages/index/index.json"] = parsed_sections["json"]
        
    return files

def generate_with_repair(user_prompt: str, progress_callback=None) -> tuple:
    """
    Executes generation with up to 2 attempts (self-healing loop).
    Returns (files_dict, warnings, attempts, is_fallback, fallback_name, error_history).
    """
    max_attempts = 2
    error_history = []
    
    for attempt in range(max_attempts):
        if progress_callback:
            progress_callback(attempt + 1, max_attempts, error_history)
            
        # 1. Build prompt
        error_msg_context = "; ".join(error_history[-1]) if error_history else None
        prompt = prompt_builder.build_prompt(user_prompt, attempt, error_msg_context)
        
        # 2. Call Gemma
        try:
            raw_output = gemma_client.call_gemma(prompt)
        except Exception as e:
            raw_output = ""
            error_history.append([f"调用大模型失败或超时: {str(e)}"])
            continue
            
        # 3. Parse output
        parsed = parser.parse_triple(raw_output)
        if not parsed:
            error_history.append(["格式解析失败：未能提取出完整的三段式代码（WXML/WXSS/JS）。"])
            continue
            
        # 4. Merge and Validate
        files_dict = merge_with_scaffold(parsed)
        hard_errors = validator.validate_hard(files_dict)
        
        if not hard_errors:
            # Succeeded! Now get warnings (not blocking)
            warnings = validator.validate_warnings(files_dict)
            return files_dict, warnings, attempt + 1, False, None, error_history
        else:
            error_history.append(hard_errors)
            
    # All attempts failed -> fallback
    print("[Generator] All repair attempts failed. Running fallback...")
    files_dict, fallback_name = fallback_by_keywords(user_prompt)
    warnings = ["模型生成失败，系统已自动降级加载标准黄金样例。"]
    return files_dict, warnings, max_attempts, True, fallback_name, error_history

if __name__ == "__main__":
    # Test generator
    print("Testing generator...")
    prompt = "我需要一个红色的报名表单，可以填写姓名和手机"
    res, warn, att, fb, fb_name, history = generate_with_repair(prompt)
    print(f"Fallback used? {fb} ({fb_name})")
    print(f"Warnings: {warn}")
    print(f"Attempts: {att}")
