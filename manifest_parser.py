import json
import re

def parse_three_blocks(text: str) -> dict:
    """
    Parses the raw JSON model output and extracts the three required code blocks.
    Expected format:
    {
      "wxml": "...",
      "wxss": "...",
      "js": "..."
    }
    
    Returns:
        dict: {'wxml': '...', 'wxss': '...', 'js': '...'} or empty dict if invalid.
    """
    try:
        # Clean up potential markdown formatting that models sometimes include
        text = text.strip()
        
        # Try to find a ```json block first
        json_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_block_match:
            text = json_block_match.group(1)
        else:
            # Fallback: find the first '{' and last '}'
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
                text = text[start_idx:end_idx+1]
                
        data = json.loads(text)
        
        result = {}
        result['wxml'] = data.get('wxml', '')
        result['wxss'] = data.get('wxss', '')
        result['js'] = data.get('js', '')
        
        # Validation: must have at least some content in wxml or js to be considered valid
        if not result['wxml'] and not result['js']:
            return {}
            
        return result
    except json.JSONDecodeError:
        print("JSONDecodeError when parsing model output:", text)
        return {}
    except Exception as e:
        print("Unexpected error when parsing model output:", e)
        return {}
