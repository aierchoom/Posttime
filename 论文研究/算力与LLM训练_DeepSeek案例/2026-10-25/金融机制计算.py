"""Recompute descriptive financial metrics and explicitly hypothetical project scenarios.

Python standard library suffices for JSON/results; --plots additionally needs matplotlib.
This script estimates neither causal effects nor company fair values.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

def project(p, efficiency=1.0, pass_through=0.8, elasticity=0.6):
    a, rho, eps = efficiency, pass_through, elasticity
    if not (a >= 1 and 0 <= rho <= 1 and eps >= 0):
        raise ValueError('Invalid efficiency, pass-through or elasticity')
    n=p['years']
    if not (isinstance(n,int) and n>0 and p['investment']>0 and p['discount_rate']>=0):
        raise ValueError('Invalid life, investment or discount rate')
    if not (0<p['base_tasks']<=p['base_capacity']*p['max_utilization'] and 0<p['max_utilization']<=1):
        raise ValueError('Invalid base demand/capacity')
    price=p['base_price_yuan']*a**(-rho)
    demand=p['base_tasks']*a**(rho*eps)
    capacity=a*p['base_capacity']*p['max_utilization']
    tasks=min(demand,capacity)
    variable=p['compute_variable_cost_yuan']/a+p['other_variable_cost_yuan']
    revenue=price*tasks  # yuan/task * million tasks = million yuan
    ebitda=(price-variable)*tasks-p['fixed_cash_cost']
    depreciation=p['investment']/n
    cash_tax=p['tax_rate']*max(ebitda-depreciation,0)
    cash=ebitda-cash_tax
    nwc=p['working_capital_revenue_ratio']*revenue
    salvage=p['investment']*p['salvage_ratio']*(1-p['tax_rate'])
    flows=[-p['investment']-nwc]+[cash]*n
    flows[-1]+=nwc+salvage
    npv=sum(v/(1+p['discount_rate'])**t for t,v in enumerate(flows))
    return dict(efficiency=a,pass_through=rho,elasticity=eps,price=price,
        desired_tasks=demand,served_tasks=tasks,capacity_bound=demand>capacity,
        utilization=tasks/(a*p['base_capacity']),compute_ratio=tasks/a/p['base_tasks'],
        revenue=revenue,ebitda=ebitda,cash_tax=cash_tax,annual_operating_cash=cash,
        initial_working_capital=nwc,npv=npv,cash_flows=flows)

def metrics(raw):
    out=[]
    for case in raw['cases']:
        for x in case['years']:
            r=x['revenue']; c=x['cost_of_revenue']; f=x['cfo']; k=x['cash_purchase_long_assets']
            out.append(dict(company=case['company'],year=x['year'],citation=case['citation'],
                revenue_100m=r/1e8,gross_margin_pct=100*(r-c)/r,
                cfo_100m=f/1e8,cfo_margin_pct=100*f/r,
                cash_purchase_100m=k/1e8,cash_purchase_revenue_pct=100*k/r,
                cfo_less_purchase_100m=(f-k)/1e8,net_income_parent_100m=x['net_income_parent']/1e8))
    return out

def verify(p):
    base=project(p)
    for rho,eps in [(0,0),(1,3),(0.8,1.25)]:
        assert math.isclose(project(p,1,rho,eps)['npv'],base['npv'])
    a=2.; equal=project(p,a,0.8,1.25)
    assert math.isclose(equal['compute_ratio'],1.0)
    capped=project(p,a,0.8,5)
    assert capped['capacity_bound'] and math.isclose(capped['utilization'],p['max_utilization'])
    assert math.isclose(capped['compute_ratio'],p['base_capacity']*p['max_utilization']/p['base_tasks'])
    assert project(p,2,0,0)['npv']>base['npv']
    n=p['years'];r=p['discount_rate'];annuity=sum((1+r)**(-t) for t in range(1,n+1))
    check=-p['investment']-base['initial_working_capital']+base['annual_operating_cash']*annuity+base['initial_working_capital']/(1+r)**n
    assert p['salvage_ratio']==0 and math.isclose(base['npv'],check)

def plots(p):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    import numpy as np
    font_path=Path('C:/Windows/Fonts/msyh.ttc')
    if font_path.exists():plt.rcParams['font.family']=FontProperties(fname=str(font_path)).get_name()
    plt.rcParams['axes.unicode_minus']=False
    plt.rcParams['svg.fonttype']='path'
    rs=np.linspace(0,1,41); es=np.linspace(0,3,61)
    z=np.array([[project(p,2,float(r),float(e))['npv']-project(p)['npv'] for r in rs] for e in es])
    work=np.array([[project(p,2,float(r),float(e))['compute_ratio'] for r in rs] for e in es])
    fig,axs=plt.subplots(1,2,figsize=(12,5.4),layout='constrained')
    vmax=max(abs(z.min()),abs(z.max()))
    im=axs[0].pcolormesh(rs,es,z,cmap='RdBu',vmin=-vmax,vmax=vmax,shading='auto')
    axs[0].contour(rs,es,z,levels=[0],colors='black',linewidths=1.3)
    axs[0].set_title('项目净现值变化（相对未提效参照）')
    fig.colorbar(im,ax=axs[0],label='百万元人民币')
    im2=axs[1].pcolormesh(rs,es,work,cmap='viridis',shading='auto',vmin=0.5,vmax=1.8)
    axs[1].contour(rs,es,work,levels=[1],colors='white',linewidths=1.3)
    axs[1].set_title('实际计算量倍率（参照 = 1）')
    fig.colorbar(im2,ax=axs[1],label='倍率')
    for ax in axs:
        ax.set_xlabel('价格传导参数 ρ');ax.set_ylabel('任务需求价格弹性 ε')
    fig.suptitle('假设情景：效率 a = 2；有限容量；未经企业或市场数据校准',fontsize=12)
    out=HERE/'图表';out.mkdir(exist_ok=True)
    fig.savefig(out/'效率与项目价值敏感性.png',dpi=180)
    fig.savefig(out/'效率与项目价值敏感性.svg')
    plt.close(fig)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plots',action='store_true');args=parser.parse_args()
    p=json.loads((HERE/'金融机制参数.json').read_text(encoding='utf-8'))
    raw=json.loads((HERE/'金融案例数据.json').read_text(encoding='utf-8'))
    verify(p);base=project(p)
    cases=[]
    for s in p['scenarios']:
        x=project(p,**{k:s[k] for k in ['efficiency','pass_through','elasticity']})
        cases.append(dict(name=s['name'],**x,delta_npv=x['npv']-base['npv']))
    sensitivity=[]
    for n in [3,4,5]:
        for rate in [0.08,0.10,0.12]:
            pp={**p,'years':n,'discount_rate':rate}
            after=project(pp,2,0.8,0.6);before=project(pp)
            sensitivity.append(dict(years=n,discount_rate=rate,npv_before=before['npv'],npv_after=after['npv'],delta_npv=after['npv']-before['npv']))
    output=dict(status=p['status'],financial_metrics=metrics(raw),project_scenarios=cases,sensitivity=sensitivity,
        warning='财报为描述性事实；项目参数全部是假设，不是企业估值或市场预测。')
    (HERE/'金融机制结果.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for x in output['financial_metrics']:print(json.dumps(x,ensure_ascii=False))
    for x in cases:print(x['name'],f"NPV={x['npv']:.4f}; delta={x['delta_npv']:.4f}; compute={x['compute_ratio']:.4f}; utilization={x['utilization']:.4f}")
    if args.plots:plots(p)
    print('PASS arithmetic identities, capacity bounds and reproducible outputs.')

if __name__=='__main__':main()
