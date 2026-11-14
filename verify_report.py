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
    #
    # 必选字段两边都必须有值，简单。可选字段不行：
    # 东财源没有「成交额」这一列，两条路都可能拿不出 r。
    # 所以这里不是「比数值」，而是先判断「谁有值、谁没值」，再决定要不要比。
    #
    for k_stat, k_num in OPTIONAL.items():
        # ── 第一步：把两边的状态各压成一个布尔值 ──
        #
        # 左边 = stats.py 的输出（字典 stats）
        # 「没有值」有两种写法，对下游来说完全一样，所以合成一个：
        #   (a) 键不存在        → 字典里压根没有 "r"
        #   (b) 键在，值是 "NA" → 打印了 r=NA，表示算不出来
        左有键 = k_stat in stats                          # stats 里有 "r" 这个键吗
        左为空 = 左有键 and str(stats[k_stat]) == "NA"     # 有键，但值是字符串 "NA" 吗
        左没值 = (not 左有键) or 左为空                    # 上面两种情况 (a)(b) 都算「没有值」
        # 右边 = build_nums 的返回值（字典 nums）
        # 注意多查一次 is not None：键在但值是 None，对下游也等于没有
        右有值 = k_num in nums and nums[k_num] is not None

        # ── 第二步：四选一 ──
        #  左没值  右有值     意思                     动作
        #  ───────────────────────────────────────────────────────
        #  True    False    都说没有（正常）           放过
        #  True    True     一个有一个没有（矛盾）      报错
        #  False   False    一个有一个没有（矛盾）      报错
        #  False   True     两边都有                    比数

        # ① 都说没有 → 一致。
        # 场景：东财源无成交额，stats.py 打 r=NA，build_nums 也没 r。
        # 两个人都说「我没有」，不是错误，跳过。
        if 左没值 and not 右有值:
            continue

        # ② 左边说没有，右边却有 → nums 多算了。
        # 场景：同样一份数据，stats.py 算不出 r，build_nums 却算出了 -0.28。
        # 说明两条路读到的数据不同，或判断条件不同 —— 必须查。
        #
        # 为什么不写成 elif：后面每个分支都 continue，效果等同于 elif，
        # 但平铺更好读，加分支时不用改缩进。
        #
        # stats.get(k_stat, '缺键')：这里左边正可能是「键不存在」，
        # 用 stats[k_stat] 会 KeyError，.get() 给个默认值就不会崩。
        if 左没值 and 右有值:
            msgs.append(
                f"不一致：build_nums 有 {k_num}={nums[k_num]}，"
                f"stats.py 却是 {stats.get(k_stat, '缺键')}"
            )
            失败 += 1
            continue   # ← 必须跳出，否则会掉到 ③ 去 float("NA") 崩掉

        # ④ 左边有值，右边却没有 → nums 漏算了。
        # 场景：stats.py 算出 r=-0.2836，build_nums 的字典里根本没 r。
        # 和 ② 方向相反：② 是多算，④ 是漏算，排查时指向不同的 bug。
        if (not 左没值) and (not 右有值):
            msgs.append(
                f"不一致：stats.py 有 {k_stat}={stats[k_stat]}，"
                f"build_nums 却没有 {k_num}"
            )
            失败 += 1
            continue

        # ③ 两边都有数字 —— 到这里才轮到比数值。
        #
        # 为什么先 round 到 3 位再比：
        #   stats.py   输出 -0.2836（原始值，格式化 4 位）
        #   build_nums 里写的是 round(..., 3) → -0.284
        # 直接比 -0.2836 != -0.284 会天天误报。
        # 这是「精度口径不同」，不是算错 —— 对齐口径比放宽容差安全：
        # 容差 0.001 会掩盖 0.0009 的真错误，对齐 3 位只放过舍入差。
        a = round(float(stats[k_stat]), 3)
        b = round(float(nums[k_num]), 3)
        # 用 1e-9 而不是 ==：浮点数 round 后仍可能有极小的表示误差
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
