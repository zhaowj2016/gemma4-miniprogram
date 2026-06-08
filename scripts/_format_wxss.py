import sys, re
from pathlib import Path

def pretty(css: str) -> str:
    out = []
    buf = ''
    i = 0
    n = len(css)
    indent = '  '
    depth = 0
    def flush_decl(b):
        b = b.strip()
        if b:
            out.append(indent + b + ';')
    while i < n:
        # preserve comments verbatim
        if css[i] == '/' and i + 1 < n and css[i+1] == '*':
            end = css.find('*/', i+2)
            if end == -1: end = n - 2
            comment = css[i:end+2]
            # flush any pending buffer first
            if buf.strip():
                flush_decl(buf); buf = ''
            out.append(comment)
            i = end + 2
            # swallow following spaces/newlines
            while i < n and css[i] in ' \t':
                i += 1
            continue
        c = css[i]
        if c == '{':
            sel = ' '.join(buf.split()).strip()
            out.append(sel + ' {')
            buf = ''
            depth = 1
        elif c == ';' and depth == 1:
            flush_decl(buf); buf = ''
        elif c == '}':
            if buf.strip():
                flush_decl(buf); buf = ''
            out.append('}')
            out.append('')
            depth = 0
        else:
            buf += c
        i += 1
    # collapse 3+ blank lines
    text = '\n'.join(out)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip() + '\n'

for p in sys.argv[1:]:
    path = Path(p)
    src = path.read_text(encoding='utf-8')
    path.write_text(pretty(src), encoding='utf-8')
    print(p, '->', len(pretty(src).splitlines()), 'lines')
