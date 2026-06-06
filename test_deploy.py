import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ci_deployer import deploy_to_wechat

try:
    with open("dummy_key.key", "r") as f:
        key_content = f.read()

    page_files = {
        "wxml": "<view>Test</view>",
        "wxss": "view { color: red; }",
        "js": "Page({})"
    }

    print("Starting test deployment...")
    # This should pass the local signature phase and fail with a network/WeChat API error
    qr_path = deploy_to_wechat(page_files, "wx1234567890abcdef", key_content)
    print("Success:", qr_path)
except Exception as e:
    print("Caught Exception:")
    print(str(e))
