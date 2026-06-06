import re
import sys
sys.path.append('.')
import parser as p
from parser import parse_triple
from scaffold import APP_WXSS

with open('raw.txt', 'r', encoding='utf-8') as f:
    raw = f.read()

res = parse_triple(raw)
wxml = res['wxml']
wxss = APP_WXSS + "\n" + res['wxss']

# Convert rpx to px for browser rendering (1rpx = 0.5px approx for standard screen)
wxss = re.sub(r'(\d+)rpx', lambda m: str(int(m.group(1)) // 2) + 'px', wxss)

# Quick and dirty WXML to HTML conversion
html = wxml.replace('<view', '<div').replace('</view>', '</div>')
html = html.replace('<text', '<span').replace('</text>', '</span>')
html = html.replace('<image', '<img').replace('<scroll-view', '<div').replace('</scroll-view>', '</div>')
html = html.replace('<block', '<div').replace('</block>', '</div>')

full_html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Segoe UI, Arial, Roboto, 'PingFang SC', 'miui', 'Hiragino Sans GB', 'Microsoft Yahei', sans-serif; background-color: #f7f7f7; }}
{wxss}
</style>
</head>
<body>
<div style="max-width: 400px; margin: 0 auto; background: white; min-height: 100vh; position: relative;">
{html}
</div>
</body>
</html>'''

with open('preview.html', 'w', encoding='utf-8') as f:
    f.write(full_html)
print("Preview HTML generated at preview.html")
