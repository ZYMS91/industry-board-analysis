"""金标测试：第三套独立实现（纯标准库）给两条路当裁判。

为什么需要：
  build_nums（函数，返回字典）和 stats.py（独立进程，打印 key=value）互为校验，
  但两者都错了同一处时，谁也发现不了。第三套实现不 import 任何项目模块、
  不用 pandas，只用 csv + math ——一旦它和那两条路都对上，说明公式和口径是同一套；
  一旦对不上，说明有人在某处「改对了一半」。

边界（重要）：
  金标只验「算得对不对」，不验「结论对不对」。
  样本小的时候相关系数会翻符号（实测 12 行 r=+0.332，全量 90 行 r=-0.429），
  所以任何方向性结论都必须用全量数据，不能拿这个样本去说事。
"""
import csv
import math
import sys
from pathlib import Path

from summarize import build_nums
from verify_report import parse_stats

ROOT = Path(__file__).parent.parent

COLS = ["数据源", "板块名称", "涨跌幅", "成交额"]

# 手工数得出来的样本：涨 6 / 跌 5 / 平 1 / 共 12
ROWS = [
    ["测试源", "A", 1.5, 120],
    ["测试源", "B", -0.8, 85],
    ["测试源", "C", 2.3, 200],
    ["测试源", "D", 0.0, 60],
    ["测试源", "E", -1.2, 45],
    ["测试源", "F", 0.6, 150],
    ["测试源", "G", 3.1, 310],
    ["测试源", "H", -2.4, 40],
    ["测试源", "I", 0.9, 95],
    ["测试源", "J", -0.3, 70],
    ["测试源", "K", 1.1, 130],
    ["测试源", "L", -1.7, 55],
]


def _write_sample(tmp_path, rows=ROWS, amount=True):
    p = tmp_path / "sample.csv"
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow(r if amount else r[:3] + [""])
    return p


def _golden(path):
    """第三套实现：纯标准库读 CSV 并算 n / up / down / r，不碰 pandas。

    两个口径要分清（写错这里，金标自己就会给出 n=0）：
      行数/涨跌家数  只看「涨跌幅」能不能解析
      r            要求「涨跌幅」和「成交额」都能解析，两边都要有值
    """
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    head, body = rows[0], rows[1:]
    ip, ia = head.index("涨跌幅"), head.index("成交额")

    pct, pairs = [], []
    for r in body:
        try:
            p = float(r[ip])
        except (ValueError, IndexError):
            continue          # 涨跌幅都读不出来，这一行不算
        pct.append(p)
        try:
            a = float(r[ia])
        except (ValueError, IndexError):
            continue          # 只有成交额缺，行还算，只是进不了 r
        pairs.append((p, a))

    n = len(pct)
    up = sum(1 for x in pct if x > 0)
    down = sum(1 for x in pct if x < 0)

    r = None
    if len(pairs) >= 3:
        xs = [p for p, _ in pairs]
        ys = [a for _, a in pairs]
        m = len(pairs)
        mx, my = sum(xs) / m, sum(ys) / m
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        vx = sum((x - mx) ** 2 for x in xs)
        vy = sum((y - my) ** 2 for y in ys)
        if vx > 0 and vy > 0:
            r = round(cov / math.sqrt(vx * vy), 3)
    return {"行数": n, "上涨": up, "下跌": down, "r": r}


def test_three_paths_agree(tmp_path):
    """金标 / build_nums / stats.py 三方对同一份样本必须给出同一组数。"""
    p = _write_sample(tmp_path)

    g = _golden(p)
    # 先钉住人工数得出来的三个数，防止「金标自己也错」时三方一致地错
    assert g["行数"] == 12
    assert g["上涨"] == 6
    assert g["下跌"] == 5

    a = build_nums(str(p))
    assert a["行数"] == g["行数"]
    assert a["上涨"] == g["上涨"]
    assert a["下跌"] == g["下跌"]
    assert round(float(a["r"]), 3) == g["r"]

    b = parse_stats(p)
    assert int(float(b["n"])) == g["行数"]
    assert int(float(b["up"])) == g["上涨"]
    assert int(float(b["down"])) == g["下跌"]
    assert round(float(b["r"]), 3) == g["r"]


def test_no_amount_all_three_say_none(tmp_path):
    """成交额全空时：三边都必须说「没有 r」，而不是各自编一个 0。"""
    p = _write_sample(tmp_path, amount=False)

    g = _golden(p)
    assert g["r"] is None
    assert g["行数"] == 12

    a = build_nums(str(p))
    assert "r" not in a, "成交额全空时不该出现 r"

    b = parse_stats(p)
    assert b["r"] == "NA", f"stats.py 应该说 NA，实际 {b.get('r')}"


def test_golden_catches_tampered_number(tmp_path):
    """证明这套裁判真的能判错：把一个数改掉，三方必然不再一致。"""
    p = _write_sample(tmp_path)
    g = _golden(p)
    a = build_nums(str(p))
    a["上涨"] = a["上涨"] + 1          # 模拟「有人改了一条路」
    assert a["上涨"] != g["上涨"]
