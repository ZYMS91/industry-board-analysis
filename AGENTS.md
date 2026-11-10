# AGENTS.md — 给 AI 编码助手的项目说明

> 本文件供 Trae / Cursor / Copilot 等 AI 助手阅读。开始改代码前必须先读完。

## 这是什么项目

A 股行业板块行情分析管线：每日收盘后自动采集 90 个行业板块的涨跌数据，计算 5 个指标，生成中文研报，并通过 HTTP 接口对外提供。

**一句话**：数据采集 → 指标计算 → 报告生成（含 AI 评述）→ HTTP 服务。

## 技术栈

- Python 3.14（虚拟环境 `.venv`，必须用 `.venv\Scripts\python.exe`）
- pandas 3.0.6 / matplotlib 3.11.2
- akshare 1.19.1（数据源：东方财富主源、同花顺备源）
- pytest 9.1.1（12 个测试，全绿）
- FastAPI 0.162.0 + uvicorn 0.54.0
- requests 2.34.2（DeepSeek API 调用）
- python-dotenv 1.2.4

## 目录结构与职责

```
update.py        唯一联网的脚本。抓取 → data/*.csv 快照。失败自动降级备源
data_repo.py     数据访问层。load_csv() 是全项目唯一的 CSV 读取入口，换存储只改这里
check_freshness.py  交易日 15:45 检查数据新鲜度与可用性，写 logs/freshness.log
analyze.py       读本地快照，输出三段分析（不联网）
stats.py         计算分布、相关系数、p 值（不联网）
chart.py         生成 top10.png（不联网）
summarize.py     核心：build_nums（算指标）→ generate（LLM 或模板）→ check_numbers（校验）
utils.py         纯函数（pick：从候选列里挑第一个存在且有值的）
check.py         环境自检
app.py           FastAPI 服务，GET /summary 返回 JSON
evidence.py      每周证据盘点（硬数字 + 缺口）
data/            industry_YYYYMMDD_HHMMSS.csv 快照 + latest.csv（被 gitignore）
reports/         每次快照的结论 + 复盘（私人内容，部分被 gitignore）
tests/           test_pick.py / test_data.py / test_summarize.py / test_api.py
```

## 关键设计（改代码前必须理解）

1. **只有 `update.py` 联网**。其余脚本只读本地 CSV。这样数据源挂了、断网时，分析和报告照样能出。
2. **数字与评述分离**。`build_nums` 算出 5 个数字（行数/上涨/下跌/r/top5_集中度），LLM 只写**不含数字**的定性评述。数字由 f-string 注入，LLM 没有机会编造。
3. **防幻觉校验** `check_numbers(text, nums)`：
   - 用正则从成品文案抽出所有数字
   - 白名单 = `nums` 的所有值
   - 文案里的数字不在白名单 → `SystemExit(1)`
   - 白名单里的值没在文案出现（差集非空）→ `SystemExit(1)`
4. **降级路径** `generate(nums)`：先试 `llm_summary`，抛异常则打印原因并回落 `template_summary`。**任何情况下都要有输出**。
5. **测试隔离**：用 `tmp_path` 造临时文件、`skipif` 跳过无数据场景、`monkeypatch` 屏蔽外部依赖。测试**不许**依赖网络和真实数据。

## 运行方式

```powershell
cd /d D:\work\day01
.venv\Scripts\python.exe update.py          # 抓数据（需要网络）
.venv\Scripts\python.exe analyze.py         # 分析
.venv\Scripts\python.exe summarize.py       # 生成报告 + 校验
.venv\Scripts\python.exe -m pytest -q       # 跑测试，应显示 12 passed
.venv\Scripts\python.exe -m uvicorn app:app --reload   # 起服务
curl.exe http://127.0.0.1:8000/summary      # 验证接口
```

## 硬性约定（违反会破坏项目）

| # | 规则 | 原因 |
|---|---|---|
| 1 | **改代码前先 `git commit`** | 没有回滚点，AI 改坏后无法恢复 |
| 2 | **改完跑 `git diff --stat` 核对行数** | 只改要求的那几行，不要顺手重构 |
| 3 | **测试红了先判断：产品代码错，还是测试用例错** | 判错就会去改不该改的文件 |
| 4 | **反向实验只改产品代码，绝不动测试断言** | 改测试让它红等于自己骗自己 |
| 5 | **断言必须绑定字段名和值**（`f"上涨 {n} 个"`），不许裸子串（`"7" in text`） | 裸子串在字段对调后仍然通过 |
| 6 | **每个新增函数必须配一条测试** | 否则改动无人保护 |
| 7 | 测试文件放 `tests/`，名字 `test_*.py`；临时脚本放根目录且**不以 `test_` 开头** | 避免误收集 |

## 禁区（绝对不要做）

- **不要读、写、打印 `.env`** 的内容。API key 只允许通过 `os.environ.get("DEEPSEEK_API_KEY")` 读取。
- **不要在代码里硬编码任何密钥**。
- **不要修改 `reports/` 下的复盘、错误库、计划文件**（私人内容，部分已 gitignore）。
- **不要修改 `data/` 下的 CSV 内容**（是历史快照，改了结论就不可复现）。
- **不要在 `update.py` 之外引入联网调用**。

## 当前状态（2026-11-05）

- 阶段 0（工程化）：完成。定时采集、测试、README 全部到位。
- 阶段 1（AI 应用层）：**完成**。`/summary` 接口返回 date/nums/summary，降级已测。
- **项目技术冻结中（至 2026-11-20）**：当前优先级是求职材料与投递，不接受新功能。
- 如需加功能，先确认不是"已冻结"范围内的事。

## 常见陷阱（本项目踩过的）

1. `df('列名')` 用圆括号 → `TypeError: not callable`。取列必须用方括号。
2. `os.environ.get("sk-xxx")` 传 key 值 → 取到 None。参数是**变量名**。
3. 第二个 `def` 缩进进第一个函数 → pytest 静默不收集。跑 `--collect-only` 核对条数。
4. 在 `>>>` REPL 里敲 shell 命令 → SyntaxError。
5. CSV 里数字小数点必须用 `.`，逗号是分隔符。
6. `git checkout -- 文件` 会丢弃未提交改动，执行前先 commit。
7. PowerShell 里 `curl` 是 `Invoke-WebRequest` 别名，不打印 body。用 `curl.exe`。
