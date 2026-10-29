"""2026-10-29：2027E条件估值，披露事实/可审计残余代理/预测假设分开。
不是精确CCL分部预测。年度基数使用Q3*4后再分别调整等效规模、价格/结构、毛利和费用。
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
f=json.loads((ROOT/'三季报更新复核.json').read_text(encoding='utf-8'))
a=json.loads((ROOT/'历史预测偏差复核.json').read_text(encoding='utf-8'))
g=f['facts']['Q3'];e=a['electronic']['q3']
own=a['electronic']['ownership_at_sept_end'];shares=f['facts']['shares'];price=f['facts']['price']
res={k:g[k]-e[k] for k in ['revenue','gross']}
res['gpm']=res['gross']/res['revenue']
hist={'Q3_group':g,'Q3_PCB_consolidated':e,'Q3_remaining_including_eliminations':res}
cases={
 'Bear':{'res':dict(scale=.90,mix=.92,gpm=.30,opex=.115,finance=3,other=.5,impair=5,tax=.15),
         'pcb':dict(scale=1.05,mix=.97,gpm=.31,opex=.12,finance_rate=.02,impair_rate=.01,tax=.15),
         'own':.58,'other_minor':.5,'pe':[20,25]},
 'Base':{'res':dict(scale=1.10,mix=.95,gpm=.375,opex=.105,finance=2,other=1,impair=3,tax=.13),
         'pcb':dict(scale=1.15,mix=1,gpm=.35,opex=.11,finance_rate=.015,impair_rate=.005,tax=.12),
         'own':own,'other_minor':.3,'pe':[25,30]},
 'Bull':{'res':dict(scale=1.15,mix=1,gpm=.41,opex=.10,finance=1.5,other=1.5,impair=1.5,tax=.12),
         'pcb':dict(scale=1.25,mix=1.02,gpm=.37,opex=.105,finance_rate=.01,impair_rate=.002,tax=.12),
         'own':own,'other_minor':.3,'pe':[30,35]},
}
out={'date':'2026-10-29','units':'人民币亿元/亿股/元每股；比率为小数',
 'facts_and_proxies':hist,'shares':shares,'price':price,'price_date':'2026-10-29收盘',
 'limits':['剩余池包含CCL、其他业务与内部抵销，不是披露的CCL独立分部',
 'scale为假设的等效交付规模，mix为价格/组合指数，不是实测物理销量或同规格ASP',
 '季度乘4仅作为收入基数；利润率和各项费用重新预测，未直接年化Q3归母',
 '未取得同截点同财年全套同行预测，PE是本报告假设，不能用TTM53.67与2027PE直接算溢价',
 '目标为未来6-12个月采用2027E盈利定价的条件区间，未折现，不含分红税费，不赋概率'],
 'cases':{}}
for name,x in cases.items():
 r,p=x['res'],x['pcb']
 rr=res['revenue']*4*r['scale']*r['mix'];pr=e['revenue']*4*p['scale']*p['mix']
 rg=rr*r['gpm'];pg=pr*p['gpm']
 rpbt=rg-rr*r['opex']-r['finance']+r['other']-r['impair']
 ppbt=pg-pr*p['opex']-pr*p['finance_rate']-pr*p['impair_rate']
 rn=rpbt*(1-r['tax']);pn=ppbt*(1-p['tax'])
 minor=pn*(1-x['own'])+x['other_minor'];parent=rn+pn-minor;eps=parent/shares
 band=[eps*v for v in x['pe']]
 fy26=f['q4_cases'][name]['fy26_parent']
 out['cases'][name]=dict(assumptions=x,revenue=rr+pr,gross=rg+pg,gpm=(rg+pg)/(rr+pr),
    remaining=dict(revenue=rr,gross=rg,pretax=rpbt,net=rn),
    PCB=dict(revenue=pr,gross=pg,pretax=ppbt,net=pn,parent_contribution=pn*x['own']),
    consolidated_net=rn+pn,minority=minor,parent=parent,eps=eps,pe=x['pe'],target_band=band,
    return_range=[v/price-1 for v in band],fy26_conditional_parent=fy26,profit_growth_vs_fy26_case=parent/fy26-1)
 assert abs(parent-(rpbt*(1-r['tax'])+ppbt*(1-p['tax'])-minor))<1e-9
 assert abs(rr+pr-(out['cases'][name]['remaining']['revenue']+out['cases'][name]['PCB']['revenue']))<1e-9
b=out['cases']['Base'];rr=b['remaining']['revenue'];pn=b['PCB']['net']
out['sensitivity']=dict(remaining_gpm_minus3pct_parent=rr*.03*(1-cases['Base']['res']['tax']),
  remaining_gpm_minus3pct_price=[rr*.03*(1-cases['Base']['res']['tax'])/shares*pe for pe in b['pe']],
  pcb_ownership_minus1pct_parent=pn*.01,pe_plus5_price=b['eps']*5,
  remaining_pool_proxy_gpm_q3=res['gpm'],base_remaining_gpm_change_pp=(.375-res['gpm'])*100)
out['profit_pe_matrix']=[dict(parent=out['cases'][name]['parent'],case=name,
  prices={str(pe):out['cases'][name]['eps']*pe for pe in [20,25,30,35]}) for name in cases]
legacy_pe={'Bear':[25,30],'Base':[30,35],'Bull':[35,40]}
out['same_old_multiples_comparison']={name:dict(eps=v['eps'],pe=legacy_pe[name],
   target_band=[v['eps']*pe for pe in legacy_pe[name]],
   return_range=[v['eps']*pe/price-1 for pe in legacy_pe[name]]) for name,v in out['cases'].items()}
legacy=json.loads((ROOT/'经营估值模型.json').read_text(encoding='utf-8'))
old_eps=legacy['models']['Base']['fy2027']['eps']
out['base_central_value_bridge']=dict(old_model_eps=old_eps,new_model_eps=b['eps'],
  old_central_at_32_5=old_eps*32.5,new_profit_at_old_pe_32_5=b['eps']*32.5,
  own_central_at_27_5=b['eps']*27.5,
  profit_and_model_rebuild_effect=(b['eps']-old_eps)*32.5,pe_effect=-b['eps']*5,
  note='保持中央EPS隔离倍数，不叠加旧EPS半宽；盈利重建差额含新事实和代理方法变化，非全属新事实')
assert abs(res['revenue']+e['revenue']-g['revenue'])<1e-9
assert abs(res['gross']+e['gross']-g['gross'])<1e-9
assert out['cases']['Bear']['parent']<b['parent']<out['cases']['Bull']['parent']
assert out['cases']['Bear']['parent']<f['q4_cases']['Bear']['fy26_parent']
assert b['parent']<g['adjusted']*4
for band in [v['target_band'] for v in out['cases'].values()]:assert band[0]<band[1]
(ROOT/'三季报后目标估值模型.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'cases':out['cases'],'sensitivity':out['sensitivity']},ensure_ascii=True,indent=2))
