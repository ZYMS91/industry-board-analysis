"""钉住：入口脚本的 stdout 必须是 UTF-8，不依赖外部环境变量。

背景（2026-11-26 真事）：在 PowerShell（代码页 936）里跑 pytest，
5 条测试挂 UnicodeDecodeError，全是子进程输出 GBK、父进程按 utf-8 解。
之前在助手终端里全绿，是因为那边带着 PYTHONUTF8=1。
所以这里的每个用例都**主动清掉** UTF-8 相关环境变量，模拟干净环境。
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_CLEAR = ("PYTHONUTF8", "PYTHONIOENCODING", "PYTHONLEGACYWINDOWSSTDIO")


def _clean_env():
    env = dict(os.environ)
    for k in _CLEAR:
        env.pop(k, None)
    return env


def test_utf8stdout在干净环境下仍输出UTF8():
    r = subprocess.run(
        [sys.executable, "-c", "import utf8stdout; print('中文测试')"],
        cwd=ROOT, capture_output=True, encoding="utf-8", env=_clean_env(), timeout=60,
    )
    assert r.returncode == 0, r.stderr
    assert "中文测试" in r.stdout


def test_stats在干净环境下可被utf8解析():
    r = subprocess.run(
        [sys.executable, "stats.py", "data/latest.csv"],
        cwd=ROOT, capture_output=True, encoding="utf-8", env=_clean_env(), timeout=180,
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip(), "stats.py 没有输出任何内容"


def test_enable是幂等的():
    import utf8stdout
    utf8stdout.enable()
    first = utf8stdout.enable()          # 已经是 utf-8 了，第二次不该再改
    assert first == 0
