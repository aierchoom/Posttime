"""Reproducible calculations. USD millions unless explicitly stated otherwise."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = {
 'FY2024': dict(revenue=2442.753, gross_profit=477.375, op_income=116.043, net_income=56.299, ebitda=351.470, cfo=236.894, net_capex=152.871, fcf=84.023),
 'FY2025': dict(revenue=2906.345, gross_profit=601.686, op_income=264.684, net_income=177.448, ebitda=456.304, cfo=291.882, net_capex=273.940, fcf=17.942),
 '2025Q3': dict(revenue=752.736, gross_profit=156.736, op_income=71.906, net_income=53.055, adj_net_income=70.956, ebitda=120.915, cfo=141.803, net_capex=99.233, fcf=42.570, ad_sales=344.482, commercial_sales=408.920, elimination=-0.666, ad_profit=56.010, commercial_profit=60.031),
 '2026Q2': dict(revenue=1004.054, gross_profit=211.858, op_income=109.055, net_income=83.047, adj_net_income=106.879, ebitda=166.770, cfo=96.429, net_capex=50.416, fcf=46.013, ad_sales=382.750, commercial_sales=621.605, elimination=-0.301, ad_profit=63.861, commercial_profit=112.676),
 '2026Q3': dict(revenue=1203.855, gross_profit=291.864, op_income=162.253, net_income=84.803, adj_net_income=157.775, ebitda=242.307, cfo=154.711, net_capex=79.921, fcf=74.790, ad_sales=416.540, commercial_sales=787.882, elimination=-0.567, ad_profit=77.041, commercial_profit=166.279, pretax_income=141.701, tax=56.898, sbc=24.090),
 '2025_9M': dict(revenue=2132.025, gross_profit=435.817, op_income=183.935, net_income=126.763, adj_net_income=184.149, ebitda=330.130, cfo=228.952, net_capex=222.687, fcf=6.265, ad_sales=995.915, commercial_sales=1137.249, ad_profit=146.524, commercial_profit=163.749),
 '2026_9M': dict(revenue=3053.885, gross_profit=684.903, op_income=343.757, net_income=217.838, adj_net_income=344.736, ebitda=541.959, cfo=272.883, net_capex=237.138, fcf=35.745, ad_sales=1150.954, commercial_sales=1904.530, ad_profit=195.681, commercial_profit=360.523),
}
metrics = []
def add(name, value, formula, unit='%'):
    metrics.append(dict(metric=name, value=value, unit=unit, formula=formula))
for period, d in DATA.items():
    for key in ['gross_profit', 'op_income', 'net_income', 'ebitda', 'cfo', 'net_capex', 'fcf']:
        add(f'{period}_{key}_margin', d[key]/d['revenue']*100, f'{period}.{key}/{period}.revenue*100')
    add(f'{period}_CFO_GAAP_conversion', d['cfo']/d['net_income']*100, f'{period}.cfo/{period}.net_income*100')
    if 'adj_net_income' in d:
        add(f'{period}_CFO_adjusted_conversion', d['cfo']/d['adj_net_income']*100, f'{period}.cfo/{period}.adj_net_income*100')
    if 'ad_sales' in d:
        total_profit=d['ad_profit']+d['commercial_profit']
        for seg in ['ad','commercial']:
            add(f'{period}_{seg}_margin',d[seg+'_profit']/d[seg+'_sales']*100,f'{seg}_profit/{seg}_sales*100')
            add(f'{period}_{seg}_profit_contribution',d[seg+'_profit']/total_profit*100,f'{seg}_profit/(ad_profit+commercial_profit)*100')
            add(f'{period}_{seg}_sales_share',d[seg+'_sales']/d['revenue']*100,f'{seg}_sales/consolidated_revenue*100')
    assert abs(d['cfo']-d['net_capex']-d['fcf'])<1e-6
    if 'elimination' in d:
        assert abs(d['ad_sales']+d['commercial_sales']+d['elimination']-d['revenue'])<1e-6
for current,previous,label in [('2026Q3','2025Q3','Q3_YoY'),('2026Q3','2026Q2','Q3_QoQ'),('2026_9M','2025_9M','9M_YoY')]:
    for key in ['revenue','gross_profit','op_income','net_income','adj_net_income','ebitda','cfo','fcf','ad_sales','commercial_sales','ad_profit','commercial_profit']:
        add(label+'_'+key,(DATA[current][key]/DATA[previous][key]-1)*100,f'({current}.{key}/{previous}.{key}-1)*100')
q=DATA['2026Q3']; p=DATA['2025Q3']
add('Q3_commercial_incremental_profit_contribution',(q['commercial_profit']-p['commercial_profit'])/(q['ad_profit']+q['commercial_profit']-p['ad_profit']-p['commercial_profit'])*100,'106.248/127.279*100')
add('Q3_commercial_incremental_revenue_contribution',(q['commercial_sales']-p['commercial_sales'])/(q['revenue']-p['revenue'])*100,'378.962/451.119*100')
add('Q3_effective_GAAP_tax_rate',q['tax']/q['pretax_income']*100,'56.898/141.701*100')
add('Q3_adjustment_as_share_of_adjusted_income',(q['adj_net_income']-q['net_income'])/q['adj_net_income']*100,'72.972/157.775*100')
add('Q3_SBC_revenue',q['sbc']/q['revenue']*100,'24.090/1203.855*100')
add('9M_FCF_EBITDA',DATA['2026_9M']['fcf']/DATA['2026_9M']['ebitda']*100,'35.745/541.959*100')
add('Sep28_net_debt_book_proxy',184+1459.872-876.347,'184+1459.872-876.347','USD million')
add('Sep28_illustrative_NWC',836.362+793.552+325.432-1032.661-202.342,'AR+contract_assets+inventory-AP-contract_liabilities','USD million')
add('Dec29_illustrative_NWC',563.741+468.006+250.057-543.538-175.627,'AR+contract_assets+inventory-AP-contract_liabilities','USD million')
add('2027_guide_revenue_growth_midpoint',(6625/4480-1)*100,'(6625/4480-1)*100')
add('2027_guide_adj_EPS_growth_midpoint',(8.5/5-1)*100,'(8.5/5.0-1)*100')
add('Q3_revenue_beat_guidance_midpoint',(1203.855/1120-1)*100,'(1203.855/1120-1)*100')
add('Q3_adj_EPS_beat_guidance_midpoint',(1.46/1.25-1)*100,'(1.46/1.25-1)*100')
add('Q4_revenue_guide_sequential_growth',(1430/1203.855-1)*100,'(1430/1203.855-1)*100')
add('2027_guide_vs_Q4_run_rate',(6625/(1430*4)-1)*100,'(6625/(1430*4)-1)*100')
adjustments=[9.224,24.090,0.753,0,-0.516,4.738,6.103,9.848,18.732]
assert abs(sum(adjustments)+q['net_income']-q['adj_net_income'])<1e-6
assert abs(243.320-0.380-13.564-24.090-33.809-9.224-q['op_income'])<1e-6

# Independent scenario assumptions, not company disclosed production volumes or forecasts.
# Starting run-rate = four times Q3 2026 sales by segment, before immaterial eliminations.
assumptions={
 'Bear':dict(ad_volume=1.05,epiq_sales=140,europe_sales=20,commercial_volume=1.12,commercial_mix=1.00,ad_margin=.17,commercial_margin=.18,corporate=145,net_interest=195,other=20,tax=.25,shares=111),
 'Base':dict(ad_volume=1.12,epiq_sales=160,europe_sales=25,commercial_volume=1.35,commercial_mix=1.07,ad_margin=.20,commercial_margin=.24,corporate=145,net_interest=165,other=10,tax=.22,shares=110),
 'Bull':dict(ad_volume=1.20,epiq_sales=180,europe_sales=40,commercial_volume=1.55,commercial_mix=1.08,ad_margin=.22,commercial_margin=.26,corporate=170,net_interest=145,other=5,tax=.21,shares=111),
}
scenarios={}
for label,a in assumptions.items():
    ad=q['ad_sales']*4*a['ad_volume']+a['epiq_sales']+a['europe_sales']
    commercial=q['commercial_sales']*4*a['commercial_volume']*a['commercial_mix']
    revenue=ad+commercial
    ad_op=ad*a['ad_margin']; commercial_op=commercial*a['commercial_margin']
    adj_op=ad_op+commercial_op-a['corporate']
    adj_pretax=adj_op-a['net_interest']-a['other']
    adj_ni=adj_pretax*(1-a['tax'])
    scenarios[label]=dict(**a,ad_revenue=ad,commercial_revenue=commercial,revenue=revenue,ad_segment_profit=ad_op,commercial_segment_profit=commercial_op,adj_operating_income=adj_op,adj_net_income=adj_ni,adj_eps=adj_ni/a['shares'],revenue_growth_vs_2026guide=revenue/4480-1)
add('Base_commercial_1pp_margin_EPS_sensitivity',scenarios['Base']['commercial_revenue']*.01*.78/110,'4552.382196*.01*.78/110','USD/share')
add('Floating_debt_100bps_EPS_sensitivity',1100*.01*.78/110,'assumed floating debt 1100*.01*.78/110','USD/share')
with (ROOT/'2026-10-22_财务计算结果.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['metric','value','unit','formula']);writer.writeheader();writer.writerows(metrics)
(ROOT/'2026-10-22_计算输入与情景.json').write_text(json.dumps(dict(data=DATA,scenarios=scenarios),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(scenarios,ensure_ascii=False,indent=2))
for m in metrics:
    if m['metric'].startswith(('Q3_','9M_','Sep28','2027_','2026Q3_commercial','2026Q3_ad','2026_9M_CFO')):
        print(f"{m['metric']}: {m['value']:.4f} {m['unit']}")
print('Reconciliation checks passed: net FCF, segment revenue, GAAP operating income and adjusted net income.')
