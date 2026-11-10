import pandas as pd
from check_freshness import evaluate


# 假数据统一造 50 行以上，避开"行数不足"这条规则，
# 才能单独验证日期和字段检查。只有 too_few_rows 故意造 10 行。
ROWS = 50


def test_evaluate_ok():
    df = pd.DataFrame(
        {"抓取时间": ["2026-11-10 15:35:00"] * ROWS, "涨跌幅": [1.0] * ROWS}
    )
    assert evaluate(df, "2026-11-10") == ("OK", "2026-11-10")


def test_evaluate_stale():
    df = pd.DataFrame(
        {"抓取时间": ["2026-11-09 15:35:00"] * ROWS, "涨跌幅": [1.0] * ROWS}
    )
    assert evaluate(df, "2026-11-10") == ("STALE", "2026-11-09")


def test_evaluate_bad():
    # 行数够，但涨跌幅全是空值 → 必须是因为"字段全空"才判 BAD
    df = pd.DataFrame(
        {"抓取时间": ["2026-11-10 15:35:00"] * ROWS, "涨跌幅": [None] * ROWS}
    )
    assert evaluate(df, "2026-11-10") == ("BAD", "2026-11-10")

def test_evaluate_too_few_rows():
    df = pd.DataFrame({
        "抓取时间": ["2026-11-10 15:35:00"] * 10,
        "涨跌幅": [1.0] * 10,
    })
    assert evaluate(df, "2026-11-10") == ("BAD", "2026-11-10")
