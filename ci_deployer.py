import os
import subprocess
import tempfile
import json

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deploy_config.json")


def load_deploy_config() -> dict | None:
    """Load saved WeChat deploy credentials from local gitignored file."""
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_deploy_config(appid: str, private_key: str):
    """Persist WeChat deploy credentials locally (gitignored, never committed)."""
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"appid": appid, "private_key": private_key}, f, ensure_ascii=False, indent=2)


def clear_deploy_config():
    """Delete saved WeChat deploy credentials."""
    if os.path.exists(_CONFIG_PATH):
        os.remove(_CONFIG_PATH)


def deploy_to_wechat(page_files: dict, appid: str, private_key_content: str) -> str:
    """
    Creates a physical temporary directory, dumps the files, and calls upload.js to generate a QR code.
    Returns the path to the generated QR code image if successful, otherwise raises an exception.
    """
    from scaffold import get_scaffold_files
    
    # 1. Create a persistent temporary directory for the QR code output
    qr_dir = tempfile.mkdtemp(prefix="gemma_qr_")
    qr_code_path = os.path.join(qr_dir, "preview.jpg")
    
    # 2. Create the project workspace
    with tempfile.TemporaryDirectory() as workspace:
        # Write scaffold files
        scaffolds = get_scaffold_files()
        
        # Override project.config.json with real AppID
        p_config = json.loads(scaffolds['project.config.json'])
        p_config['appid'] = appid
        scaffolds['project.config.json'] = json.dumps(p_config, ensure_ascii=False)
        
        for filepath, content in scaffolds.items():
            full_path = os.path.join(workspace, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
                
        # Write page files
        page_dir = os.path.join(workspace, "pages", "index")
        os.makedirs(page_dir, exist_ok=True)
        if 'wxml' in page_files:
            with open(os.path.join(page_dir, "index.wxml"), "w", encoding="utf-8") as f:
                f.write(page_files['wxml'])
        if 'wxss' in page_files:
            with open(os.path.join(page_dir, "index.wxss"), "w", encoding="utf-8") as f:
                f.write(page_files['wxss'])
        if 'js' in page_files:
            with open(os.path.join(page_dir, "index.js"), "w", encoding="utf-8") as f:
                f.write(page_files['js'])
                
        # 3. Write private key (with strict sanitization)
        cleaned_key = private_key_content.strip()
        # Fix common copy-paste errors (missing newlines after headers)
        if "-----BEGIN RSA PRIVATE KEY-----" in cleaned_key and not cleaned_key.startswith("-----BEGIN RSA PRIVATE KEY-----\n"):
            cleaned_key = cleaned_key.replace("-----BEGIN RSA PRIVATE KEY-----", "-----BEGIN RSA PRIVATE KEY-----\n")
            cleaned_key = cleaned_key.replace("-----END RSA PRIVATE KEY-----", "\n-----END RSA PRIVATE KEY-----")
            cleaned_key = "\n".join([line.strip() for line in cleaned_key.split('\n') if line.strip()])
        
        key_path = os.path.join(workspace, f"private.{appid}.key")
        with open(key_path, "w", encoding="utf-8") as f:
            f.write(cleaned_key)
            
        # 4. Invoke node upload.js
        upload_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload.js")
        
        cmd = [
            "node",
            upload_script,
            workspace,
            appid,
            key_path,
            qr_code_path
        ]
        
        # CRITICAL FIX: miniprogram-ci forks child processes. 
        # Command line args (--openssl-legacy-provider) don't inherit, but NODE_OPTIONS env var does!
        env = os.environ.copy()
        env["NODE_OPTIONS"] = "--openssl-legacy-provider"
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True, timeout=120)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            err = (e.stderr or "") + (e.stdout or "")
            hint = ""
            if "频率" in err or "rate" in err.lower() or "limit" in err.lower() or "-1" in err:
                hint = "\n\n提示：微信 CI 每日预览次数有上限（约25次/天/AppID），明天再试或更换 AppID。"
            elif "invalid" in err.lower() or "key" in err.lower() or "签名" in err:
                hint = "\n\n提示：私钥格式可能有误，请重新从微信公众平台下载 private key 文件。"
            elif "appid" in err.lower() or "未认证" in err:
                hint = "\n\n提示：AppID 未开通 CI 权限，请在微信公众平台 → 开发 → 开发管理 → 开发设置中生成密钥。"
            raise Exception(f"微信上传失败：{err[:500]}{hint}")
            
    if not os.path.exists(qr_code_path):
        raise Exception("QR code generation failed: Image not found.")
        
    return qr_code_path
