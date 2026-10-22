"""2026-10-22 valuation supplement; no changes to the original operating model."""
import json
from pathlib import Path

P=Path(__file__).resolve().parent
model=json.loads((P/'2026-10-22_计算输入与情景.json').read_text(encoding='utf-8'))
PRICE=75.19
QUOTE='2026-10-22 10:54 EDT / 22:54 Asia/Shanghai; intraday, not close'
Q3_DILUTED=107.699
VALUATION_SHARES=110.0
COMMON_SHARES=105.348864 # Q2 10-Q cover: July 31 2026, not current reported share count
NET_DEBT_PROXY=767.525+1100 # Sept28 net book debt + Sept30 incremental loans, approximate
LTM_GAAP_NI=177.448-126.763+217.838
LTM_ADJ_NI=258.970-184.149+344.736
LTM_FCF=17.942-6.265+35.745
LTM_EBITDA=456.304-330.130+541.959
base=model['scenarios']['Base']
ratios={
 'price':PRICE,'quote_time':QUOTE,'previous_close':102.15,
 'change_vs_previous_close_pct':(PRICE/102.15-1)*100,
 'guide_2026_PE_low_high':[PRICE/5.03,PRICE/4.97],
 'guide_2027_PE_low_high':[PRICE/8.90,PRICE/8.10],
 'guide_2027_PE_mid':PRICE/8.5,
 'own_base_2027_PE':PRICE/base['adj_eps'],
 'pre_Q3_public_consensus_2027_PE':PRICE/7.29,
 'public_consensus_update_date':'2026-10-20, pre-Q3; not a terminal export',
 'LTM_GAAP_NI':LTM_GAAP_NI,'LTM_adjusted_NI':LTM_ADJ_NI,
 'LTM_GAAP_PE_diluted_proxy':PRICE*Q3_DILUTED/LTM_GAAP_NI,
 'LTM_adjusted_PE_diluted_proxy':PRICE*Q3_DILUTED/LTM_ADJ_NI,
 'LTM_FCF':LTM_FCF,'LTM_EBITDA':LTM_EBITDA,
 'diluted_equity_proxy':PRICE*VALUATION_SHARES,
 'common_equity_proxy_using_July_share_count':PRICE*COMMON_SHARES,
 'post_Epiq_net_debt_proxy':NET_DEBT_PROXY,
 'diluted_EV_proxy':PRICE*VALUATION_SHARES+NET_DEBT_PROXY,
 'reported_FCF_yield_diluted_proxy_pct':LTM_FCF/(PRICE*VALUATION_SHARES)*100,
 'LTM_EV_EBITDA_scope_mismatch':(PRICE*VALUATION_SHARES+NET_DEBT_PROXY)/LTM_EBITDA,
}
peers={
 'WUS':dict(price=106.96,currency='CNY',quote='2026-10-22 15:04 CST, delayed',eps_2027=5.01,period_end='2027-12-31',pe=106.96/5.01),
 'SANM':dict(price=155.64,currency='USD',quote='2026-10-22 10:31 EDT',eps_2027=14.08,period_end='2027-09-30',pe=155.64/14.08),
 'MRCY':dict(price=74.79,currency='USD',quote='2026-10-22 10:36 EDT',eps_2027=1.67,period_end='2027-06-30',pe=74.79/1.67),
}
valuation={}
for label,multiples in [('Bear',[8,10]),('Base',[11,14]),('Bull',[14,17])]:
    s=model['scenarios'][label]
    prices=[s['adj_eps']*m for m in multiples]
    valuation[label]=dict(eps=s['adj_eps'],pe=multiples,price_range=prices,return_pct=[(p/PRICE-1)*100 for p in prices],basis='2027E own segment model, adjusted EPS; multiples are research assumptions, not observed TTMI historical quantiles')
reverse={}
for pe in [10,11,12,14,15,20]:
    eps=PRICE/pe
    # Keep all Base segment variables other than Commercial margin fixed.
    needed_NI=eps*base['shares']
    needed_pretax=needed_NI/(1-base['tax'])
    needed_commercial_profit=needed_pretax+base['corporate']+base['net_interest']+base['other']-base['ad_segment_profit']
    reverse[str(pe)]=dict(required_eps=eps,discount_to_guide_mid_pct=(eps/8.5-1)*100,required_commercial_margin_pct=needed_commercial_profit/base['commercial_revenue']*100)
cash={}
for yield_pct in [4,6,8,10]:
    required=PRICE*VALUATION_SHARES*yield_pct/100
    cash[str(yield_pct)]=dict(required_FCF=required,required_FCF_to_Base_adjusted_NI_pct=required/base['adj_net_income']*100,required_FCF_per_share=required/VALUATION_SHARES)

# Cash-backed earnings capitalization sensitivity; no claim that raw FCF equals economic profit.
cash_multiples=[]
for conversion in [.4,.6,.8]:
    for required_yield in [.06,.08]:
        pe=conversion/required_yield
        cash_multiples.append(dict(conversion=conversion,required_cash_yield=required_yield,implied_PE=pe,base_price=pe*base['adj_eps']))
economic_eps=base['adj_eps']-(24.090*4)*(1-.22)/110
result=dict(ratios=ratios,peers=peers,valuation=valuation,reverse_PE=reverse,cash_yield=cash,cash_supported_multiples=cash_multiples,SBC_stress=dict(annual_SBC=24.09*4,after_tax_SBC_per_share=(24.09*4)*.78/110,economic_eps_proxy=economic_eps,price_to_economic_eps_proxy=PRICE/economic_eps),caveats=['Quote is fixed intraday snapshot, not close; peers same day but not same second','110 million is conservative future diluted-share assumption; not observed current common shares','Net debt reconstructed from book values, excludes fees and subsequent movements; not reported Sept30 net debt','LTM EBITDA excludes most Epiq earnings but net debt includes acquisition, so LTM EV/EBITDA is mismatched and not used as fair multiple','EPS forecasts are adjusted; WUS profit standard may differ and fiscal years end in different months','Original segment model retained; public company call transcript later says 108.1m 2027 shares, but original 110m conservative model kept separate','No Ophir contribution or additional acquisition financing assumed in 2027 scenarios'])
assert abs(LTM_FCF-47.422)<1e-6
assert abs(LTM_GAAP_NI-268.523)<1e-6
assert abs(NET_DEBT_PROXY-1867.525)<1e-6
assert ratios['guide_2027_PE_mid']<10
for label,v in valuation.items():
    assert v['price_range'][0]<v['price_range'][1]
(P/'2026-10-22_估值补充_计算结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
