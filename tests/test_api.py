from fastapi.testclient import TestClient
import pytest
from pathlib import Path
import app as app_module
import summarize


CSV = Path(__file__).parent.parent / "data" / "latest.csv"

# 没有快照文件时跳过（克隆仓库后 data/ 里没有 CSV）
pytestmark = pytest.mark.skipif(not CSV.exists(), reason="没有快照文件，跳过接口测试")



def test_summary_endpoint_ok(monkeypatch):
    # 用假函数替换 LLM 调用：测试不花 API 钱、不依赖网络。
    # 注意：假函数必须返回「模板文案 + 一句无数字评述」——generate() 现在会做双向校验，
    # 只返回一句「测试评述」会因为缺少全部字段值被拒（这正是本次改造的效果）。
    monkeypatch.setattr(
        "summarize.llm_summary",
        lambda nums: summarize.template_summary(nums) + " 资金集中在头部。",
    )

    from app import app
    client = TestClient(app)
    r = client.get("/summary")

    assert r.status_code == 200
    d = r.json()
    assert d["date"]
    assert {"行数", "上涨", "下跌"} <= set(d["nums"])
    assert "资金集中在头部" in d["summary"]


def test_summary_ok_without_key(monkeypatch):
    """没有 API key → 走模板文案，接口 200。"""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    client = TestClient(app_module.app)
    r = client.get("/summary")

    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"date", "nums", "summary"}
    assert body["summary"], "摘要不能为空"
    assert body["nums"]["行数"] > 0


def test_summary_200_when_llm_raises(monkeypatch):
    """LLM 抛非预期异常（KeyError）也必须 200 —— 验证 except Exception 够宽。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake")

    def boom(nums):
        raise KeyError("choices")   # 模拟 DeepSeek 返回格式变了

    monkeypatch.setattr(summarize, "llm_summary", boom)

    client = TestClient(app_module.app)
    r = client.get("/summary")

    assert r.status_code == 200, f"LLM 崩了也不该 500：{r.text}"
    assert r.json()["summary"]


def test_summary_endpoint_rejects_unrecognized_number(monkeypatch):
    """接口路径也必须校验：评述里出现白名单外的数字 → 500，并说明是哪个数字。

    这条守的是 ISSUES #2：改回 `return generate(nums)` 不接改验，
    或者把 check_numbers 从 generate() 里挪走，这条必须变红。
    """
    def bad(nums):
        return summarize.template_summary(nums) + " 资金集中度约 0.5。"

    monkeypatch.setattr(summarize, "llm_summary", bad)

    client = TestClient(app_module.app)
    r = client.get("/summary")

    assert r.status_code == 500, f"编造的数字必须被拒，实际 {r.status_code}"
    detail = r.json()["detail"]
    assert detail["error"] == "文案校验未通过"
    assert "0.5" in detail["无法溯源"]
    assert detail["缺少字段值"] == []   # 模板部分齐全，只多不少


def test_summary_endpoint_rejects_missing_field_values(monkeypatch):
    """反向漏检：评述里一个数字都没写（值全缺）也必须被拒。"""
    monkeypatch.setattr(summarize, "llm_summary", lambda nums: "今日市场分化明显。")

    client = TestClient(app_module.app)
    r = client.get("/summary")

    assert r.status_code == 500
    detail = r.json()["detail"]
    assert detail["无法溯源"] == []
    assert set(detail["缺少字段值"]) >= {"行数", "上涨", "下跌"} or detail["缺少字段值"], \
        f"必须报出缺失的字段值：{detail}"
