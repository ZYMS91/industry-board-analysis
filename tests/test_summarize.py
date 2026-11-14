from summarize import build_nums
import pytest
from summarize import check_numbers
from summarize import template_summary
from summarize import generate
from summarize import market_mood

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
    assert f"今日 {nums['行数']} 个板块" in text
    assert f"上涨 {nums['上涨']} 个" in text
    assert f"下跌 {nums['下跌']} 个" in text
    assert f"r={nums['r']}" in text
    assert f"占全市场 {nums['top5_集中度']}%" in text

def test_generate_falls_back_without_key(monkeypatch):
    # 把环境变量删掉，模拟"用户没配 key"
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    nums = {"行数": 90, "上涨": 7, "下跌": 83, "r": -0.263, "top5_集中度": 30.0}
    text = generate(nums)

    assert text == template_summary(nums)

def test_check_numbers_accepts_valid_text():
    nums = {"行数": 90, "上涨": 7, "下跌": 83, "r": -0.263, "top5_集中度": 30.0}
    text = template_summary(nums)
    check_numbers(text, nums)      # 正常文案不该抛异常

def test_check_numbers_rejects_duplicates():
    nums = {"行数": 90, "上涨": 7, "下跌": 83, "r": -0.263, "top5_集中度": 30.0}
    with pytest.raises(SystemExit):
        check_numbers("90 90 90 90 90", nums)

def test_build_nums_without_amount_column(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("""涨跌幅
1.0
-1.0
0.5
""", encoding="utf-8-sig")

    nums = build_nums(p)
    assert set(nums) == {"行数", "上涨", "下跌"}

def test_market_mood():
    assert market_mood({"上涨": 84, "下跌": 6}) == "普涨"
    assert market_mood({"上涨": 7, "下跌": 83}) == "普跌"
    assert market_mood({"上涨": 45, "下跌": 45}) == "分化"


def test_build_nums_rejects_all_nan_column(tmp_path):
    """涨跌幅整列为空时必须抛 ValueError，不能返回一堆 0。

    守的是 summarize.py 里这两行：
        if df["涨跌幅"].notna().sum() == 0:
            raise ValueError("涨跌幅列全为空，本份快照无法使用")
    删掉它们，这条必须变红。
    """
    import pandas as pd

    p = tmp_path / "all_nan.csv"
    pd.DataFrame({
        "板块名称": ["A", "B"],
        "涨跌幅": [None, None],
    }).to_csv(p, index=False, encoding="utf-8-sig")

    with pytest.raises(ValueError, match="涨跌幅列全为空"):
        build_nums(p)

