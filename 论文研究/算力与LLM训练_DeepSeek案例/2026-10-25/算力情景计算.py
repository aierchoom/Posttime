"""Illustrative conditional model. Inputs are not empirically calibrated forecasts."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
config = json.loads((ROOT / '算力情景参数.json').read_text(encoding='utf-8'))
assert config['status'] == 'illustrative_uncalibrated_not_a_forecast'
share = config['training_share']
assert 0 <= share <= 1
assert config['end_year'] >= config['base_year']
rows = []
for s in config['scenarios']:
    assert s['alpha'] > 0 and 0 < s['residual_target_multiplier'] <= 1
    assert all(v > 0 for k, v in s.items() if k.endswith('multiplier'))
    per_run = s['residual_target_multiplier'] ** (-1 / s['alpha']) / s['training_algorithm_efficiency_multiplier']
    train = per_run * s['training_runs_multiplier']
    infer = s['query_multiplier'] * s['complexity_multiplier'] / s['inference_algorithm_efficiency_multiplier']
    for year in range(config['base_year'], config['end_year'] + 1):
        t = year - config['base_year']
        training_index = config['base_index'] * train ** t
        inference_index = config['base_index'] * infer ** t
        total_index = share * training_index + (1-share) * inference_index
        hardware_index = total_index / s['effective_per_device_throughput_multiplier'] ** t
        assert all(math.isfinite(x) and x > 0 for x in (training_index,inference_index,total_index,hardware_index))
        if t == 0:
            assert math.isclose(total_index, config['base_index'])
        rows.append(dict(scenario=s['name'],year=year,training_compute_index=training_index,
                         inference_compute_index=inference_index,total_compute_index=total_index,
                         compute_only_device_lower_bound_index=hardware_index,
                         annual_single_run_multiplier=per_run,
                         status=config['status']))
out = ROOT / '算力情景结果.csv'
with out.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
print('ILLUSTRATIVE, UNCALIBRATED; not a market prediction or confidence interval.')
for row in rows:
    if row['year']==config['end_year']:
        print(f"{row['scenario']}: total_compute_index={row['total_compute_index']:.2f}; "
              f"compute_only_device_lower_bound_index={row['compute_only_device_lower_bound_index']:.2f}")
print(f'Wrote {len(rows)} rows to {out.name}')
