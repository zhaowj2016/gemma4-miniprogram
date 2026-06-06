import os
import subprocess
import tempfile
import json

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
            # Need to disable stdout buffering for real-time capture if we wanted to, but simple check=True works
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Deployment failed:\n{e.stderr}\n{e.stdout}")
            
    if not os.path.exists(qr_code_path):
        raise Exception("QR code generation failed: Image not found.")
        
    return qr_code_path
