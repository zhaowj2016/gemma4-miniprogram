# parser.py
import re

def clean_model_output(raw: str) -> str:
    """
    Strips markdown code block wrappers like ```wxml ... ``` or similar.
    """
    if not raw:
        return ""
    # Strip leading/trailing whitespaces
    cleaned = raw.strip()
    
    # Remove markdown code blocks if the entire content is wrapped
    if cleaned.startswith("```"):
        # Find the first newline
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline+1:]
        else:
            cleaned = cleaned[3:]
            
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
            
    return cleaned.strip()

def parse_triple(raw_output: str) -> dict:
    """
    Parses the raw text output from the model into WXML, WXSS, and JS code blocks.
    
    Tries to extract standard markdown code blocks:
    - wxml: ```xml, ```wxml, ```html
    - wxss: ```css, ```wxss
    - js: ```javascript, ```js
    
    If standard markdown blocks are not found, falls back to the ===SECTION=== logic.
    """
    result = {}
    
    # Try Markdown Code Blocks first
    wxml_match = re.search(r'```(?:xml|wxml|html)\n(.*?)```', raw_output, re.IGNORECASE | re.DOTALL)
    if wxml_match:
        result['wxml'] = wxml_match.group(1).strip()
        
    wxss_match = re.search(r'```(?:css|wxss)\n(.*?)```', raw_output, re.IGNORECASE | re.DOTALL)
    if wxss_match:
        result['wxss'] = wxss_match.group(1).strip()
        
    js_match = re.search(r'```(?:javascript|js)\n(.*?)```', raw_output, re.IGNORECASE | re.DOTALL)
    if js_match:
        result['js'] = js_match.group(1).strip()
        
    if 'wxml' in result and 'wxss' in result and 'js' in result:
        return result
        
    # Fallback to ===TAG===
    # Look for the strict section headers anywhere in the text
    # It handles optional markdown ticks around the headers
    pattern = r"^\s*(?:```)?===\s*(WXML|WXSS|JS|JSON)\s*===(?:```)?\s*$"
    
    matches = list(re.finditer(pattern, raw_output, re.IGNORECASE | re.MULTILINE))
    
    if not matches:
        return result if result else None

    for i, match in enumerate(matches):
        tag = match.group(1).lower()
        start_idx = match.end()
        if i + 1 < len(matches):
            end_idx = matches[i+1].start()
        else:
            end_idx = len(raw_output)
            
        block = raw_output[start_idx:end_idx].strip()
        
        # Remove any stray markdown wrappers that might be inside the parsed content
        block = clean_model_output(block)
            
        result[tag] = block

    # Check for mandatory sections: wxml, wxss, js
    mandatory = ["wxml", "wxss", "js"]
    for m in mandatory:
        if m not in result:
            print(f"[Parser] Missing mandatory section: {m.upper()}")
            return None
            
    return result

if __name__ == "__main__":
    # Test case
    test_str = """
    ===WXML===
    <view>Hello</view>
    ===WXSS===
    view { color: red; }
    ===JS===
    Page({})
    ===JSON===
    { "title": "test" }
    """
    parsed = parse_triple(test_str)
    print("Parsed result:", parsed)
