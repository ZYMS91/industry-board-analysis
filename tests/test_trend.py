"""trend.py 的口径测试：分组键、异源跳过、缺口标注、Δ下跌独立。

全部离线：CSV 用 tmp_path 现造，或直接 monkeypatch _count，不碰真实数据和网络。
"""
import pandas as pd
import pytest

import trend


COLS = ["数据源", "抓取时间", "板块名称", "涨跌幅", "上涨家数", "下跌家数",
        "总市值", "换手率", "成交额"]


def _写快照(dir, 文件名, 源, 涨跌幅):
    n = len(涨跌幅)
    df = pd.DataFrame({
        "数据源": [源] * n,
        "抓取时间": ["2026-11-05 15:35:02"] * n,
        "板块名称": [f"板块{i}" for i in range(n)],
        "涨跌幅": 涨跌幅,
        "上涨家数": [0] * n,
        "下跌家数": [0] * n,
        "总市值": [None] * n,
        "换手率": [None] * n,
        "成交额": [None] * n,
    })[COLS]
    df.to_csv(dir / 文件名, index=False, encoding="utf-8-sig")


def test_按数据源分组而不是按行数(tmp_path, monkeypatch):
    """同源不同行数必须归一组；异源必须分开。行数一变就劈组 = 这个测试红。"""
    monkeypatch.setattr(trend, "DATA", tmp_path)
    _写快照(tmp_path, "industry_20261105_120000.csv", "同花顺", [1.0, 2.0])            # 2 行
    _写快照(tmp_path, "industry_20261105_153502.csv", "同花顺", [1.0, 2.0, 3.0])      # 3 行，同日更晚
    _写快照(tmp_path, "industry_20261106_153502.csv", "东方财富", [1.0, -2.0, 0.0, 0.0])

    g = trend.load_snapshots()

    assert sorted(g) == ["东方财富", "同花顺"]
    assert list(g["同花顺"]) == ["20261105"]          # 同日两份只留一份
    assert g["同花顺"]["20261105"] == ("153502", "industry_20261105_153502.csv")
    assert list(g["东方财富"]) == ["20261106"]


def test_异源日标成跳过且不参与配对(monkeypatch):
    """1106 只有东财；同花顺 1105→1109 这一对要跳过它，而不是跟它配对。
    1107/1108 是周末，不该被写成缺快照。"""
    groups = {
        "同花顺": {"20261105": ("153502", "a.csv"), "20261109": ("153502", "b.csv")},
        "东方财富": {"20261106": ("153501", "c.csv")},
    }
    假计数 = {"a.csv": (10, 20), "b.csv": (30, 20), "c.csv": (0, 0)}
    monkeypatch.setattr(trend, "_count", lambda 文件名: 假计数[文件名])

    结果 = trend.diffs(groups)

    assert len(结果) == 2 - 1                          # 异源那天不生成额外配对
    源, 前, 后, du, dd, 说明 = 结果[0]
    assert (源, 前, 后) == ("同花顺", "20261105", "20261109")
    assert 说明 == "（跳过异源 20261106）"              # 周末不掺进来
    assert (du, dd) == (20, 0)                         # 涨 +20、跌不变，两条各自算


def test_缺快照与异源分开标(monkeypatch):
    """中间两个工作日任何源都没有 → 只标「缺快照」，不能混成异源。"""
    groups = {"同花顺": {"20261109": ("153502", "a.csv"), "20261112": ("153502", "b.csv")}}
    monkeypatch.setattr(trend, "_count", lambda 文件名: (10, 20))

    结果 = trend.diffs(groups)

    assert len(结果) == 1
    说明 = 结果[0][5]
    assert 说明 == "（缺快照 20261110/20261111）"
    assert "异源" not in 说明


def test_Δ下跌不复用负Δ上涨(tmp_path, monkeypatch):
    """平盘板块转涨：上涨 +1、下跌不变。若 dd 写成 -du，这里会红成 (1, -1)。"""
    monkeypatch.setattr(trend, "DATA", tmp_path)
    _写快照(tmp_path, "industry_20261105_153502.csv", "同花顺", [1.0, -1.0, 0.0])
    _写快照(tmp_path, "industry_20261106_153502.csv", "同花顺", [1.0, -1.0, 2.0])

    结果 = trend.diffs(trend.load_snapshots())

    assert len(结果) == 1
    _, 前, 后, du, dd, _ = 结果[0]
    assert (前, 后) == ("20261105", "20261106")
    assert (du, dd) == (1, 0)
