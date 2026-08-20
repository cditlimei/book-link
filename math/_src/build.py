#!/usr/bin/env python3
"""把 src/ 三个文件合成一个自包含 HTML，输出 dist/math-plan.html"""
import os, datetime
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
os.makedirs(dist, exist_ok=True)
html = open(os.path.join(src, 'index.html'), encoding='utf-8').read()
bank = open(os.path.join(src, 'bank.js'), encoding='utf-8').read()
app  = open(os.path.join(src, 'app.js'),  encoding='utf-8').read()
html = html.replace('<script src="bank.js"></script>\n<script src="app.js"></script>',
                    '<script>\n%s\n%s\n</script>' % (bank, app))
assert '<script src=' not in html, '还有外链脚本没内联'
assert 'http://' not in html and 'https://' not in html, '存在外部请求，必须自包含'
out = os.path.join(dist, 'math-plan.html')
open(out, 'w', encoding='utf-8').write(html)
print('%s  %.1f KB  (built %s)' % (out, len(html.encode())/1024, datetime.date.today()))
