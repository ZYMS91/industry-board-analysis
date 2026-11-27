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


def test_位置对调目前漏过_已知边界():
    """钉住当前行为：白名单只比数字集合，不比语义方向。

    对调「上涨 7 / 下跌 83」后每个数字仍在白名单里，check_numbers 放行 → exit 0。
    这是已知边界（2026-11-18 注入实验 4/5，见 reports/check-numbers-bench.txt）。
    哪天要修成「按字段名核对」，这条测试必须变红——那时删掉它、换成拦截断言。
    """
    nums = {"行数": 90, "上涨": 7, "下跌": 83}
    swapped = "今日 90 个板块中，上涨 83 个，下跌 7 个。"
    check_numbers(swapped, nums)   # 不抛异常 = 漏过（当前行为）


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

def test_写死的测试会被拦下():
    nums = {"行数":90,"上涨":23}
    text = "今日90个板块中，上涨23个（阈值0.5）。"
    with pytest.raises(SystemExit):
        check_numbers(text,nums)


# ---------- ISSUES #2：校验进 generate()，两个入口共用 ----------

def test_generate_rejects_bad_llm_text(monkeypatch):
    """LLM 编了白名单外的数字 → generate() 必须抛 NumberMismatch，而且要指出是哪个。

    守的是 summarize.generate() 末尾那句 `check_numbers(text, nums)`：
    删掉它，这条会红（会直接返回带 0.5 的文案）。
    """
    import summarize

    nums = {"行数": 90, "上涨": 58, "下跌": 32}
    monkeypatch.setattr(
        summarize, "llm_summary",
        lambda n: summarize.template_summary(n) + " 资金集中度约 0.5。",
    )

    with pytest.raises(summarize.NumberMismatch) as ei:
        summarize.generate(nums)

    assert ei.value.offenders == ["0.5"]
    assert ei.value.missing == []
    assert "无法溯源" in str(ei.value)


def test_generate_degrades_but_still_validates(monkeypatch):
    """没有 key → 降级成模板，且模板本身过校验（不能因为降级就跳过校验）。"""
    import summarize

    nums = {"行数": 90, "上涨": 58, "下跌": 32}
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    text = summarize.generate(nums)

    assert "90 个板块" in text
    assert "上涨 58 个" in text
    assert "下跌 32 个" in text


def test_check_numbers_has_single_call_site():
    """check_numbers 只允许有一个调用点（命令行和接口共用 generate()）。

    守的是 ISSUES #2 第 4 条验收标准：多一个调用点就说明又分叉了。
    """
    from pathlib import Path

    src = Path(__file__).parent.parent.joinpath("summarize.py").read_text(encoding="utf-8")
    calls = [
        line.strip() for line in src.splitlines()
        if "check_numbers(" in line and not line.strip().startswith("def ")
    ]
    assert len(calls) == 1, f"check_numbers 应该只有一个调用点，实际 {calls}"
    assert calls[0].startswith("check_numbers(text, nums)")
