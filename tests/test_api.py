from fastapi.testclient import TestClient
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import pytest

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
    assert set(d["nums"]) == {"行数", "上涨", "下跌", "r", "top5_集中度"}
    assert "测试评述" in d["summary"]


def test_summary_falls_back_without_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    from app import app
    client = TestClient(app)
    r = client.get("/summary")

    assert r.status_code == 200               # 关键：不是 500
    d = r.json()
    assert "今日" in d["summary"]              # 降级时有模板文案
    assert "LLM" not in d["summary"]           # 不该把错误信息塞进报告
