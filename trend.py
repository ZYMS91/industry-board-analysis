"""按数据源把快照分组，算同源相邻两天的涨跌家数差。

独立分析脚本：不被 app.py / stats.py / summarize.py import，
坏了不影响每天 15:35 的采集和 /summary 接口。
"""
from pathlib import Path
import re

import pandas as pd

from data_repo import load_csv

DATA = Path(__file__).parent / "data"

def load_snapshots():
    """返回 {行数: {日期: 文件名}}，同一天多份只留时间最晚的。"""
    files = sorted(DATA.glob("industry_*.csv"))
    groups = {}

    for f in files:
        # 从文件名拿日期和时间：industry_20261106_153501.csv
        m = re.match(r"industry_(\d{8})_(\d{6})\.csv", f.name)
        if not m:
            continue
        日期, 时间 = m.group(1), m.group(2)

        行数 = sum(1 for _ in f.open(encoding="utf-8-sig")) - 1   # 减表头

        组 = groups.setdefault(行数, {})
        # 同一天多份：比时间字符串，留大的
        if 日期 not in 组 or 时间 > 组[日期][0]:
            组[日期] = (时间, f.name)
    return groups

def _count(文件名):
    """读一份快照，返回 (上涨家数, 下跌家数)。"""
    df = load_csv(DATA / 文件名)
    return int((df["涨跌幅"] > 0).sum()), int((df["涨跌幅"] < 0).sum())

def diffs(groups):
    """同源内相邻两天的涨跌家数差。

    返回 [(行数, 前日期, 后日期, Δ上涨, Δ下跌, 说明)]
    """
    # 所有出现过的日期，用来判断两个同源日之间是否夹着异源日
    全部日期 = sorted({d for 组 in groups.values() for d in 组})

    结果 = []

    for 行数 in sorted(groups):
        组 = groups[行数]
        日期列表 = sorted(组)

        for 前, 后 in zip(日期列表, 日期列表[1:]):
            前up, 前down = _count(组[前][1])
            后up, 后down = _count(组[后][1])

            # 前和后之间还有别的日期 → 那些是异源，被跳过了
            夹着 = [d for d in 全部日期 if 前 < d < 后]
            说明 = f"（跳过 {'/'.join(夹着)}，异源）" if 夹着 else ""

            结果.append((行数, 前, 后, 后up - 前up, 后down - 前down, 说明))

    return 结果





def main():
    groups = load_snapshots()

    for 行数 in sorted(groups):
        组 = groups[行数]
        源 = "同花顺" if 行数 < 200 else "东财"
        print(f"{行数} 行（{源}）：{len(组)} 份")
        for 日期 in sorted(组):
            时间, 文件名 = 组[日期]
            print(f"  {日期[:4]}-{日期[4:6]}-{日期[6:]}  取 {时间}  {文件名}")
        print()

    print("=== 日环比（同源内）===")
    for 行数, 前, 后, du, dd, 说明 in diffs(groups):
        print(f"[{行数}行] {前} → {后}  Δ上涨 {du:+d}  Δ下跌 {dd:+d}  {说明}")



if __name__ == "__main__":
    main()
