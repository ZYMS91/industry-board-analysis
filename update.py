# -*- coding: utf-8 -*-
r"""
抓一次数据，存成本地 CSV。下游脚本只读 CSV，不再联网。

用法：
    python update.py

生成：
    data/industry_YYYYMMDD_HHMMSS.csv   带时间戳的本次快照
    data/latest.csv                     最新一份，下游脚本读这个

设计要点：
  1. 多个数据源依次尝试，第一个成功就用（东财 → 同花顺）
  2. 不同源的字段名不一样，统一映射成同一套标准列
  3. 全部源都失败时，不报错退出，而是保留旧数据并提示
"""
from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
STANDARD_COLS = ["板块名称", "涨跌幅", "上涨家数", "下跌家数", "总市值", "换手率", "成交额"]


def from_eastmoney():
    """东方财富行业板块：字段最全（496 行左右）"""
    import akshare as ak

    df = ak.stock_board_industry_name_em()
    out = pd.DataFrame({
        "板块名称": df["板块名称"],
        "涨跌幅": df["涨跌幅"],
        "上涨家数": df["上涨家数"],
        "下跌家数": df["下跌家数"],
        "总市值": df["总市值"],
        "换手率": df["换手率"],
        "成交额": pd.NA,
    })
    return out, "东方财富"


def from_ths():
    """同花顺行业板块：没有总市值/换手率，但有成交额、净流入"""
    import akshare as ak

    df = ak.stock_board_industry_summary_ths()
    out = pd.DataFrame({
        "板块名称": df["板块"],
        "涨跌幅": df["涨跌幅"],
        "上涨家数": df["上涨家数"],
        "下跌家数": df["下跌家数"],
        "总市值": pd.NA,
        "换手率": pd.NA,
        "成交额": df["总成交额"],
    })
    return out, "同花顺"


SOURCES = [from_eastmoney, from_ths]


def main():
    DATA_DIR.mkdir(exist_ok=True)
    now = datetime.now()

    for fn in SOURCES:
        try:
            df, src = fn()
        except Exception as e:
            print(f"  × {fn.__name__} 失败：{type(e).__name__}")
            continue

        df = df[STANDARD_COLS]
        df.insert(0, "数据源", src)
        df.insert(1, "抓取时间", now.strftime("%Y-%m-%d %H:%M:%S"))

        stamp = now.strftime("%Y%m%d_%H%M%S")
        snap = DATA_DIR / f"industry_{stamp}.csv"
        df.to_csv(snap, index=False, encoding="utf-8-sig")
        df.to_csv(DATA_DIR / "latest.csv", index=False, encoding="utf-8-sig")

        missing = [c for c in ["总市值", "换手率", "成交额"] if df[c].isna().all()]
        print(f"  √ 数据源：{src}")
        print(f"    行数：{len(df)}")
        print(f"    快照：{snap.name}")
        if missing:
            print(f"    注意：该源不含这些字段 → {', '.join(missing)}")
        return

    # 全部失败：保留旧数据
    old = DATA_DIR / "latest.csv"
    if old.exists():
        prev = pd.read_csv(old, nrows=1)
        print("  ! 所有数据源都失败了，继续使用上次的数据")
        print(f"    上次抓取时间：{prev['抓取时间'][0]}  数据源：{prev['数据源'][0]}")
        print("    下游脚本可以照常运行。")
    else:
        print("  ! 所有数据源都失败，且本地没有历史数据。")
        print("    等接口恢复后重新运行 update.py")


if __name__ == "__main__":
    print(f"更新数据 …")
    main()
