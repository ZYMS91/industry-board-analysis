import pandas as pd

from check_freshness import evaluate


def test_evaluate_ok():
    df = pd.DataFrame({"抓取时间": ["2026-11-10 15:35:00"], "涨跌幅": [1.0]})
    assert evaluate(df, "2026-11-10") == ("OK", "2026-11-10")


def test_evaluate_stale():
    df = pd.DataFrame({"抓取时间": ["2026-11-09 15:35:00"], "涨跌幅": [1.0]})
    assert evaluate(df, "2026-11-10") == ("STALE", "2026-11-09")


def test_evaluate_bad():
    df = pd.DataFrame({"抓取时间": ["2026-11-10 15:35:00"], "涨跌幅": [None]})
    assert evaluate(df, "2026-11-10") == ("BAD", "2026-11-10")
