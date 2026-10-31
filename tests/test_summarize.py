from summarize import build_nums
import pytest

def test_build_nums(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("""涨跌幅,成交额
1.0,100
-1.0,300
0.5,600
""", encoding="utf-8-sig")

    nums = build_nums(p)

    assert nums["行数"] == 3
    assert nums["上涨"] == 2
    assert nums["下跌"] == 1
    assert nums["top5_集中度"] == 100.0
    assert nums["r"] == pytest.approx(-0.127, abs=1e-3)
    assert set(nums) == {"行数", "上涨", "下跌", "r", "top5_集中度"}
