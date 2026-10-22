import csv
import io
import json
from pathlib import Path

P=Path(__file__).resolve().parent
R=P.parents[1]/'公司档案/TTM科技（TTMI）/2026-10-22'
v=json.loads((P/'2026-10-22_估值补充_计算结果.json').read_text(encoding='utf-8'))
m=json.loads((P/'2026-10-22_计算输入与情景.json').read_text(encoding='utf-8'))
price=v['ratios']['price']
assert abs(price/8.5-v['ratios']['guide_2027_PE_mid'])<1e-10
assert abs(v['reverse_PE']['12']['required_eps']*12-price)<1e-10
for label,result in v['valuation'].items():
    assert result['eps']==m['scenarios'][label]['adj_eps']
    for multiple,target,change in zip(result['pe'],result['price_range'],result['return_pct']):
        assert abs(result['eps']*multiple-target)<1e-10
        assert abs((target/price-1)*100-change)<1e-10
for key,cash in v['cash_yield'].items():
    assert abs(cash['required_FCF']/(price*110)*100-float(key))<1e-10
old=(P/'2026-10-22_估值补充前台账快照.csv').read_bytes()
current=(R/'TTM科技（TTMI）_evidence-ledger.csv').read_bytes()
assert current.startswith(old),'Original evidence rows modified'
rows=list(csv.DictReader(io.StringIO(current.decode('utf-8'))))
assert len(rows)==289
assert {r['source_id'] for r in rows}=={f'S{i}' for i in range(1,21)}
for row in rows:
    assert Path(row['source_path_or_url']).is_file(),row['source_path_or_url']
captures='\n'.join(json.loads(p.read_text(encoding='utf-8')) for p in P.glob('2026-10-22_估值补充_*web抓取.json'))
for token in ['75.19','102.15','7.29','106.96','5.01','155.64','14.08','74.79','1.67']:
    assert token in captures,token
report=(R/'TTM科技（TTMI）.md').read_text(encoding='utf-8')
assert '### 9.1 分部经营桥' in report
assert '### 9.6 净债务和EV的口径裁决' in report
assert '新增信息 / 改动章节' in report
assert '75.19' in report
for readme in [R.parent/'README.md',R.parents[1]/'README.md']:
    text=readme.read_text(encoding='utf-8')
    assert '75.19' in text and '92.26' in text and '0.57%' in text
print('PASS: valuation arithmetic, reverse earnings, cash requirements, source tokens, README consistency, and original 251-row ledger prefix verified; total 289 rows / 20 sources.')
