# 验收记录 #1 — 陌生人 10 分钟跑通

- **验收时间**：2026-11-26 18:11:29 – 18:12:25（**56 秒**完成全链路）
- **验收人**：甲方视角（AI，按 README 逐条执行）
- **环境**：干净目录 `H:\hermes\cache\scratch\stranger_1126\repo`，`git clone` 本地仓库，Python 3.14.5
- **结论**：❌ **退回**（差一段「怎么装」；不是代码问题，是 README 问题）

## 实测时间线

| 时刻 | 步骤 | 结果 |
|---|---|---|
| 18:11:29 | `git clone` | ✅ 60 个文件，1 秒 |
| 18:11:30 | 照 README「如何复现」第一条：`python update.py` | ❌ **`ModuleNotFoundError: No module named 'pandas'`** |
| 18:11:33 | （甲方自行补）`python -m venv .venv` | ✅ |
| 18:11:33 | （甲方自行补）`.venv\Scripts\python.exe -m pip install -r requirements.txt` | ✅ 全部装上 |
| 18:12:12 | `update.py` | ✅ 7.3 秒，东财 496 行，快照 `industry_20261126_181212.csv` |
| 18:12:19 | `analyze.py` | ✅ 三段分析正常，流动性字段自动选「换手率」 |
| 18:12:19 | `chart.py` | ✅ 生成 `top10.png` |
| 18:12:20 | `stats.py data/latest.csv` | ✅ `n=496 up=353 down=142 flat=1 r=NA`（成交额全空，如实 NA） |
| 18:12:25 | `summarize.py` | ✅ **降级成模板**：`今日 496 个板块中，上涨 353 个，下跌 142 个。` + `校验通过：3 个数字全部可溯源` |
| 18:12:25 | `pytest -q` | ✅ **43 passed** |

## 卡点与问题（按严重度）

### P0-1 README 没有安装步骤

- 现象：`H:\...\repo\update.py:20: ModuleNotFoundError: No module named 'pandas'`
- 根因：「如何复现」直接从 `python update.py` 开始，缺 `python -m venv .venv` + `.venv\Scripts\python.exe -m pip install -r requirements.txt` 两条
- 影响：**陌生人第一条命令就失败**，且不知道缺的是什么依赖
- 建议改法（3 行）：

```markdown
## 如何复现

# 1) 一次性环境（Python 3.14+）
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2) 之后每条都这样调（不是裸 python）
.venv\Scripts\python.exe update.py
.venv\Scripts\python.exe analyze.py
.venv\Scripts\python.exe chart.py
.venv\Scripts\python.exe stats.py data/latest.csv
.venv\Scripts\python.exe summarize.py     # 没配 key 会降级成模板，能跑
```

### P1-1 复现段与「环境」段口径冲突

「如何复现」全用裸 `python`，「环境」段却写「调用方式：`.venv\Scripts\python.exe update.py`」。陌生人照复现段敲命令，命中的是系统 Python（无 pandas）。

### P1-2 没写「没有 API key 也能跑」

`summarize.py` 实测会降级成模板并照样过校验。README 未声明这点，陌生人容易以为必须先申请 DeepSeek key 才能出日报。

### P1-3 测试数字过期

README 写 **41 个**，实测 **43 passed**（本轮新增 `test_写死的测试会被拦下`）。讲稿 `reports/talk2.md` 里 4 处也是 41。

### P1-4 仓库不含数据

`data/` 里 0 个文件被跟踪 → 陌生人必须联网跑 `update.py` 才有数据。当前离线不可复现，README 未在显眼处声明。

## 附：验收人自己补的两步（说明 README 不足）

1. `python -m venv .venv` —— README 有「环境」段，但没有可执行命令
2. `pip install -r requirements.txt` —— 连 `requirements.txt` 的存在都没提

**按 ISSUES.md 的规矩：「只读 README」做不到，本 issue 退回。**
