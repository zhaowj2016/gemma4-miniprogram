const ci = require('miniprogram-ci');
const fs = require('fs');

async function upload() {
  try {
    const projectPath = process.argv[2];
    const appid = process.argv[3];
    const privateKeyPath = process.argv[4];
    const qrCodeDest = process.argv[5];

    if (!projectPath || !appid || !privateKeyPath || !qrCodeDest) {
      throw new Error("Missing arguments. Usage: node upload.js <projectPath> <appid> <privateKeyPath> <qrCodeDest>");
    }

    const project = new ci.Project({
      appid: appid,
      type: 'miniProgram',
      projectPath: projectPath,
      privateKeyPath: privateKeyPath,
      ignores: ['node_modules/**/*'],
    });

    console.log("Compiling and uploading to WeChat servers...");
    
    // Generate preview QR code
    const previewResult = await ci.preview({
      project,
      desc: 'Auto-deployed by Gemma Match',
      setting: {
        es6: true,
        minify: true,
      },
      qrcodeFormat: 'image',
      qrcodeOutputDest: qrCodeDest,
      onProgressUpdate: console.log,
    });

    console.log("Preview generated successfully.");
  } catch (err) {
    console.error("Upload failed: ", err);
    process.exit(1);
  }
}

upload();
