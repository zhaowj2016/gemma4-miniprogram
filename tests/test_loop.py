import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_builder import build_planning_prompt, build_learning_prompt, build_coding_prompt
from gemma_client import call_gemma
from parser import parse_triple
from validators import validate_project

def test():
    user_request = "做一个餐厅点餐页，包含左侧垂直分类栏，右侧菜品列表，并且要有加入购物车按钮"
    api_key = os.getenv("GEMMA_API_KEY")

    print("Building planning prompt...")
    planning_prompt = build_planning_prompt(user_request)
    print(f"Planning Prompt built, length: {len(planning_prompt)}")
    
    print("Calling Gemma for planning...")
    plan_output = call_gemma(planning_prompt, api_key=api_key)
    print("Building learning prompt...")
    learning_prompt = build_learning_prompt(user_request)
    print("Calling Gemma for learning...")
    learning_output = call_gemma(learning_prompt, api_key=api_key)
    print(f"Learning output length: {len(learning_output)}")

    print("Building synthetic history to force code generation...")
    synthetic_history = [
        {"role": "user", "text": "请阅读以下【业务骨架推演】和【范式解剖指南】，准备进行大规模代码生成。"},
        {"role": "model", "text": "收到。请提供相关文档，我将严格遵守它们。"},
        {"role": "user", "text": f"【业务骨架推演】\n{plan_output}\n\n【范式解剖指南】\n{learning_output}"},
        {"role": "model", "text": "我已经彻底消化了业务需求和底层原子类结构。我准备好手写出上千行的极高质量商业级前端代码了，绝不含任何汉字废话或 markdown 块。请下达最终指令。"}
    ]
    coding_prompt = "开始生成！严格按照 ===WXML===、===WXSS===、===JS=== 的顺序输出完整代码！必须以 ===WXML=== 开头！"
    
    print("Calling Gemma for coding...")
    raw_output = call_gemma(coding_prompt, history=synthetic_history, api_key=api_key)
    with open("raw_test.txt", "w", encoding="utf-8") as f:
        f.write(raw_output)
        
    print(f"Raw output length: {len(raw_output)}")
    print(raw_output[:200])
    
    print("Parsing output...")
    page_files = parse_triple(raw_output)
    if not page_files:
        print("FAIL: Parser returned empty")
        return
    print(f"Parsed keys: {list(page_files.keys())}")
    print(f"WXML Length: {len(page_files.get('wxml', ''))}")
    print(f"WXSS Length: {len(page_files.get('wxss', ''))}")
    print(f"JS Length: {len(page_files.get('js', ''))}")
    
    print("Validating...")
    val_files = {
        "pages/index/index.wxml": page_files.get("wxml", ""),
        "pages/index/index.wxss": page_files.get("wxss", ""),
        "pages/index/index.js": page_files.get("js", "")
    }
    val_result = validate_project(val_files, full_project=False)
    
    if val_result.ok:
        print("SUCCESS! Validation passed.")
        print(f"Warnings: {val_result.warnings}")
    else:
        print("FAIL: Validation returned errors:")
        for err in val_result.hard_errors:
            print(f"- {err}")

if __name__ == "__main__":
    test()
