from fastapi.testclient import TestClient
import pytest
from pathlib import Path
import app as app_module
import summarize


CSV = Path(__file__).parent.parent / "data" / "latest.csv"

# 没有快照文件时跳过（克隆仓库后 data/ 里没有 CSV）
pytestmark = pytest.mark.skipif(not CSV.exists(), reason="没有快照文件，跳过接口测试")



def test_summary_endpoint_ok(monkeypatch):
    # 用假函数替换 LLM 调用：测试不花 API 钱、不依赖网络
    monkeypatch.setattr("summarize.llm_summary", lambda nums: "测试评述")

    from app import app
    client = TestClient(app)
    r = client.get("/summary")

    assert r.status_code == 200
    d = r.json()
    assert d["date"]
    assert {"行数", "上涨", "下跌"} <= set(d["nums"])
    assert "测试评述" in d["summary"]


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
