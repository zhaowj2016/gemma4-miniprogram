# scaffold.py

APP_JSON = """{"pages":["pages/index/index"],"window":{"navigationBarTitleText":"Gemma Match","navigationBarBackgroundColor":"#ffffff","navigationBarTextStyle":"black"},"style":"v2","sitemapLocation":"sitemap.json"}"""

APP_JS = """App({})"""

APP_WXSS = """page { 
  --primary: #007AFF; 
  --primary-light: #E5F1FF;
  --bg-color: #F5F7FA;
  --surface: #FFFFFF;
  --text-main: #1A1A1A;
  --text-sub: #8E8E93;
  --border-radius-sm: 12rpx;
  --border-radius-md: 24rpx;
  --border-radius-lg: 36rpx;
  --shadow-sm: 0 4rpx 12rpx rgba(0,0,0,0.05);
  --shadow-md: 0 12rpx 32rpx rgba(0,0,0,0.08);
  --glass-bg: rgba(255, 255, 255, 0.75);
  
  background-color: var(--bg-color); 
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Segoe UI, Arial, Roboto, 'PingFang SC', 'miui', 'Hiragino Sans GB', 'Microsoft Yahei', sans-serif;
  font-size: 28rpx; 
  color: var(--text-main); 
  box-sizing: border-box;
}

/* 核心布局基类 */
.flex-row { display: flex; flex-direction: row; align-items: center; }
.flex-col { display: flex; flex-direction: column; }
.flex-center { display: flex; justify-content: center; align-items: center; }
.flex-between { display: flex; justify-content: space-between; align-items: center; }

/* 现代 UI 组件基类 */
.card {
  background: var(--surface);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-sm);
  padding: 32rpx;
  margin-bottom: 24rpx;
  transition: all 0.3s ease;
}

.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-md);
  border: 1px solid rgba(255, 255, 255, 0.4);
  padding: 40rpx;
}

.btn-primary {
  background: linear-gradient(135deg, #007AFF 0%, #0056B3 100%);
  color: #fff;
  border-radius: var(--border-radius-lg);
  padding: 24rpx 0;
  text-align: center;
  font-weight: 600;
  font-size: 32rpx;
  box-shadow: 0 8rpx 20rpx rgba(0, 122, 255, 0.3);
  transition: opacity 0.2s;
}
.btn-primary:active { opacity: 0.8; }

.text-title { font-size: 36rpx; font-weight: bold; color: var(--text-main); margin-bottom: 12rpx; }
.text-desc { font-size: 26rpx; color: var(--text-sub); line-height: 1.5; }
"""

INDEX_JSON = """{"navigationBarTitleText":"Gemma Match"}"""

PROJECT_CONFIG_JSON = """{"appid":"touristappid","projectname":"gemma-match-generated","compileType":"miniprogram","miniprogramRoot":"./","setting":{"es6":true,"postcss":true,"minified":false,"urlCheck":false}}"""

def get_scaffold_files():
    return {
        'app.json': APP_JSON,
        'app.js': APP_JS,
        'app.wxss': APP_WXSS,
        'project.config.json': PROJECT_CONFIG_JSON,
        'pages/index/index.json': INDEX_JSON
    }
