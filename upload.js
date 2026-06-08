const ci = require('miniprogram-ci');

async function upload() {
  try {
    const projectPath = process.argv[2];
    const appid = process.argv[3];
    const privateKeyPath = process.argv[4];
    const qrCodeDest = process.argv[5];
    const robotArg = process.argv[6] || '1';
    const robot = Number.parseInt(robotArg, 10);

    if (!projectPath || !appid || !privateKeyPath || !qrCodeDest) {
      throw new Error("Missing arguments. Usage: node upload.js <projectPath> <appid> <privateKeyPath> <qrCodeDest> [robot]");
    }
    if (!Number.isInteger(robot) || robot < 1 || robot > 30) {
      throw new Error(`Invalid robot "${robotArg}". Expected an integer from 1 to 30.`);
    }

    const project = new ci.Project({
      appid: appid,
      type: 'miniProgram',
      projectPath: projectPath,
      privateKeyPath: privateKeyPath,
      ignores: ['node_modules/**/*'],
    });

    console.log(JSON.stringify({
      event: 'wechat_preview_start',
      appid,
      projectPath,
      qrCodeDest,
      robot,
    }));
    
    await ci.preview({
      project,
      desc: 'MiniPilot Agent Preview',
      setting: {
        es6: true,
        minify: true,
      },
      robot,
      bigPackageSizeSupport: true,
      qrcodeFormat: 'image',
      qrcodeOutputDest: qrCodeDest,
      onProgressUpdate: console.log,
    });

    console.log(JSON.stringify({
      event: 'wechat_preview_success',
      qrCodeDest,
      robot,
    }));
  } catch (err) {
    const payload = {
      event: 'wechat_preview_failed',
      message: err && err.message ? err.message : String(err),
      errCode: err && (err.errCode || err.code),
      errMsg: err && err.errMsg,
      stack: err && err.stack,
    };
    console.error(JSON.stringify(payload, null, 2));
    process.exit(1);
  }
}

upload();
