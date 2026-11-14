"""verify_report.compare() 的测试。

compare 是纯函数（不读文件、不打印、只返回 (失败数, 消息)），
所以可以随便造假数据喂进去——这是把它从 main() 里抽出来的全部理由。
"""
import subprocess
import sys
from pathlib import Path

import pytest

from verify_report import compare

ROOT = Path(__file__).parent.parent

# 一组「全对」的基准数据：stats 侧是字符串（模拟 re.findall 的结果）
def _good():
    stats = {"n": "90", "up": "6", "down": "84", "r": "-0.2836"}
    nums = {"行数": 90, "上涨": 6, "下跌": 84, "r": -0.284}   # round(..., 3)
    return stats, nums


# ---------- 必选字段 ----------

def test_all_match():
    stats, nums = _good()
    失败, msgs = compare(stats, nums)
    assert 失败 == 0, msgs


def test_detects_up_mismatch():
    stats, nums = _good()
    nums["上涨"] = 7
    失败, msgs = compare(stats, nums)
    assert 失败 == 1
    assert "上涨" in msgs[0]


def test_detects_all_three_at_once():
    """三个字段全错时必须报 3 处，不能第一个就退出。"""
    stats, nums = _good()
    nums.update({"行数": 91, "上涨": 7, "下跌": 83})
    失败, msgs = compare(stats, nums)
    assert 失败 == 3
    assert len(msgs) == 3


def test_detects_missing_required_in_stats():
    stats, nums = _good()
    del stats["up"]
    失败, msgs = compare(stats, nums)
    assert 失败 >= 1
    assert any("缺少" in m for m in msgs)


# ---------- 可选字段 r：四态 ----------

def test_r_both_missing_is_ok():
    """甲：stats 说 r=NA，build_nums 没有 r 键 → 一致，不能报错。"""
    stats, nums = _good()
    stats["r"] = "NA"
    del nums["r"]
    失败, msgs = compare(stats, nums)
    assert 失败 == 0, msgs


def test_r_key_absent_both_sides_is_ok():
    """甲的另一形态：两边都没有 r 这个键。"""
    stats, nums = _good()
    del stats["r"]
    del nums["r"]
    失败, msgs = compare(stats, nums)
    assert 失败 == 0, msgs


def test_r_only_in_nums_is_error():
    """乙：stats 说没有，nums 说有 → 必须报错（最容易漏的一态）。"""
    stats, nums = _good()
    stats["r"] = "NA"
    失败, msgs = compare(stats, nums)
    assert 失败 == 1
    assert "r" in msgs[0]


def test_r_only_in_stats_is_error():
    """④ 反向：stats 有值，nums 没有 → 也必须报错。"""
    stats, nums = _good()
    del nums["r"]
    失败, msgs = compare(stats, nums)
    assert 失败 == 1
    assert "r" in msgs[0]


def test_r_value_differs_is_error():
    """丙：两边都有但差得多 → 报错。"""
    stats, nums = _good()
    nums["r"] = -0.5
    失败, msgs = compare(stats, nums)
    assert 失败 == 1
    assert "r" in msgs[0]


def test_r_rounding_difference_is_ok():
    """-0.2836 vs -0.284 是精度口径不同，不是错——按 3 位对齐后必须放过。

    这条是本文件的守门测试：把 round(..., 3) 删掉立刻变红。
    """
    stats, nums = _good()
    stats["r"] = "-0.2836"
    nums["r"] = -0.284
    失败, msgs = compare(stats, nums)
    assert 失败 == 0, msgs


# ---------- 真实数据端到端 ----------

@pytest.mark.skipif(not (ROOT / "data" / "latest.csv").exists(), reason="无数据快照")
def test_verify_report_passes_on_real_data():
    """真快照上跑完整脚本，必须退出码 0。"""
    r = subprocess.run(
        [sys.executable, "verify_report.py"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=180,
    )
    assert r.returncode == 0, f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    assert "校验通过" in r.stdout
