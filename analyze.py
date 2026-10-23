# -*- coding: utf-8 -*-
r"""
行业板块分析：三个问题。

数据从 data/latest.csv 读（由 update.py 生成），不联网。

运行：
    python analyze.py
"""
import pandas as pd
from pathlib import Path

# ===== 加载数据 =====
csv_path = Path(__file__).parent / "data" / "latest.csv"
if not csv_path.exists():
    print("找不到 data/latest.csv")
    print("请先运行：python update.py  （抓取数据并生成 CSV）")
    raise SystemExit(1)
df = pd.read_csv(csv_path, encoding="utf-8-sig")



def pick(df, candidates):
    """从候选字段名里，挑出第一个「存在且有值」的。都没有就返回 None。

    为什么需要这个：不同数据源字段不一样。东财有总市值/换手率，
    同花顺没有。如果直接 df['换手率']，拿到的是全空列，
    算出来的结果看着正常、其实是错的 —— 这种静默错误最危险。
    """
    for col in candidates:
        if col in df.columns and df[col].notna().any():
            return col
    return None


# ===== 数据自检（每次分析前都要做）=====
print("数据来源:", df["数据源"][0], "| 抓取时间:", df["抓取时间"][0])
print("行数:", len(df), "| 列数:", len(df.columns))

liquidity_col = pick(df, ["换手率", "成交额"])   # 流动性指标
value_col = pick(df, ["总市值", "成交额"])       # 规模指标
print("流动性字段 →", liquidity_col or "无可用字段")
print("规模字段   →", value_col or "无可用字段")
print()


# ===== 问题 1：涨幅最高的 5 个行业 =====
print("=" * 46)
print("问题1：涨幅最高的 5 个行业")
print(df.sort_values('涨跌幅', ascending=False)[['板块名称', '涨跌幅']].head(5).to_string(index=False))


# ===== 问题 2：涨跌幅和流动性有关系吗？=====
print("=" * 46)
print("问题2：涨跌幅 与 流动性的相关性")
if liquidity_col is None:
    print("跳过：本数据源没有可用的流动性字段")
else:
    if liquidity_col != "换手率":
        print(f"（注意：本数据源无换手率，改用 {liquidity_col}）")
    r = df['涨跌幅'].corr(df[liquidity_col])
    print(f"与 {liquidity_col} 的相关系数 = {r:.4f}")


# ===== 问题 3：规模最大的 5 个行业里，有几个上涨 =====
print("=" * 46)
print("问题3：规模 Top5 中有几个上涨")
if value_col is None:
    print("跳过：本数据源没有可用的规模字段")
else:
    if value_col != "总市值":
        print(f"（注意：本数据源无总市值，改用 {value_col}）")
    top5 = df.sort_values(value_col, ascending=False).head(5)
    print(top5[['板块名称', value_col, '涨跌幅']].to_string(index=False))
    print(f"上涨个数 = {(top5['涨跌幅'] > 0).sum()} / 5")
