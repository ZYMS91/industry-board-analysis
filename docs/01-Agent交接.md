# 01 · 给其他 Agent 的交接（2026-11-19 10:35，hermes 实测）

> 用途：其他 agent 不要再引用我的口述，直接看这份 + 下面列的文件。
> 标注规则：**[实测]** = 我本次跑命令看到的输出；**[自述]** = 学习者自己说的；**[未验证]** = 没有证据。

---

## 1. 路径与启动（学习者终端是 CMD，不是 bash）

```
项目根：D:\work\day01
虚拟环境：D:\work\day01\.venv\Scripts\python.exe
```

常用命令（CMD 语法，逐行敲）：

```cmd
cd /d D:\work\day01
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe summarize.py
.venv\Scripts\python.exe stats.py
```

接口（需先起服务）：

```cmd
.venv\Scripts\python.exe -m uvicorn app:app --port 8000
curl -s http://127.0.0.1:8000/summary -o reports\api-test.json
```

---

## 2. 模块表（[实测] 行数，2026-11-19 10:30）

| 文件 | 行数 | 职责（一句话） |
|---|---|---|
| `update.py` | 117 | 采集入口：`from_eastmoney()` 主源，`from_ths()` 备用，`main()` 落盘快照 |
| `data_repo.py` | 14 | **唯一 CSV 读取入口**（`load_csv` / `load_latest`） |
| `stats.py` | 60 | 指标计算：n / up / down / range / r / R² / p（`t_p` 用 lgamma 防溢出）/ Top5 集中度 |
| `analyze.py` | 67 | 分析输出 |
| `trend.py` | 134 | 时序（新增，11-19 前） |
| `summarize.py` | 115 | `build_nums`（数字从数据算）→ `llm_summary` / `template_summary`（降级）→ `check_numbers`（数字溯源校验）→ `generate` |
| `app.py` | 20 | FastAPI `/summary`，返回 date / nums / summary |
| `check_freshness.py` | 59 | 数据体检：STALE / BAD / FAIL + 退出码 |
| `evidence.py` | 223 | 硬数字盘点（提交数、快照数、错误库行数、是否有接口层/真实用户） |
| `verify_report.py` | 169 | 报告数字复核（新增） |
| `bench_check_numbers.py` | 65 | check_numbers 的拦截率基准（5 类错数字） |
| `check.py` / `utils.py` / `fetch.py` / `chart.py` | 63 / 11 / 30 / 52 | 全角标点检查 / 工具 / 旧抓取 / 出图 |
| `tests/` | 42 个 test 函数 | pytest，其中 `test_stats / test_summarize / test_trend / test_verify` |

数据：`data/industry_YYYYMMDD_HHMMSS.csv` 快照 **21 个**（含 `latest.csv`，最新 `industry_20261118_153502.csv`）[实测]
自动采集：Windows 计划任务 15:35（11-12 机器关机缺过一天）

---

## 3. 数字口径（已核对，不要再怀疑「51 vs 42」）

| 数字 | 构成 | 状态 |
|---|---|---|
| **1766 行** | day01 非测试 1217 行 + 送货系统 `shipment-tracker` 549 行 = 1766 | [实测] **完全对上** |
| **51 条用例** | day01 42 条 + 送货系统 9 条 = 51 | [实测] **完全对上** |
| 42 passed | 只跑 day01 的 pytest | [实测] 2026-11-19 10:05 |
| 849 行 / 21 passed | 11-13 的旧口径（当时只有 day01 早期文件） | 已作废 |
| 908 行 / 27 条 / 673 行 | 简历第一版，来源不可考 | **已删，别再引用** |

---

## 4. 判据现状

| 阶段 | 状态 |
|---|---|
| 0 工程化 | ✅ 4/4 |
| 1 AI 应用层 | ①✅ 接口通；②✅ `api-20261117.json` 实测 200；③✅ 无 key 降级不 500 |
| 2 面试包装 | ①⚠️ 半过：录音 3:14（ffprobe 实测 193.74s），但缺「4/5 拦截率」量化句，且录音里说「16 模块 / 38 条」，实测 **17 模块 / 42 条**；②✅ 简历单页 PDF（`D:\work\resume\李泽庆-AI应用实施-13827299892.pdf`）+ 追问库 14 题；③❌ 技能上架未做 |

投递：11-18 两家（安菲翁 已沟通未回；1 家待补），11-19 待发 2 家（嘉为/华为项目外包、禅游科技）。本周目标 3 家。
累计真实投递：**4 家**（11-05 一家、11-11 三家）+ 11-18 两家 = **6 家，0 回复**[自述+记录]。

---

## 5. 学习者的真实水平（三堆分类——**必须他自己划，以下是我不该替他答的部分**）

| 来源 | 证据 | 等级 |
|---|---|---|
| 能独立改单点（修 `stats.py` 溢出、补 3 条测试、写 `check_freshness` 纯函数） | 11-12 的 commit 与 21→42 passed | [实测] |
| 讲不出「CSV 换 SQLite 怎么改」 | 11-07 自述 | [自述] |
| 能念稿 3 分钟，但缺量化句 | 11-18 录音 | [实测] |
| 看得懂哪一层、看不懂哪一层 | **未知** | **[未验证]** ← 这是他本人要划的三堆 |

---

## 6. 已知缺口（写进 AGENTS.md 的）

- 同源自证：接口路径的文案未接 `check_numbers`（`app.py:19` 证据）
- `check_numbers` 已知边界：位置对调会漏过（39 条测试时发现）
- 送货系统：无权限 / 无限流 / 无重试 / 无日志
- 三条度量（单均核对耗时、拦错次数、断号命中数）均未记录
- 送货系统 `D:\work1` **不是 git 仓库**；`shipment-tracker` 是旧副本，判据 `delivery_note` 表指向已废弃副本
