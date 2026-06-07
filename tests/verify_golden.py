import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from validators import validate_project

def main():
    golden_dir = os.path.join("gemma_core", "golden_examples")
    scenarios = os.listdir(golden_dir)
    results = {}
    
    for scenario in scenarios:
        scenario_path = os.path.join(golden_dir, scenario)
        if not os.path.isdir(scenario_path):
            continue
            
        wxml_path = os.path.join(scenario_path, "index.wxml")
        wxss_path = os.path.join(scenario_path, "index.wxss")
        js_path = os.path.join(scenario_path, "index.js")
        
        val_files = {
            "pages/index/index.wxml": open(wxml_path, encoding='utf-8').read() if os.path.exists(wxml_path) else "",
            "pages/index/index.wxss": open(wxss_path, encoding='utf-8').read() if os.path.exists(wxss_path) else "",
            "pages/index/index.js": open(js_path, encoding='utf-8').read() if os.path.exists(js_path) else ""
        }
        
        res = validate_project(val_files, full_project=False)
        results[scenario] = {
            "ok": res.ok,
            "errors": res.hard_errors,
            "warnings": res.warnings
        }
        
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
