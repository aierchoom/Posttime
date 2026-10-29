"""2026-10-29：事实与合并口径情景敏感性；不虚构Q3分部、不调用旧模型覆盖输出。"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
U=1e8
def yi(**kw):return {k:v/U for k,v in kw.items()}
H1=yi(revenue=19025611766.13,cost=13186218676.71,parent=3286977278.33,adjusted=2907702351.56,cfo=2983205422.39,capex=1884642413.91,pretax=4221158818.97,tax=503333577.84,minority=430847962.80,invest=33429357.39,fairvalue=409892390.86,receivables=13224161689.87,inventory=7521866985.72)
M9=yi(revenue=33207534206.33,cost=21464749116,parent=6727389219.18,adjusted=6379483116.42,cfo=6065680636.37,capex=2995667461.63,pretax=8491891099.02,tax=1019971317.11,minority=744530562.73,invest=416986424.22,fairvalue=34996032.94,receivables=16947075609.76,inventory=9390465806.55)
PREV9=yi(revenue=20613555150.44,cost=15102168456.05,parent=2443164415.82,cfo=3175998085.60,capex=1700842464.46)
Q1=yi(revenue=8141455910.40,parent=1158139324.56,adjusted=1082821715.86)
Q2={k:H1[k]-v for k,v in Q1.items()}
Q3={k:M9[k]-H1[k] for k in H1 if k not in ['receivables','inventory']}
SHARES=24.29003670
PRICE=94.12
for d in [H1,M9,PREV9,Q3]:
    d['gross']=d['revenue']-d['cost']
    d['gpm']=d['gross']/d['revenue']
    d['fcf_proxy']=d['cfo']-d['capex']
    d['cfo_parent']=d['cfo']/d['parent']
    if 'adjusted' in d:
        d['nonrecurring']=d['parent']-d['adjusted']
        d['cfo_adjusted']=d['cfo']/d['adjusted']
        d['cfo_consolidated_net']=d['cfo']/(d['parent']+d['minority'])
FY25_PARENT=33.3395437792
TTM=FY25_PARENT+M9['parent']-PREV9['parent']
out=dict(asof='2026-10-29晚',announcement_date='2026-10-30',units='CNY亿元/亿股/元每股；比率为小数',facts=dict(H1=H1,M9=M9,prior9=PREV9,Q1=Q1,Q2=Q2,Q3=Q3,shares=SHARES,price=PRICE,price_date='2026-10-29收盘',fy25_parent=FY25_PARENT),calculations=dict(ttm_parent=TTM,market_cap=PRICE*SHARES,ttm_pe=PRICE*SHARES/TTM,q3_qoq={k:Q3[k]/Q2[k]-1 for k in Q2},price_change_from_old=PRICE/143.93-1,inventory_qoq=M9['inventory']/H1['inventory']-1,receivables_qoq=M9['receivables']/H1['receivables']-1),q4_cases={})
# 合并口径的Q4敏感性，不是分部预测，也不伪称公司指引。
# 收入基于Q3运行速度；毛利相较Q3约41.63%分别下压6.63/3.63/0.13个百分点。
cases={
 'Bear':dict(revenue_factor=.90,gpm=.35,opex=.11,finance=.9,other_income=.25,invest=0,impair=1.2,tax=.15,minority=4.0),
 'Base':dict(revenue_factor=1.00,gpm=.38,opex=.105,finance=.7,other_income=.3,invest=0,impair=.8,tax=.13,minority=3.8),
 'Bull':dict(revenue_factor=1.10,gpm=.415,opex=.10,finance=.6,other_income=.4,invest=0,impair=.6,tax=.12,minority=4.2),
}
for k,a in cases.items():
    revenue=Q3['revenue']*a['revenue_factor']
    gross=revenue*a['gpm'];expense=revenue*a['opex']
    pretax=gross-expense-a['finance']+a['other_income']+a['invest']-a['impair']
    parent=pretax*(1-a['tax'])-a['minority']
    fyparent=M9['parent']+parent
    out['q4_cases'][k]=dict(assumptions=a,revenue=revenue,gross=gross,opex=expense,pretax=pretax,tax=pretax*a['tax'],parent=parent,fy26_revenue=M9['revenue']+revenue,fy26_parent=fyparent,fy26_eps=fyparent/SHARES,fy26_pe=PRICE*SHARES/fyparent)
out['reverse_valuation']=[dict(pe=pe,required_parent=PRICE*SHARES/pe,year1_required_parent=PRICE*SHARES*1.1/pe,year2_required_parent=PRICE*SHARES*1.1**2/pe) for pe in [20,25,30,35,40]]
# 2027净利润横轴是待实现条件，不赋予Base/Bull概率，不是新目标价。
out['profit_pe_sensitivity']=[dict(parent=n,eps=n/SHARES,prices={str(pe):n/SHARES*pe for pe in [20,25,30,35,40]}) for n in [90,110,130,150]]
out['runrate_checks']=dict(fy26_q4_repeat_q3_adjusted=M9['parent']+Q3['adjusted'],annual_q3_adjusted=Q3['adjusted']*4,note='仅运行速度校验；不能当2027分部预测')
out['q4_sensitivity']=dict(gpm_plus1pct_parent=Q3['revenue']*.01*(1-cases['Base']['tax']),pe_plus5_at_110_profit=110/SHARES*5)
assert abs(Q3['parent']-34.4041194085)<1e-8
assert abs(Q3['adjusted']-34.7178076486)<1e-8
assert abs(Q3['revenue']-141.819224402)<1e-8
assert abs(M9['fcf_proxy']-30.7001317474)<1e-8
assert all(M9['parent']<x['fy26_parent'] for x in out['q4_cases'].values())
(ROOT/'三季报更新复核.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='facts'},ensure_ascii=False,indent=2))
