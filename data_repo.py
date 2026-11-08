from pathlib import Path
import pandas as pd

CSV_latest = Path(__file__).parent / "data" / "latest.csv"


def load_csv(path) -> pd.DataFrame:
    """所有 CSV 读取的唯一入口。换存储只改这里。"""
    return pd.read_csv(path, encoding="utf-8-sig")


def load_latest() -> pd.DataFrame:
    """读最新快照。"""
    return load_csv(CSV_latest)
