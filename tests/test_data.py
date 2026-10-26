import pytest
import pandas as pd
from pathlib import Path

CSV = Path(__file__).parent.parent / "data" / "latest.csv"

@pytest.mark.skipif(not CSV.exists(), reason="没有快照文件，跳过数据校验")
def test_latest_snapshot_is_sane():
    df = pd.read_csv(CSV, encoding="utf-8-sig")
    assert len(df)>0          # 断言1：这份快照至少要有数据（行数不能是 0）
    assert df['涨跌幅'].between(-20,20).all()          # 断言2：涨跌幅全部落在合理区间（盘中 -20% ~ +20%）
