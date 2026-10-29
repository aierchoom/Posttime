"""人民币亿元/亿股/元每股；事实、经营假设及估值参数分开；不以机构净利作输入。"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
SHARES=24.29119230
PRICE=143.93
OWNERSHIP=.5977
OLD_OWNERSHIP=.62499
H1={
 'CCL':(123.5699022319,36.0272848051),
 'PCB':(55.1943042883,17.2216544455),
 '环保':(4.7630657624,.9075944943),
 '地产':(2.6333118075,.2712434170),
 '其他营业':(4.0955335712,3.9661537323)
}
H1_PARENT=32.8697727833
OLD_BASE_H2={'CCL':94.10,'PCB':55.14}
# scale/price_mix为等效指数，不是同规格ASP；保留旧版H2同比范围的中部。
H2={
 'Bear':dict(scale=(1.12,1.10),price_mix=(1.18,1.14),gpm=(.27,.27),other=[(5,.18),(1,.05),(3.5,.75)],opex=.105,finance=1.4,other_income=.9,invest=.3,impair=2,tax=.15,pcb_net=.17,other_minor=.25),
 'Base':dict(scale=(1.18,1.20),price_mix=(1.27,1.17),gpm=(.2925,.30),other=[(5.3,.19),(2,.10),(4,.90)],opex=.102,finance=1,other_income=1.1,invest=.4,impair=1.2,tax=.13,pcb_net=.205,other_minor=.25),
 'Bull':dict(scale=(1.24,1.30),price_mix=(1.33,1.19),gpm=(.3125,.32),other=[(5.7,.21),(2.5,.15),(4.5,.90)],opex=.098,finance=.8,other_income=1.4,invest=.7,impair=.8,tax=.12,pcb_net=.23,other_minor=.25)
}
FY27={
 'Bear':dict(scale=(1.20,1.20),price_mix=(1.08,1.06),gpm=(.29,.30),other=[(10,.18),(1,.05),(7,.75)],opex=.102,finance=2.4,other_income=1.8,invest=.5,impair=3,tax=.15,pcb_net=.19,other_minor=.4),
 'Base':dict(scale=(1.20,1.25),price_mix=(1.12,1.08),gpm=(.315,.325),other=[(11.1,.20),(2,.10),(8.9,.80)],opex=.096,finance=1.8,other_income=2.2,invest=.8,impair=2,tax=.13,pcb_net=.22,other_minor=.4),
 'Bull':dict(scale=(1.26,1.30),price_mix=(1.16,1.12),gpm=(.33,.35),other=[(12.5,.22),(3,.15),(10,.85)],opex=.091,finance=1.5,other_income=2.6,invest=1.3,impair=1,tax=.12,pcb_net=.25,other_minor=.4)
}
PE={'Bear':(25,30),'Base':(30,35),'Bull':(35,40)}
EPS_HALF_WIDTH={'Bear':.15,'Base':.2,'Bull':.3}
OLD_EPS={'Bear':(3.1,3.4),'Base':(3.7,4.1),'Bull':(4.6,5.2)}
def calculate(baseline,a,ownership):
 seg={}
 for i,k in enumerate(['CCL','PCB']):
  rev=baseline[k]*a['scale'][i]*a['price_mix'][i];seg[k]=[rev,rev*a['gpm'][i]]
 for k,(rev,gpm) in zip(['环保','地产','其他营业'],a['other']):seg[k]=[rev,rev*gpm]
 revenue=sum(v[0] for v in seg.values());gross=sum(v[1] for v in seg.values())
 opex=revenue*a['opex']
 pretax=gross-opex-a['finance']+a['other_income']+a['invest']-a['impair']
 tax=pretax*a['tax']
 pcb_net_proxy=seg['PCB'][0]*a['pcb_net']
 minority=pcb_net_proxy*(1-ownership)+a['other_minor']
 parent=pretax-tax-minority
 return dict(segments=seg,revenue=revenue,gross=gross,opex=opex,finance=a['finance'],other_income=a['other_income'],invest=a['invest'],impair=a['impair'],pretax=pretax,tax=tax,pcb_net_proxy=pcb_net_proxy,minority=minority,parent=parent,eps=parent/SHARES,assumptions=a,ownership=ownership)
out={'units':'CNY亿元/亿股/元每股','facts':{'shares':SHARES,'price':PRICE,'price_date':'2026-09-18','H1_segments':H1,'H1_parent':H1_PARENT,'H1_cfo':29.8320542239,'H1_capex':18.8464241391,'H1_fcf_proxy':10.9856300848,'current_pcb_ownership':OWNERSHIP},'models':{}}
for case in H2:
 h2=calculate(OLD_BASE_H2,H2[case],OWNERSHIP)
 rev26={k:H1[k][0]+v[0] for k,v in h2['segments'].items()}
 fy27=calculate(rev26,FY27[case],OWNERSHIP)
 old_own=calculate(rev26,FY27[case],OLD_OWNERSHIP)
 n26=H1_PARENT+h2['parent'];eps=fy27['eps'];w=EPS_HALF_WIDTH[case]
 price_band=[(eps-w)*PE[case][0],(eps+w)*PE[case][1]]
 out['models'][case]=dict(h2_2026=h2,fy2026_revenue=sum(rev26.values()),fy2026_parent=n26,fy2026_eps=n26/SHARES,fy2027=fy27,point_pe_range=[eps*x for x in PE[case]],pe=PE[case],eps_band=[eps-w,eps+w],valuation_band=price_band,return_range=[p/PRICE-1 for p in price_band],unchanged_ownership_eps=old_own['eps'],ownership_effect_eps=fy27['eps']-old_own['eps'])
b=out['models']['Base']
out['old_new_bridge']=dict(old_eps_center=3.9,old_pe_center=32.5,old_center=3.9*32.5,model_at_old_ownership=b['unchanged_ownership_eps']*32.5,updated_center=b['fy2027']['eps']*32.5,old_band=[111,143.5],new_band=b['valuation_band'],pe_change=0,method_note='保留旧PE及EPS半宽；先分开经营模型重建与权益变化。旧版没有完整2027利润桥，经营差额不能全部归因于新事实。')
out['reverse_current_price']=[dict(pe=pe,required_eps=PRICE/pe,required_parent=PRICE*SHARES/pe) for pe in [25,30,35,40]]
out['waiting_return_test']=[dict(years=y,required_return=.10,exit_pe=pe,required_parent=PRICE*SHARES*1.10**y/pe) for y in [1,2] for pe in [30,35]]
out['sensitivity']={'CCL_gpm_plus1pct_parent':b['fy2027']['segments']['CCL'][0]*.01*(1-FY27['Base']['tax']), 'PE_plus5_value':b['fy2027']['eps']*5, 'gpm_plus1pct_note':'只改CCL毛利、其他费用与少数假设固定；不是现金回报承诺'}
assert abs(sum(v[0] for v in H1.values())-190.2561176613)<1e-8
assert all(out['models'][x]['fy2027']['parent']>0 for x in H2)
assert out['models']['Bear']['fy2027']['parent']<b['fy2027']['parent']<out['models']['Bull']['fy2027']['parent']
(ROOT/'经营估值模型.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'models':{k:{'revenue26':v['fy2026_revenue'],'profit26':v['fy2026_parent'],'profit27':v['fy2027']['parent'],'eps27':v['fy2027']['eps'],'band':v['valuation_band'],'pe_only':v['point_pe_range']} for k,v in out['models'].items()},'bridge':out['old_new_bridge'],'reverse':out['reverse_current_price'],'holding':out['waiting_return_test']},ensure_ascii=False,indent=2))
