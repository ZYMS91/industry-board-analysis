from datetime import date
from pathlib import Path
import pandas as pd
from data_repo import load_csv

CSV = Path(__file__).parent / "data" / "latest.csv"
LOG = Path(__file__).parent / "logs" / "freshness.log"
LOG.parent.mkdir(exist_ok=True)


def evaluate(df, today_str):
    """纯函数：给数据和今天的日期，返回 (状态, 详情)。
    状态只有三种：OK / STALE / BAD
    """
    fetched = str(df["抓取时间"][0])[:10]

    if fetched != today_str:
        return "STALE", fetched

    if df["涨跌幅"].notna().sum() == 0:
        return "BAD", fetched

    if len(df) < 50:
        return "BAD", fetched


    return "OK", fetched


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{date.today()} | {msg}\n")


def main():
    if not CSV.exists():
        print("警告：latest.csv 不存在，从未采集成功")
        log("FAIL 无 latest.csv")
        return 1

    df = load_csv(CSV)
    status, detail = evaluate(df, str(date.today()))

    if status == "OK":
        print(f"正常：数据日期 {detail}")
        log(f"OK {detail}")
        return 0
    elif status == "STALE":
        print(f"警告：数据不是今天的，最新是 {detail}")
        log(f"STALE 最新 {detail}")
        return 1
    else:
        print("警告：数据日期是今天，但涨跌幅列全空")
        log(f"BAD {detail} 涨跌幅全空")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
