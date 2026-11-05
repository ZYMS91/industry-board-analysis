# -*- coding: utf-8 -*-
"""证据盘点：每周跑一次，输出「可写进简历的硬数字」和「还缺什么」。

用法（CMD）：
    cd /d D:\\work\\day01
    .venv\\Scripts\\python.exe evidence.py

输出：控制台打印 + 落盘 reports/evidence-YYYYMMDD.md
原则：所有数字都是现场跑出来的，不读缓存、不手填。
"""
from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"


def run(cmd: list[str]) -> tuple[int, str]:
    """跑一条命令，返回 (退出码, 合并输出)。不抛异常，失败也是一种证据。"""
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as exc:  # noqa: BLE001 - 盘点脚本不该因为一条命令挂掉
        return -1, f"[执行失败] {exc}"


def py_files_stat() -> tuple[int, int, int]:
    """返回 (业务代码行数, 测试代码行数, Python 文件数)。空行与纯注释也计入，口径固定。"""
    prod = test = files = 0
    for p in ROOT.rglob("*.py"):
        if ".venv" in p.parts:
            continue
        n = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
        files += 1
        if "tests" in p.parts or p.name.startswith("test_"):
            test += n
        else:
            prod += n
    return prod, test, files


def git_commits() -> tuple[int, int, str, str]:
    """返回 (提交总数, 有提交的天数, 首日, 末日)。"""
    _, total = run(["git", "rev-list", "--count", "HEAD"])
    _, dates = run(["git", "log", "--format=%ad", "--date=short"])
    days = [d for d in dates.splitlines() if d.strip()]
    return (
        int(total) if total.isdigit() else 0,
        len(set(days)),
        days[-1] if days else "?",
        days[0] if days else "?",
    )


def snapshot_stats() -> tuple[int, int]:
    """返回 (15:35 自动采集快照数, CSV 总数)。"""
    csvs = list((ROOT / "data").glob("industry_*.csv"))
    auto = [p for p in csvs if re.search(r"_1535\d\d\.csv$", p.name)]
    return len(auto), len(csvs)


def error_book_rows() -> int:
    f = REPORTS / "错误库.md"
    if not f.exists():
        return 0
    return sum(1 for line in f.read_text(encoding="utf-8").splitlines() if line.startswith("| 2026-"))


def review_count() -> int:
    return len(list(REPORTS.glob("review-*.md")))


def has_api_layer() -> bool:
    # 只认 import 语句，不能搜字符串——否则会把自己的正则字面量当成"有 API"（真踩过）。
    pat = re.compile(r"^\s*(?:from|import)\s+(fastapi|flask|uvicorn)\b", re.I | re.M)
    for p in ROOT.rglob("*.py"):
        if ".venv" in p.parts or p.name == Path(__file__).name:
            continue
        if pat.search(p.read_text(encoding="utf-8", errors="ignore")):
            return True
    return False


def has_real_users() -> bool:
    """真实使用 = 有别人也在用的痕迹：数据库表或使用日志。个人脚本自己跑不算。"""
    return any((ROOT / p).exists() for p in ("data/app.db", "data/usage.log"))


def has_deploy() -> bool:
    return any((ROOT / p).exists() for p in ("Dockerfile", "Procfile", "deploy.sh", "fly.toml"))


def pytest_line() -> tuple[str, int]:
    code, out = run([sys.executable, "-m", "pytest", "-q"])
    tail = out.splitlines()[-1] if out else "[无输出]"
    return tail, code


def prev_evidence() -> dict[str, int]:
    """读上一份 evidence-*.md，抽出几个关键数字，用来做环比。没有上一份就返回空。"""
    today = dt.date.today().isoformat()
    files = sorted(p for p in REPORTS.glob("evidence-*.md") if p.name != f"evidence-{today}.md")
    if not files:
        return {}
    text = files[-1].read_text(encoding="utf-8")
    pats = {
        "commits": r"提交数\s*\|\s*\*\*(\d+)\*\*",
        "tests": r"(\d+)\s+passed",
        "auto": r"自动采集\s*\|\s*\*\*(\d+)\*\*",
        "errors": r"错误库\s*\*\*(\d+)\*\*",
        "reviews": r"复盘文档\s*\*\*(\d+)\*\*",
    }
    out = {}
    for k, p in pats.items():
        m = re.search(p, text)
        if m:
            out[k] = int(m.group(1))
    out["_file"] = files[-1].name  # type: ignore[assignment]
    return out


def delta(cur: int, prev: dict[str, int], key: str) -> str:
    """把环比写成 +N / -N / 持平；没有上一份就是「首次」。"""
    if key not in prev:
        return "首次"
    d = cur - prev[key]
    return "持平" if d == 0 else f"{d:+d}"


def main() -> None:
    today = dt.date.today().isoformat()
    commits, active_days, first, last = git_commits()
    prod, test, files = py_files_stat()
    auto, csv_total = snapshot_stats()
    err_rows, reviews = error_book_rows(), review_count()
    api, users, deploy = has_api_layer(), has_real_users(), has_deploy()
    ptest, _ = pytest_line()
    live_code, live_out = run([sys.executable, "summarize.py"])
    live_last = [ln for ln in live_out.splitlines() if ln.strip()][-1:] or ["[无输出]"]
    prev = prev_evidence()
    tests_n = int(m.group(1)) if (m := re.search(r"(\d+)\s+passed", ptest)) else 0

    gaps = []
    if not api:
        gaps.append("**没有 API 层** —— 脚本 + LLM 调用还不算「AI 应用」，阶段 1 判据①未完成")
    if not users:
        gaps.append("**零真实用户** —— 缺最硬的量化证据（N 人用 / 每天 N 次）")
    if not deploy:
        gaps.append("**没有部署** —— 面试问「别人怎么用」只能答「本地跑」")
    if auto < 20:
        gaps.append(f"**数据天数少**（{auto} 天）—— 别写「大数据」，会被追问")
    if err_rows < 10:
        gaps.append(f"**错误库只有 {err_rows} 条** —— 复盘密度不够")

    lines = [
        f"# 证据盘点 {today}",
        "",
        "全部现场跑出来的数字，无手填。",
        "",
        "## A 档：可写进简历（面试官能核）",
        "",
        "| 项 | 数值 | 怎么验 |",
        "|---|---|---|",
        f"| 提交数 | **{commits}** 次（{first} → {last}，有提交 **{active_days}** 天） | `git log --oneline` |",
        f"| 代码量 | **{prod}** 行业务 + **{test}** 行测试（{files} 个 .py） | `wc -l *.py tests/*.py` |",
        f"| 测试 | `{ptest}` | `pytest -q` |",
        f"| 自动采集 | **{auto}** 天 15:35 快照（CSV 共 {csv_total} 份） | `ls data/` |",
        f"| 实跑 | exit={live_code}，末行：`{live_last[0]}` | `python summarize.py` |",
        "",
        "## 环比（对比上一份证据）",
        "",
    ]
    if prev:
        lines += [
            f"| 指标 | 本期 | 上期 | 变化 |",
            "|---|---|---|---|",
            f"| 提交 | {commits} | {prev.get('commits', '?')} | {delta(commits, prev, 'commits')} |",
            f"| 测试通过数 | {tests_n} | {prev.get('tests', '?')} | {delta(tests_n, prev, 'tests')} |",
            f"| 自动采集天数 | {auto} | {prev.get('auto', '?')} | {delta(auto, prev, 'auto')} |",
            f"| 错误库条数 | {err_rows} | {prev.get('errors', '?')} | {delta(err_rows, prev, 'errors')} |",
            "",
            f"> 上期：`{prev.get('_file', '?')}`",
        ]
    else:
        lines.append("（首次盘点，没有上一期可对比）")

    lines += [
        "",
        "## B 档：面试能讲（别写简历）",
        "",
        f"- 错误库 **{err_rows}** 条（现象 / 根因类别 / 怎么提前发现）",
        f"- 复盘文档 **{reviews}** 份",
        "",
        "## D 档：缺口",
        "",
    ]
    lines += [f"- {g}" for g in gaps] if gaps else ["- ✅ 无缺口"]
    lines += [
        "",
        "## 一句话",
        "",
        f"> 目前能对外说的是「{commits} 次提交、{test} 行测试、{auto} 天自动采集、LLM 数字零编造」；"
        f"还不能说的是「有人在用」。"
        if not users
        else f"> 已具备真实使用证据，可以进入投递阶段。",
        "",
    ]

    text = "\n".join(lines)
    out = REPORTS / f"evidence-{today}.md"
    REPORTS.mkdir(exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"\n[已写入] {out}")


if __name__ == "__main__":
    main()
