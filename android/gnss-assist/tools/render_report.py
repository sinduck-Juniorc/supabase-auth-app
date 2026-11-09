"""의존성 없이 이 보고서의 단순 Markdown을 인쇄용 HTML로 변환한다."""
from pathlib import Path
import html,re
root=Path(__file__).resolve().parents[1]
def inline(text):
    text=html.escape(text)
    text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
    text=re.sub(r'(https://[^\s<>]+)',r'<a href="\1">\1</a>',text)
    return text
out=[];code=False;table=False
for line in (root/'REPORT_ko.md').read_text(encoding='utf-8').splitlines():
    if line.startswith('```'):
        out.append('</code></pre>' if code else '<pre><code>');code=not code;continue
    if code:out.append(html.escape(line)+'\n');continue
    if line.startswith('|'):
        if re.match(r'^\|[\s:|\-]+$',line):continue
        tag='td' if table else 'th'
        if not table:out.append('<table>');table=True
        out.append('<tr>'+''.join(f'<{tag}>'+inline(c.strip())+f'</{tag}>' for c in line.strip('|').split('|'))+'</tr>');continue
    if table:out.append('</table>');table=False
    if line.startswith('## '):out.append('<h2>'+inline(line[3:])+'</h2>')
    elif line.startswith('# '):out.append('<h1>'+inline(line[2:])+'</h1>')
    elif line:out.append('<p>'+inline(line)+'</p>')
if table:out.append('</table>')
style='''body{font:14px/1.7 "Noto Sans CJK KR","Malgun Gothic",sans-serif;color:#172033;max-width:1000px;margin:32px auto;padding:0 24px}h1{font-size:27px;color:#183b56}h2{font-size:20px;margin-top:32px;border-bottom:2px solid #dce7ee;break-after:avoid}table{border-collapse:collapse;width:100%;font-size:12px;line-height:1.55}th,td{border:1px solid #cbd5e1;padding:8px;vertical-align:top}th{background:#edf4f8}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f7;padding:12px}code{font-size:12px}a{color:#175e8c;overflow-wrap:anywhere}p{overflow-wrap:anywhere}tr{break-inside:avoid}@page{size:A4;margin:16mm}@media print{body{font-size:10.5pt;margin:0;padding:0}h1{font-size:20px}h2{font-size:15px}table{font-size:8.5pt}code{font-size:9pt}a{color:inherit}}'''
(root/'REPORT_ko.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fold3 GNSS 조사 및 적용 보고서</title><style>'+style+'</style><body>'+''.join(out)+'</body></html>',encoding='utf-8')
