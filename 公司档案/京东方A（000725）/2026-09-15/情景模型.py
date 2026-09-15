"""可复算研究敏感性，单位默认人民币亿元；全部预测参数为研究假设。"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SHARES=370.44328064
PRICE=5.30
H1_REVENUE=1031.32382859
H1_PARENT=52.47660077
H1_SEGMENTS={
 '显示':(817.55437509,713.34915353),
 'IoT':(190.00029296,167.15631569),
 '传感':(4.20796061,3.44165234),
 'MLED':(64.05513503,60.10661923),
 '医工':(9.57120156,9.77450159),
 '其他抵销':(-54.06513666,-77.52921759),
}
H2={
 'Bear':{'显示':(800,.12),'IoT':(190,.115),'传感':(4.5,.18),'MLED':(60,.05),'医工':(9.5,-.03),'其他抵销':(-55,20)},
 'Base':{'显示':(870,.134),'IoT':(210,.123),'传感':(5,.22),'MLED':(70,.07),'医工':(10,0),'其他抵销':(-55,24)},
 'Bull':{'显示':(925,.155),'IoT':(220,.13),'传感':(6,.25),'MLED':(75,.08),'医工':(10.5,.01),'其他抵销':(-55,26)},
}
# 费用率含税金附加、销售、管理、研发；折旧已包含在毛利率中，不再额外加回。
# 以下依次为费用率、财务费用、其他收益、投资收益、减值、税率、少数股东损益。
H2_BRIDGE={'Bear':(.114,13,14,4,10,.25,0),'Base':(.111,10.5,16,7,8,.25,3),'Bull':(.108,9,18,10,7,.25,5)}
FY27_GROWTH={
 'Bear':{'显示':1.03*.99,'IoT':1.05,'传感':1.15,'MLED':1.10,'医工':1.03},
 'Base':{'显示':1.06*1.01,'IoT':1.075,'传感':1.30,'MLED':1.15,'医工':1.05},
 'Bull':{'显示':1.10*1.03,'IoT':1.12,'传感':1.60,'MLED':1.25,'医工':1.10},
}
FY27_GPM={
 'Bear':{'显示':.125,'IoT':.115,'传感':.20,'MLED':.065,'医工':0,'其他抵销':(-110,48)},
 'Base':{'显示':.147,'IoT':.125,'传感':.25,'MLED':.08,'医工':.01,'其他抵销':(-110,50)},
 'Bull':{'显示':.17,'IoT':.136,'传感':.28,'MLED':.09,'医工':.02,'其他抵销':(-115,54)},
}
FY27_BRIDGE={'Bear':(.112,20,32,12,18,.25,2),'Base':(.110,18,32,16,18,.25,5),'Bull':(.107,16,34,20,16,.25,10)}
PE={'Bear':(16,20),'Base':(18,22),'Bull':(20,24)}
def bridge(segments,params):
 revenue=sum(v[0] for v in segments.values())
 gross=sum(v[1] for v in segments.values())
 rate,finance,other,invest,impair,tax,minor=params
 pretax=gross-revenue*rate-finance+other+invest-impair
 parent=pretax*(1-tax)-minor
 return dict(revenue=revenue,gross_profit=gross,gross_margin=gross/revenue,opex=revenue*rate,finance=finance,other_income=other,investment=invest,impairment=impair,pretax=pretax,tax=pretax*tax,minority=minor,parent=parent,segments=segments)
models={}
for name,assumptions in H2.items():
 h2seg={k:(v[0],v[1] if k=='其他抵销' else v[0]*v[1]) for k,v in assumptions.items()}
 h2=bridge(h2seg,H2_BRIDGE[name])
 fy26rev={k:H1_SEGMENTS[k][0]+v[0] for k,v in h2seg.items()}
 fy27seg={k:(fy26rev[k]*g,fy26rev[k]*g*FY27_GPM[name][k]) for k,g in FY27_GROWTH[name].items()}
 fy27seg['其他抵销']=FY27_GPM[name]['其他抵销']
 fy27=bridge(fy27seg,FY27_BRIDGE[name])
 low,high=(fy27['parent']/SHARES*p for p in PE[name])
 models[name]=dict(h2_2026=h2,fy2026_revenue=H1_REVENUE+h2['revenue'],fy2026_parent=H1_PARENT+h2['parent'],fy2027=fy27,pe=PE[name],price_range=(low,high),return_range=(low/PRICE-1,high/PRICE-1))
def glass(capacity,util,cuts,yield_rate,asp,net_margin,pe,ownership=1):
 units=capacity*12*util*cuts*yield_rate
 revenue=units*asp/1e8
 parent=revenue*net_margin*ownership
 value=max(0,parent*pe)
 return dict(capacity=capacity,utilization=util,cuts=cuts,yield_rate=yield_rate,asp=asp,net_margin=net_margin,ownership=ownership,pe=pe,good_units=units,revenue=revenue,parent=parent,equity=value,value_per_share=value/SHARES)
glass_cases={
 '验证试制':glass(1000,.5,12,.5,1000,-.2,0),
 '试验线商业运行':glass(1000,.8,16,.75,2000,.1,30),
 '五倍产能成熟':glass(5000,.85,16,.85,3000,.15,30),
 '十倍产能成熟':glass(10000,.85,16,.85,3000,.15,30),
 '长期突破压力测试':glass(20000,.9,20,.9,3000,.2,35),
}
reverse=[]
for delta in [.1,.5,1,2]:
 equity=delta*SHARES; parent=equity/30; revenue=parent/.15
 capacity=revenue*1e8/(12*.85*16*.85*3000)
 reverse.append(dict(delta=delta,equity=equity,parent=parent,revenue=revenue,monthly_capacity=capacity,pilot_multiple=capacity/1000))
matrix={str(c):{str(a):glass(c,.85,16,.85,a,.15,30)['value_per_share'] for a in [1000,3000,6000]} for c in [1000,5000,10000]}
option_pv={str(p):max(0,p*glass_cases['十倍产能成熟']['equity']/1.12**4-10)/SHARES for p in [.2,.4,.6]}
gp=sum(r-c for r,c in H1_SEGMENTS.values())
hist={k:dict(revenue=r,gross=r-c,gpm=(r-c)/r,share=r/H1_REVENUE,gross_contribution=(r-c)/gp) for k,(r,c) in H1_SEGMENTS.items()}
out=dict(share_count_100million=SHARES,price_date='2026-09-14',price=PRICE,market_cap=SHARES*PRICE,h1_segments=hist,core=models,glass=glass_cases,reverse=reverse,asp_matrix=matrix,option_present_value=option_pv,
 assumptions_note='无公司ASP、可切割数、量产良率或正式扩产指引。主业为6-12个月前瞻估值；玻璃成熟价值不是当前目标价，概率折现另列。')
assert abs(sum(v[0] for v in H1_SEGMENTS.values())-H1_REVENUE)<1e-6
assert all(models[k]['fy2027']['parent']>0 for k in models)
assert abs(glass_cases['十倍产能成熟']['value_per_share']-2*glass_cases['五倍产能成熟']['value_per_share'])<1e-12
(ROOT/'情景模型.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
