"""stats.py 的回归测试：496 行快照上跑通、不崩、r 为空时如实输出 NA。

注：stats.py 顶层就执行 sys.argv[1]，无法 import，只能作为子进程运行。
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
CSV = ROOT / "data" / "latest.csv"


def _run(csv_path):
    return subprocess.run(
        [sys.executable, "stats.py", str(csv_path)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=180,
    )


def _make_csv(path, n=496, with_amount=True):
    """造快照。with_amount=False 时成交额整列空（东财源的真实情况）。"""
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(0)
    data = {
        "板块名称": [f"B{i}" for i in range(n)],
        "涨跌幅": np.round(rng.standard_normal(n) * 2, 2),
        "成交额": (np.round(rng.random(n) * 100 + 1, 2) if with_amount else [None] * n),
    }
    pd.DataFrame(data).to_csv(path, index=False, encoding="utf-8-sig")


def test_large_n_with_amount_does_not_overflow(tmp_path):
    """n=496 时 gamma(247.5) 超出 float 上限 1.8e308，lgamma 版本必须扛住。

    这是本文件的守门测试：把 lgamma 改回 gamma 立刻变红。
    """
    csv = tmp_path / "with_amt.csv"
    _make_csv(csv, n=496, with_amount=True)
    r = _run(csv)
    assert r.returncode == 0, f"退出码 {r.returncode}\nstderr:\n{r.stderr}"
    assert "OverflowError" not in r.stderr

    line = next(l for l in r.stdout.splitlines() if l.startswith("r="))
    assert "r=NA" not in line, f"成交额有值时 r 应是真实数字：{line}"
    p = float(line.split("p=")[1])
    assert 0.0 <= p <= 1.0, f"p={p} 不在 [0,1]"


def test_empty_amount_outputs_na_not_zero(tmp_path):
    """成交额全空时必须输出 NA，不能填 0（pandas 的 sum() 会把全 NaN 列算成 0.0）。"""
    csv = tmp_path / "no_amt.csv"
    _make_csv(csv, n=496, with_amount=False)
    r = _run(csv)
    assert r.returncode == 0, r.stderr

    line = next(l for l in r.stdout.splitlines() if l.startswith("r="))
    assert line == "r=NA R2=NA p=NA", line
    assert "全市场 NA" in r.stdout, "全市场成交额必须是 NA，不能是 0.00"


@pytest.mark.skipif(not CSV.exists(), reason="无数据快照")
def test_real_snapshot_runs():
    """真实快照（东财源，成交额全空）必须跑通且无 Traceback。"""
    r = _run(CSV)
    assert r.returncode == 0, r.stderr
    assert "Traceback" not in r.stderr
