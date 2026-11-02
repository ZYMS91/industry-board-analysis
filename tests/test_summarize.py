from summarize import build_nums
import pytest
from summarize import check_numbers
from summarize import template_summary
from summarize import generate

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

def test_check_numbers_no_digits():
    with pytest.raises(SystemExit):
        check_numbers("这段文字里一个数字都没有", {"行数": 90, "上涨": 7})

def test_template_summary_contains_all_numbers():
    nums = {"行数": 90, "上涨": 7, "下跌": 83, "r": -0.263, "top5_集中度": 30.0}
    text = template_summary(nums)
    assert "90" in text
    assert "7" in text
    assert "83" in text
    assert "-0.263" in text
    assert "30.0" in text

def test_generate_falls_back_without_key(monkeypatch):
    # 把环境变量删掉，模拟"用户没配 key"
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    nums = {"行数": 90, "上涨": 7, "下跌": 83, "r": -0.263, "top5_集中度": 30.0}
    text = generate(nums)

    assert text == template_summary(nums)
