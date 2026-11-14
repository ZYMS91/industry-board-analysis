"""校验 summarize 的摘要数字与 stats.py 的独立计算是否一致。

为什么需要这个文件：
  build_nums()  在 summarize.py 里，用 pandas 算一遍
  stats.py      独立脚本，也用 pandas 算一遍
两条独立路径算同一组数——如果同一处算错，各自都不知道；
只有互相比对，才能发现「两边算得不一样」。

判据（阶段 1 ②）：摘要里每个数字都能在 stats.py 输出里找到出处。
"""
import re
import subprocess
import sys
from pathlib import Path

from summarize import build_nums, CSV_latest

ROOT = Path(__file__).parent
CSV = ROOT / "data" / "latest.csv"

# 左边是 stats.py 的输出键，右边是 build_nums() 的字典键
REQUIRED = {"n": "行数", "up": "上涨", "down": "下跌"}
OPTIONAL = {"r": "r"}


def parse_stats(csv_path):
    """跑 stats.py 子进程，把输出里前几行的 key=value 解析成字典。

    只取前 3 行（FILE / n=... / r=...），避免把正文里
    「成交额 Top5 合计 0.00」这类干扰数字也算进来。
    """
    out = subprocess.run(
        [sys.executable, "stats.py", str(csv_path)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=180,
    )
    if out.returncode != 0:
        raise SystemExit(f"stats.py 执行失败（退出码 {out.returncode}）：\n{out.stderr}")

    head = "\n".join(out.stdout.splitlines()[:3])
    # (\w+) 捕获键，(-?[\d.]+|NA) 捕获值，两个组 → dict() 能直接吃
    return dict(re.findall(r"(\w+)=(-?[\d.]+|NA)", head))


def compare(stats, nums):
    """比对两组数。返回 (失败数, 消息列表)。

    纯函数：不读文件、不打印、不退出——所以能直接喂假数据做测试。
    """
    失败 = 0
    msgs = []

    # ---------- 必选字段：两边都必须有，且数值相等 ----------
    for k_stat, k_num in REQUIRED.items():
        if k_stat not in stats:
            msgs.append(f"不通过：stats.py 缺少 {k_stat}")
            失败 += 1
            continue
        if k_num not in nums:
            msgs.append(f"不通过：build_nums 缺少 {k_num}")
            失败 += 1
            continue

        a = int(stats[k_stat])   # findall 抓到的是字符串，必须转 int
        b = int(nums[k_num])     # build_nums 里是 int，测试可能喂字符串
        if a != b:
            msgs.append(f"不一致：{k_num}  stats={a}  build_nums={b}")
            失败 += 1

    # ---------- 可选字段：成交额缺失时 r 可能算不出来 ----------
    for k_stat, k_num in OPTIONAL.items():
        左有键 = k_stat in stats
        左为空 = 左有键 and str(stats[k_stat]) == "NA"
        左没值 = (not 左有键) or 左为空      # 「键不存在」和「值是 NA」都是没有值
        右有值 = k_num in nums and nums[k_num] is not None

        # ① 都说没有 → 一致
        if 左没值 and not 右有值:
            continue

        # ② 右边有值，左边说没有 → nums 多算了
        if 左没值 and 右有值:
            msgs.append(
                f"不一致：build_nums 有 {k_num}={nums[k_num]}，"
                f"stats.py 却是 {stats.get(k_stat, '缺键')}"
            )
            失败 += 1
            continue

        # ④ 左边有值，右边没有 → nums 漏算了
        if (not 左没值) and (not 右有值):
            msgs.append(
                f"不一致：stats.py 有 {k_stat}={stats[k_stat]}，"
                f"build_nums 却没有 {k_num}"
            )
            失败 += 1
            continue

        # ③ 两边都有值 → 比数
        # build_nums 用 round(..., 3)，所以按 3 位对齐再比；
        # 直接比原始值会把「-0.2836 vs -0.284」误判成不一致。
        a = round(float(stats[k_stat]), 3)
        b = round(float(nums[k_num]), 3)
        if abs(a - b) > 1e-9:
            msgs.append(f"不一致：{k_num}  stats={stats[k_stat]}  build_nums={nums[k_num]}")
            失败 += 1

    return 失败, msgs


def main():
    stats = parse_stats(CSV)
    nums = build_nums(CSV_latest)

    print(f"stats.py   : {stats}")
    print(f"build_nums : {nums}")
    print()

    失败, msgs = compare(stats, nums)
    for m in msgs:
        print(m)

    if 失败:
        print(f"\n校验失败：{失败} 处不一致")
        return 1
    print("校验通过：必选字段与可选字段全部一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
