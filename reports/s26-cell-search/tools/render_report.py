"""추가 Python 패키지 없이 고정 10쪽 원고를 인쇄 HTML로 변환한다."""
from pathlib import Path
import html
import re
ROOT = Path(__file__).resolve().parents[1]

def inline(s):
    s = html.escape(s)
    s = re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    return s

def render_page(text):
    out=[]; table=False; code=False
    for line in text.strip().splitlines():
        if line.startswith('```'):
            out.append('</code></pre>' if code else '<pre><code>'); code=not code; continue
        if code:
            out.append(html.escape(line)+'\n'); continue
        if line.startswith('|'):
            if re.match(r'^\|[\s:|\-]+$',line): continue
            tag='td' if table else 'th'
            if not table: out.append('<table>'); table=True
            out.append('<tr>'+''.join(f'<{tag}>'+inline(c.strip())+f'</{tag}>' for c in line.strip('|').split('|'))+'</tr>');continue
        if table: out.append('</table>');table=False
        if line.startswith('### '):out.append('<h2>'+inline(line[4:])+'</h2>')
        elif line.startswith('# '):out.append('<h1>'+inline(line[2:])+'</h1>')
        elif line:out.append('<p>'+inline(line)+'</p>')
    if table:out.append('</table>')
    return ''.join(out)

pages=(ROOT/'REPORT_ko.md').read_text(encoding='utf-8').split('<!-- PAGE -->')
assert len(pages)==10
css='''@page{size:A4;margin:0}*{box-sizing:border-box}body{margin:0;background:#e9edf2;color:#172334;font:10.5pt/1.66 "Noto Sans CJK KR","Malgun Gothic",sans-serif}.page{width:210mm;height:297mm;padding:17mm 18mm 20mm;background:white;position:relative;break-after:page;margin:8mm auto}.page:last-child{break-after:auto}.content{height:254mm}h1{font-size:19pt;line-height:1.4;letter-spacing:-.5px;color:#123f60;margin:0 0 6mm;padding-bottom:4mm;border-bottom:2px solid #267c98}h2{font-size:11.5pt;color:#123f60;margin:5mm 0 2mm}p{margin:0 0 3.4mm;word-break:keep-all;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse;margin:3mm 0 4mm;font-size:9.3pt;line-height:1.5}td,th{border:1px solid #cbd5df;padding:2.1mm;vertical-align:top}th{background:#edf4f8;text-align:left}pre{background:#f0f4f7;padding:3mm;white-space:pre-wrap;overflow-wrap:anywhere;font-size:8.2pt;line-height:1.5}code{font-family:"Noto Sans Mono CJK KR",monospace;font-size:.91em}a{color:#125f86;text-decoration:none}.footer{position:absolute;bottom:10mm;left:18mm;right:18mm;display:flex;justify-content:space-between;border-top:1px solid #d5dde5;padding-top:2mm;color:#5c6977;font-size:8.5pt}@media print{body{background:white}.page{margin:0}}'''
body=''.join(f'<section class="page"><main class="content">{render_page(p)}</main><footer class="footer"><span>ZetaMesh · S26+ 기지국 탐색 타당성 · 실물 미측정</span><span>{i} / 10</span></footer></section>' for i,p in enumerate(pages,1))
(ROOT/'REPORT_ko.html').write_text('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>S26+ 기지국 탐색 개선 타당성 보고서</title><style>'+css+'</style></head><body>'+body+'</body></html>',encoding='utf-8')
print('원고 10쪽을 인쇄 HTML로 변환했습니다.')
