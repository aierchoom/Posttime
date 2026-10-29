"""2026-10-29 追加审计；不改写历史预测。单位人民币亿元、亿股、元/股。"""
from pathlib import Path
import json, hashlib, re
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
DATA=REPO/'参考财报/生益科技（600183）'
old=json.loads((ROOT/'经营估值模型.json').read_text(encoding='utf-8'))
new=json.loads((ROOT/'三季报更新复核.json').read_text(encoding='utf-8'))
h1=new['facts']['H1'];q3=new['facts']['Q3'];m9=new['facts']['M9']
base=old['models']['Base']['h2_2026']
# 老模型并无Q3预测。H2/2只是本次构建的等分诊断，不能称原季度预测。
half={k:base[k]/2 for k in ['revenue','gross','pretax','tax','minority','parent','opex']}
g0=half['gross']/half['revenue']
volume=(q3['revenue']-half['revenue'])*g0
margin=q3['revenue']*(q3['gpm']-g0)
net_below_gross=-(q3['gross']-q3['pretax']-(half['gross']-half['pretax']))
tax=-(q3['tax']-half['tax']);minority=-(q3['minority']-half['minority'])
bridge=dict(revenue_effect=volume,margin_effect=margin,net_expenses_and_other=net_below_gross,tax_effect=tax,minority_effect=minority)
assert abs(sum(bridge.values())-(q3['parent']-half['parent']))<1e-9
# H1比较Q3的毛利桥：收入先变化，随后毛利率；顺序归因非因果识别。
gp_growth=dict(revenue_effect=(q3['revenue']-h1['revenue']/2)*h1['gpm'],margin_effect=q3['revenue']*(q3['gpm']-h1['gpm']))
assert abs(sum(gp_growth.values())-(q3['gross']-h1['gross']/2))<1e-9
e_h1=dict(revenue=57.8353910799,cost=37.9927415320,parent=11.1070760386,cfo=9.1744411104)
e_9=dict(revenue=95.4758607150,cost=61.8391274228,parent=19.1159751048,adjusted=19.0784013672,cfo=13.6191388609,capex=20.5160474408)
e_q3={k:e_9[k]-v for k,v in e_h1.items()}
for d in [e_h1,e_9,e_q3]:d['gross']=d['revenue']-d['cost'];d['gpm']=d['gross']/d['revenue'];d['parent_margin']=d['parent']/d['revenue']
e_9['fcf']=e_9['cfo']-e_9['capex'];e_9['cfo_parent']=e_9['cfo']/e_9['parent']
ownership=(497882175+16259982)/860261067
emc_h1=dict(revenue=803.42455,gross=257.32144,parent=152.13191)
emc_9=dict(revenue=1412.26994,gross=486.82931,parent=297.13011)
emc_q3={k:emc_9[k]-v for k,v in emc_h1.items()}
for d in [emc_h1,emc_9,emc_q3]:d['gpm']=d['gross']/d['revenue']
oq={k:v['fy2026_parent']-m9['parent'] for k,v in old['models'].items()}
q2=new['facts']['Q2']
out=dict(units='除EMC为新台币亿元，其余人民币亿元；比例小数；股本亿股',asof='2026-10-29晚',
  period_limits='2026FY/2027FY尚未结束；9M超过旧FY预测是路径失效信号，不是同期间全年预测误差',
  old_base_half_h2_diagnostic=half,old_base_implied_gpm=g0,q3_vs_old_half_h2_bridge=bridge,
  bridge_gap=q3['parent']-half['parent'],q3_profit_vs_proxy=q3['parent']/half['parent']-1,
  bridge_margin_share_of_gross_gap=margin/(q3['gross']-half['gross']),
  q3_vs_h1_quarter_average_gross_bridge=gp_growth,
  old_cases_remaining_q4=oq,old_base_h2_average_vs_q2_adjusted=half['parent']/q2['adjusted']-1,
  historical_forecasts=dict(july_2026_consensus=56.31,august_2026_base=[64,69],august_2026_bull=[73,80]),
  july_m9_exceeds_old_fy=m9['parent']/56.31-1,
  august_implied_q4=dict(base=[n-m9['parent'] for n in [64,69]],bull=[n-m9['parent'] for n in [73,80]]),
  electronic=dict(h1=e_h1,m9=e_9,q3=e_q3,ownership_at_sept_end=ownership,capex_share=e_9['capex']/m9['capex'],
    cfo_share=e_9['cfo']/m9['cfo'],q3_parent_contribution_static=e_q3['parent']*ownership,
    group_less_static_contribution=q3['parent']-e_q3['parent']*ownership,
    residual_caveat='期末持股静态敏感性，非真实加权利润归属；差额包含其他业务、投资、抵销，不能当CCL利润'),
  emc=dict(currency='NTD亿元',h1=emc_h1,m9=emc_9,q3=emc_q3,expansion_budget_ntd=986),
  q1_margin_correction=dict(parent=new['facts']['Q1']['parent']/new['facts']['Q1']['revenue'],old_1636_is='合并净利润率，非归母净利率'),
  cash_correction=dict(h1_old_proxy=h1['cfo']-33.2243357767,h1_correct_fcf=h1['fcf_proxy'],
      proxy_difference=33.2243357767-h1['capex'],e9_negative_fcf=e_9['fcf']),
  scenario_stress=dict(q4_revenue_factor=.8,q4_gpm=.28,q4_opex=.115,q4_finance=1,q4_other_income=.2,q4_impair=3,q4_tax=.15,q4_minority=3.2))
s=out['scenario_stress'];s['revenue']=q3['revenue']*s['q4_revenue_factor']
s['parent']=(s['revenue']*(s['q4_gpm']-s['q4_opex'])-s['q4_finance']+s['q4_other_income']-s['q4_impair'])*(1-s['q4_tax'])-s['q4_minority']
s['fy26_parent']=m9['parent']+s['parent'];s['fy26_pe']=new['calculations']['market_cap']/s['fy26_parent']
out['price_only_returns']={k:new['facts']['price']/p-1 for k,p in [('july03_16078',160.78),('aug20_12628',126.28),('sept18_14393',143.93)]}
# 同一个固定利润锚分解价格/倍数：只用于恒等式，不混接变化样本的共识。
fixed_profit=old['models']['Base']['fy2027']['parent']
out['fixed_2027_profit_pe']=dict(profit=fixed_profit,old_pe=143.93*old['facts']['shares']/fixed_profit,new_pe=94.12*new['facts']['shares']/fixed_profit,
  caveat='固定9月模型盈利条件，并非实际市场2027PE或已实现收益；价格表现不验证2027盈利')
assert abs(e_q3['parent']-8.0088990662)<1e-9
assert abs(ownership-.5976582769221127)<.0001
assert abs(half['parent']+sum(bridge.values())-q3['parent'])<1e-9
assert e_9['fcf']<0 and m9['fcf_proxy']>0
assert out['cash_correction']['h1_old_proxy']<0<out['cash_correction']['h1_correct_fcf']
assert emc_q3['gpm']>emc_h1['gpm']
for d in [e_h1,e_9,e_q3]:assert abs(d['gross']+d['cost']-d['revenue'])<1e-9
(ROOT/'历史预测偏差复核.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
