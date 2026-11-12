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


def fmt(x, p=4):
    """如实输出：算不出来的显示 NA，不填 0。"""
    if x is None or not isinstance(x, (int, float)) or not math.isfinite(x):
        return "NA"
    return f"{x:.{p}f}"


# two-sided p for Pearson r, no scipy: t -> numeric integration of the t pdf
def t_p(r, n):
    if n < 4 or not math.isfinite(r) or abs(r) >= 1:
        return float('nan')
    t = abs(r) * math.sqrt(n - 2) / math.sqrt(1 - r * r)
    dfree = n - 2
    # 用 lgamma 在对数空间算常数项：直接算 gamma(247.5) 会 overflow
    c = math.exp(math.lgamma((dfree + 1) / 2) - math.lgamma(dfree / 2)) / math.sqrt(dfree * math.pi)
    f = lambda u: c * (1 + u * u / dfree) ** (-(dfree + 1) / 2)
    lo_b, steps, h = t, 4000, (t * 12) / 4000
    s = f(lo_b) + f(lo_b + steps * h)
    for i in range(1, steps):
        s += f(lo_b + i * h) * (4 if i % 2 else 2)
    tail = s * h / 3
    return 2 * tail

top5 = df.sort_values('涨跌幅', ascending=False).head(5)
amt5 = df.sort_values('成交额', ascending=False).head(5)
# pandas 对全 NaN 列 sum() 返回 0.0 而不是 NaN，必须显式判空，否则输出假的 0
_amt_all_nan = bool(df['成交额'].isna().all())
total_amt = float('nan') if _amt_all_nan else df['成交额'].sum()

print(f'FILE {CSV}')
print(f'n={n} up={up} down={down} flat={flat} range={lo:.2f}~{hi:.2f}')
print(f'r={fmt(r)} R2={fmt(r * r if math.isfinite(r) else float("nan"))} p={fmt(t_p(r, n))}')
print('--- 涨跌幅 Top5 ---')
for _, row in top5.iterrows():
    print(f"  {row['板块名称']}\t{row['涨跌幅']:+.2f}%\t成交额 {fmt(row['成交额'], 2)}")
print(f'--- 成交额 Top5 (上涨 {int((amt5["涨跌幅"] > 0).sum())}/{len(amt5)}) ---')
for _, row in amt5.iterrows():
    print(f"  {row['板块名称']}\t{fmt(row['成交额'], 2)}\t{row['涨跌幅']:+.2f}%")
amt5_sum = float('nan') if _amt_all_nan else amt5["成交额"].sum()
ratio = amt5_sum / total_amt if math.isfinite(total_amt) and total_amt else float("nan")
print(f'成交额 Top5 合计 {fmt(amt5_sum, 2)} / 全市场 {fmt(total_amt, 2)} = {fmt(ratio * 100, 1)}%')
print(f'上涨板块: {", ".join(df[df["涨跌幅"] > 0].sort_values("涨跌幅", ascending=False)["板块名称"].tolist()) or "无"}')
print(f'下跌板块数前3: {", ".join(df.sort_values("涨跌幅")[["板块名称"]].head(3)["板块名称"].tolist())}')
