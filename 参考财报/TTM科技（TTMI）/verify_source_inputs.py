"""Compare extracted raw company HTML rows with the calculation inputs."""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

P=Path(__file__).resolve().parent
D=json.loads((P/'2026-10-22_计算输入与情景.json').read_text(encoding='utf-8'))['data']
def rawrows(file):
    soup=BeautifulSoup((P/file).read_bytes(),'html.parser')
    rows=[]
    for tr in soup.find_all('tr'):
        cells=[td.get_text(' ',strip=True).replace('\xa0',' ') for td in tr.find_all(['td','th'],recursive=False)]
        cells=[c for c in cells if c]
        if not cells:
            continue
        label=re.sub(r'\s+',' ',cells[0]).strip()
        vals=[]
        for c in cells[1:]:
            c=c.replace(',','').replace('$','').strip()
            if re.fullmatch(r'\(?-?\d+(\.\d+)?\)?',c):
                vals.append(abs(float(c.strip('()')))/1000)
        if len(vals)==4:
            rows.append((label,vals))
    return rows

labels={'revenue':'Net sales','gross_profit':'Gross profit','op_income':'Operating income','net_income':'Net income','ebitda':'Adjusted EBITDA','cfo':'Operating cash flow','net_capex':'Capital expenditures, net','fcf':'Free cash flow'}
checked=0
for file,periods in [
    ('2026-10-22_TTM_Q3业绩公告.html',{'2026Q3':0,'2025Q3':1,'2026_9M':2,'2025_9M':3}),
    ('2026-08-05_TTM_Q2业绩公告_411核正.html',{'2026Q2':0}),
    ('2026-02_TTM_FY2025业绩公告.html',{'FY2025':2,'FY2024':3}),
]:
    rows=rawrows(file)
    for key,label in labels.items():
        matches=[vals for name,vals in rows if name==label]
        assert matches, (file,label)
        vals=matches[0]
        for period,idx in periods.items():
            assert abs(vals[idx]-D[period][key])<1e-6,(file,period,key,vals[idx],D[period][key])
            checked+=1
    if not file.startswith('2026-02'):
        for prefix,label in [('ad','Aerospace & Defense'),('commercial','Commercial')]:
            matches=[vals for name,vals in rows if name==label]
            assert len(matches)>=2,(file,label)
            for period,idx in periods.items():
                for key,vals in [(prefix+'_sales',matches[0]),(prefix+'_profit',matches[1])]:
                    assert abs(vals[idx]-D[period][key])<1e-6,(period,key,vals[idx],D[period][key])
                    checked+=1
print(f'PASS: {checked} raw HTML numeric inputs matched the reproducible calculation model.')
