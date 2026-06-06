import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from golden_examples import get_golden_example

def inject():
    data = get_golden_example("点餐")
    wxml = data.get("wxml", "")
    wxss = data.get("wxss", "")
    js = data.get("js", "")
    
    out = f"===WXML===\n{wxml}\n===WXSS===\n{wxss}\n===JS===\n{js}"
    with open("raw.txt", "w", encoding="utf-8") as f:
        f.write(out)
        
if __name__ == "__main__":
    inject()
