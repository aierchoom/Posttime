from pathlib import Path
from statistics import mean,median
import json
ROOT=Path(__file__).resolve().parent
DATA=ROOT.parents[2]/'参考财报'/'生益科技（600183）'
facts=[
 ('生益科技','CCL+PCB','生益科技',3333954377.92,3286977278.33,1426490859.25,3174916620.66,2907702351.56,1378113301.50,65.80,100.11),
 ('南亚新材','CCL','南亚新材',240327620.48,461065617.47,87190150.81,218017399.69,452920222.37,81202292.54,6.49,10.42),
 ('华正新材','CCL等材料','华正新材',276713420.07,172929981.95,42669003.72,65670807.85,166530078.31,34328663.71,5.57,8.64),
 ('沪电股份','PCB','沪电股份',3822306272,2923361746,1682780947,3760567906,2794525941,1643812901,62.16,99.07)
]
rows=[]
for name,role,label,fy,h26,h25,afy,ah26,ah25,n26,n27 in facts:
 s=(DATA/f'2026-09-21_{label}_行情.txt').read_text(encoding='utf-8').splitlines()
 price=float(s[s.index('模拟')+1]);cap=float(s[s.index('总市值：')+1].removesuffix('亿'))
 profit=(fy+h26-h25)/1e8;adj=(afy+ah26-ah25)/1e8
 rows.append(dict(name=name,role=role,price=price,cap=cap,parent_ttm=profit,adjusted_ttm=adj,pe_ttm=cap/profit,adjusted_pe=cap/adj,forecast2026=n26,forecast2027=n27,pe2026=cap/n26,pe2027=cap/n27))
def group(rs):
 return dict(names=[r['name'] for r in rs],count=len(rs),mean=mean(r['pe_ttm'] for r in rs),median=median(r['pe_ttm'] for r in rs),aggregate=sum(r['cap'] for r in rs)/sum(r['parent_ttm'] for r in rs),forward2027_mean=mean(r['pe2027'] for r in rs),forward2027_aggregate=sum(r['cap'] for r in rs)/sum(r['forecast2027'] for r in rs))
primary={
 'revenue':190.2561176613,'cost':131.8621867671,'gross':58.3939308942,'parent':32.8697727833,'adj':29.0770235156,
 'cfo':29.8320542239,'capex':18.8464241391,'investing_cash':-33.2243357750,
 'fy2025_revenue':284.311385,'fy2025_parent':33.3395437792,'h125_revenue':126.7989670494,'h125_parent':14.2649085925,
 'h125_cfo':19.4421487942,'h125_capex':9.6354055128,
 'opex':(91077941.51+308657642.54+649611779.60+915089247.30)/1e8,
 'pretax':42.2115881897,'tax':5.0333357784,'minority':4.3084796280
}
out=dict(price_date='2026-09-18收盘',financial_cutoff='截至2026-06-30最近四季度',consensus_date='2026-09-20同花顺公开聚合，非终端导出',rows=rows,A_CCL_peers=group(rows[1:3]),A_CCL_with_shengyi=group(rows[:3]),PCB_reference=rows[3],foreign_reference={'台光电':{'currency':'TWD','price':4890,'ttm_pe':76.47,'source':'TWSE 20260918 BWIBBU_d'},'建滔积层板':{'currency':'HKD','price':47.1,'ttm_pe':33.77,'source':'理杏仁2026-09-18快照；不合并跨币种市值'}},financial=primary)
p=primary
out['financial_calculations']=dict(fcf=p['cfo']-p['capex'],old_cfo_plus_investing=p['cfo']+p['investing_cash'],fcf_prior=p['h125_cfo']-p['h125_capex'],gross_margin=p['gross']/p['revenue'],cfo_parent=p['cfo']/p['parent'],cfo_adj=p['cfo']/p['adj'],nonrecurring_share=(p['parent']-p['adj'])/p['parent'],tax_rate=p['tax']/p['pretax'],opex_rate=p['opex']/p['revenue'],annualize_h1_pe=rows[0]['cap']/(p['parent']*2),model26_pe=rows[0]['cap']/65.51287890196,model27_pe=rows[0]['cap']/92.94239175282695)
out['historical_comparison']=dict(old_price=126.28,new_price=143.93,price_change=143.93/126.28-1,old_ths_eps27=3.68,new_ths_eps27=4.12,ths_eps_change=4.12/3.68-1,old_ths_forward_pe=126.28/3.68,new_ths_forward_pe=143.93/4.12,caveat='同提供商但覆盖14增至19家，不能当作固定机构面板上修率；旧东方财富数据不与新同花顺直接拼接。')
assert abs(out['financial_calculations']['fcf']-10.9856300848)<1e-9
(ROOT/'同行与历史复核.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
