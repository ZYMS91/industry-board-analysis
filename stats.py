"""Compute the numbers the README/reports need from a local snapshot. Read-only."""
import math
import sys
from data_repo import load_csv
import pandas as pd

CSV = sys.argv[1]
df = load_csv(CSV)

n = len(df)
up = int((df['涨跌幅'] > 0).sum())
down = int((df['涨跌幅'] < 0).sum())
flat = int((df['涨跌幅'] == 0).sum())
lo, hi = df['涨跌幅'].min(), df['涨跌幅'].max()
r = df['涨跌幅'].corr(df['成交额'])

# two-sided p for Pearson r, no scipy: t -> numeric integration of the t pdf
def t_p(r, n):
    if n < 4 or abs(r) >= 1:
        return float('nan')
    t = abs(r) * math.sqrt(n - 2) / math.sqrt(1 - r * r)
    dfree = n - 2
    c = math.gamma((dfree + 1) / 2) / (math.sqrt(dfree * math.pi) * math.gamma(dfree / 2))
    f = lambda u: c * (1 + u * u / dfree) ** (-(dfree + 1) / 2)
    lo_b, steps, h = t, 4000, (t * 12) / 4000
    s = f(lo_b) + f(lo_b + steps * h)
    for i in range(1, steps):
        s += f(lo_b + i * h) * (4 if i % 2 else 2)
    tail = s * h / 3
    return 2 * tail

top5 = df.sort_values('涨跌幅', ascending=False).head(5)
amt5 = df.sort_values('成交额', ascending=False).head(5)
total_amt = df['成交额'].sum()

print(f'FILE {CSV}')
print(f'n={n} up={up} down={down} flat={flat} range={lo:.2f}~{hi:.2f}')
print(f'r={r:.4f} R2={r * r:.4f} p={t_p(r, n):.4f}')
print('--- 涨跌幅 Top5 ---')
for _, row in top5.iterrows():
    print(f"  {row['板块名称']}\t{row['涨跌幅']:+.2f}%\t成交额 {row['成交额']:.2f}")
print(f'--- 成交额 Top5 (上涨 {int((amt5["涨跌幅"] > 0).sum())}/{len(amt5)}) ---')
for _, row in amt5.iterrows():
    print(f"  {row['板块名称']}\t{row['成交额']:.2f}\t{row['涨跌幅']:+.2f}%")
print(f'成交额 Top5 合计 {amt5["成交额"].sum():.2f} / 全市场 {total_amt:.2f} = {amt5["成交额"].sum() / total_amt:.1%}')
print(f'上涨板块: {", ".join(df[df["涨跌幅"] > 0].sort_values("涨跌幅", ascending=False)["板块名称"].tolist()) or "无"}')
print(f'下跌板块数前3: {", ".join(df.sort_values("涨跌幅")[["板块名称"]].head(3)["板块名称"].tolist())}')
