"""2026-09-15自选A股面板样本；PE采用归母TTM，非2027预测PE。"""
from pathlib import Path
from statistics import mean,median
import json,re
ROOT=Path(__file__).resolve().parent
DATA=ROOT.parents[2]/'参考财报'/'京东方A（000725）'/'同行PE'
# name, code, quote-name, FY2025 parent RMB, H1 2026 parent RMB, H1 2025 parent RMB.
INPUTS=[
 ('京东方A','000725','京东方',5856966754.00,5247660077.00,3246885779.00),
 ('TCL科技','000100','TCL',4516783411.00,3808272967.00,1883499452.00),
 ('彩虹股份','600707','彩虹',374238081.74,99966413.34,451631554.20),
 ('深天马A','000050','天马',167375926.83,-727846302.36,205898915.99),
 ('维信诺','002387','维信诺',-2388951993.63,-1518539640.01,-1062018369.12),
 ('龙腾光电','688055','龙腾',-208216969.19,-188014931.67,-121150606.37)
]
rows=[]
for name,code,label,fy,h126,h125 in INPUTS:
 text=(DATA/f'2026-09-15_{label}行情.txt').read_text(encoding='utf-8')
 lines=text.splitlines()
 time=next(x for x in lines if re.fullmatch(r'2026-09-15 15:\d\d:\d\d',x))
 price=float(lines[lines.index('模拟')+1])
 cap=float(lines[lines.index('总市值：')+1].removesuffix('亿'))
 provider=lines[lines.index('市盈率(TTM)：')+1]
 profit=(fy+h126-h125)/1e8
 rows.append(dict(name=name,code=code,quote_time=time,price=price,market_cap=cap,fy2025_parent=fy/1e8,h1_2026_parent=h126/1e8,h1_2025_parent=h125/1e8,ttm_parent=profit,pe_ttm=cap/profit if profit>0 else None,provider_pe=provider))
def summarize(group):
 profitable=[r for r in group if r['ttm_parent']>0]
 cap=sum(r['market_cap'] for r in profitable)
 profit=sum(r['ttm_parent'] for r in profitable)
 all_cap=sum(r['market_cap'] for r in group)
 all_profit=sum(r['ttm_parent'] for r in group)
 return dict(universe_count=len(group),profitable_count=len(profitable),excluded_losses=[r['name'] for r in group if r['pe_ttm'] is None],mean_pe=mean(r['pe_ttm'] for r in profitable),median_pe=median(r['pe_ttm'] for r in profitable),profitable_cap=cap,profitable_profit=profit,aggregate_profitable_pe=cap/profit,market_cap_weighted_arithmetic_pe=sum(r['market_cap']*r['pe_ttm'] for r in profitable)/cap,all_cap=all_cap,all_profit=all_profit,aggregate_including_losses_pe=all_cap/all_profit if all_profit>0 else None)
output=dict(price_date='2026-09-15收盘',earnings_period='TTM截至2026-06-30（最近公开四个季度）',units='价格元/股；市值和归母利润亿元人民币；PE倍',formula='TTM=FY2025+H1_2026-H1_2025; PE=market_cap/TTM; aggregate_PE=sum(cap)/sum(profit)',rows=rows,peers_excluding_boe=summarize(rows[1:]),panel_sample_including_boe=summarize(rows),caveat='自选六家上市公司样本，不是全行业；集团PE不可代替显示分部PE。上市公司亏损不以负PE或0加入个股PE均值。BOE市值为A股等价市值。')
base=json.loads((ROOT/'情景模型.json').read_text(encoding='utf-8'))
n=base['core']['Base']['fy2027']['parent'];shares=base['share_count_100million']
output['base_walkthrough']=dict(revenue=base['core']['Base']['fy2027']['revenue'],gross=base['core']['Base']['fy2027']['gross_profit'],opex=base['core']['Base']['fy2027']['opex'],pretax=base['core']['Base']['fy2027']['pretax'],parent=n,eps=n/shares,price_by_pe={str(pe):n/shares*pe for pe in [16,18,20,21,22,24]},boe_market_forward_pe_2027=rows[0]['market_cap']/n)
assert abs(rows[2]['ttm_parent']-.2257294088)<1e-9
assert output['peers_excluding_boe']['profitable_count']==2
assert output['panel_sample_including_boe']['profitable_count']==3
assert abs(output['base_walkthrough']['price_by_pe']['18']-base['core']['Base']['price_range'][0])<1e-12
(ROOT/'同行PE核算.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(output,ensure_ascii=False,indent=2))
