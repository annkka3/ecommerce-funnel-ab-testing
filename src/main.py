import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / 'data/funnel_events.csv')
steps = ['visit','product_view','add_to_cart','checkout','purchase']
summary = []
for group, g in df.groupby('ab_group'):
    row = {'ab_group': group, 'users': len(g), 'revenue': g['revenue'].sum(), 'arpu': g['revenue'].sum()/len(g)}
    for s in steps:
        row[f'{s}_rate'] = g[s].mean()
        row[f'{s}_count'] = g[s].sum()
    summary.append(row)
summary = pd.DataFrame(summary)

control = df[df.ab_group=='control']['purchase']
variant = df[df.ab_group=='variant']['purchase']
conv_c, conv_v = control.mean(), variant.mean()
uplift = (conv_v/conv_c - 1) * 100
# two-proportion z-test
p_pool = (control.sum()+variant.sum())/(len(control)+len(variant))
se = np.sqrt(p_pool*(1-p_pool)*(1/len(control)+1/len(variant)))
z = (conv_v-conv_c)/se
p_value = 2*(1-stats.norm.cdf(abs(z)))

ab_result = pd.DataFrame([{
    'control_conversion': conv_c,
    'variant_conversion': conv_v,
    'uplift_pct': uplift,
    'z_score': z,
    'p_value': p_value,
    'decision': 'ship variant' if p_value < 0.05 and uplift > 0 else 'do not ship yet'
}])

(ROOT/'results').mkdir(exist_ok=True)
summary.to_csv(ROOT/'results/funnel_summary.csv', index=False)
ab_result.to_csv(ROOT/'results/ab_test_result.csv', index=False)

plot = summary.set_index('ab_group')[[f'{s}_rate' for s in steps]].T
plt.figure(figsize=(8,4))
for col in plot.columns:
    plt.plot(steps, plot[col], marker='o', label=col)
plt.title('E-commerce funnel conversion by A/B group')
plt.ylabel('Step conversion rate')
plt.xticks(rotation=30)
plt.legend()
plt.tight_layout()
plt.savefig(ROOT/'results/funnel_conversion_by_group.png', dpi=160)

print(ab_result.to_string(index=False))
