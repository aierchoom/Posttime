"""Q2经营速度校验及盈利/PE二维敏感性；不改动原三情景输入。"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
m = json.loads((ROOT / '经营估值模型.json').read_text(encoding='utf-8'))
shares, price = m['facts']['shares'], m['facts']['price']
h1 = m['facts']['H1_parent']
q1 = 1158139324.56 / 1e8
q1_adj = 1082821715.86 / 1e8
h1_adj = 2907702351.56 / 1e8
q2, q2_adj = h1 - q1, h1_adj - q1_adj
base_h2 = m['models']['Base']['h2_2026']['parent']
out = {
    'units': 'CNY亿元/亿股/元每股；PE倍',
    'date': '2026-09-21',
    'price_date': '2026-09-18',
    'unchanged_original_models': True,
    'sources': {'Q1': 'S25第1页', 'H1': 'S1第5页', 'model': 'S23'},
    'run_rate': {
        'Q1_parent': q1, 'Q1_adjusted': q1_adj,
        'H1_parent': h1, 'H1_adjusted': h1_adj,
        'Q2_parent': q2, 'Q2_adjusted': q2_adj,
        'Q2_nonrecurring': q2 - q2_adj,
        'Q2_adjusted_qoq': q2_adj / q1_adj - 1,
        'Base_H2_parent': base_h2,
        'Base_H2_vs_H1': base_h2 / h1 - 1,
        'Base_H2_quarter_average': base_h2 / 2,
        'Base_H2_quarter_vs_Q2_reported': base_h2 / 2 / q2 - 1,
        'Base_H2_quarter_vs_Q2_adjusted': base_h2 / 2 / q2_adj - 1,
        'FY26_Q2_adjusted_flat_H2': h1 + 2 * q2_adj,
        'FY26_Q2_reported_flat_H2': h1 + 2 * q2,
        'caveat': '两种平推仅为运行速度校验，不是预测；Q2归母含非经常性。扣非平推假设H2两个季度各等于Q2扣非且无新非经常性，未调整少数权益变化、季节性与爬坡成本。原Base H2仍含其他收益/投资收益，非严格扣非口径。'
    },
    'matrix': [],
    'required_parent_at_reference_price': {str(pe): price * shares / pe for pe in [30, 35, 40]},
    'notes': '矩阵固定中央EPS，不加原EPS半宽。PE是条件假设，不是市场保证；不赋主观概率。'
}
for case in ['Base', 'Bull']:
    n = m['models'][case]['fy2027']['parent']
    eps = n / shares
    out['matrix'].append({'earnings_case': case, 'parent': n, 'eps': eps,
        'valuation_by_pe': {str(pe): {'price': eps * pe, 'versus_reference_price': eps * pe / price - 1} for pe in [30, 35, 40]}})
assert q2_adj > q1_adj
assert base_h2 < 2 * q2_adj < 2 * q2
assert abs(out['matrix'][0]['eps'] - m['models']['Base']['fy2027']['eps']) < 1e-12
(ROOT / 'Base审慎性复核.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(out, ensure_ascii=False, indent=2))
