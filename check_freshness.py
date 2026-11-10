from datetime import date
from pathlib import Path
import pandas as pd
from data_repo import load_csv

CSV = Path(__file__).parent / "data" / "latest.csv"
LOG = Path(__file__).parent/"logs"/"freshness.log"
LOG.parent.mkdir(exist_ok=True)

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{date.today()} | {msg}\n")
if not CSV.exists():
    print("警告：latest.csv 不存在，从未采集成功")# 1. 如果没有 latest.csv → 直接告警（连数据都没有）
    log("FAIL not latest.csv")
    raise SystemExit(1)

df = load_csv(CSV)
fetched = df ["抓取时间"][0][:10]
today = str(date.today())# 2. 读「抓取时间」第一行，取前 10 位（"2026-11-09"）

if fetched == today:
    # 日期对了，再查关键字段是否有值
    full = load_csv(CSV)                    # 这次读全表，不要 nrows=1
    if full["涨跌幅"].notna().sum() == 0:
        print(f"警告：数据日期是今天，但涨跌幅列全空")
        log(f"BAD {fetched} 涨跌幅全空")
        raise SystemExit(1)

    print(f"正常：数据日期 {fetched}")
    log(f"OK {fetched}")

else: # 3. 和 str(date.today()) 比
    print(f"警告:数据不是今天的，最新是{fetched}")
    log(f"STALE 最新 {fetched}")
    raise SystemExit(1)
# 4. 不相等 → 打印警告 + 写进 freshness.log
# 5. 相等 → 写一行正常记录（有记录才能证明"它在工作）
