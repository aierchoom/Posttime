"""Recompute disclosed holdings totals and lower-bound overlaps; no return prediction."""
import csv
import json
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
with (ROOT / '基金持仓样本.csv').open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
with (ROOT / '相关ETF与主动基金布局_evidence-ledger.csv').open(encoding='utf-8-sig', newline='') as f:
    sources = list(csv.DictReader(f))
ids = {r['source_id'] for r in sources}
assert ids == {f'F{i:02}' for i in range(1, 15)}
assert len(rows) == 83
keys = [(r['fund_code'], r['holdings_date'], r['security_code']) for r in rows]
assert len(keys) == len(set(keys))
assert {r['source_id'] for r in rows} <= ids
assert all(Decimal(r['weight_pct_nav']) >= 0 for r in rows)

def basket(fund, date):
    return [r for r in rows if r['fund_code'] == fund and r['holdings_date'] == date
            and r['note'] != '前十以外补充']

def total(fund, date):
    return sum((Decimal(r['weight_pct_nav']) for r in basket(fund, date)), Decimal(0))

def overlap(fund_a, fund_b, date, by_issuer=False):
    key = 'security_name' if by_issuer else 'security_code'
    maps = []
    for fund in (fund_a, fund_b):
        values = {}
        for r in basket(fund, date):
            values[r[key]] = values.get(r[key], Decimal(0)) + Decimal(r['weight_pct_nav'])
        maps.append(values)
    return sum((min(w, maps[1].get(k, Decimal(0))) for k, w in maps[0].items()), Decimal(0))

expected = [('159819','2026-06-30','64.95'), ('516510','2026-06-30','50.77'),
            ('588200','2026-06-30','60.06'), ('SMH','2026-10-23','69.02'),
            ('SOXX','2026-10-23','62.51'), ('017102/017103','2026-09-30','60.54'),
            ('018993/018994','2026-09-30','55.70')]
for fund, date, value in expected:
    assert total(fund,date) == Decimal(value), (fund,total(fund,date))
assert overlap('159819','516510','2026-06-30') == Decimal('14.79')
assert overlap('017102/017103','018993/018994','2026-09-30') == Decimal('26.64')
assert overlap('017102/017103','018993/018994','2026-09-30',True) == Decimal('27.81')

text = (ROOT / '相关ETF与主动基金布局.md').read_text(encoding='utf-8')
assert set(re.findall(r'(?<![A-Za-z])F\d{2}(?!\d)', text)) == ids
assert '<!-- FUND_SOURCES -->' not in text
for target in re.findall(r'\]\(([^)]+)\)', text):
    if not target.startswith(('http:', 'https:', '#', '参考财报/')):
        assert (ROOT / target).exists(), target
print(json.dumps({'status':'PASS','holding_rows':len(rows),'sources':len(ids),
                  'totals':expected,'overlap_lower_bounds_pct':[14.79,26.64,27.81]},
                 ensure_ascii=False,indent=2))
