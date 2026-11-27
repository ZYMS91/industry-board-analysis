"""按数据源把快照分组，算同源相邻两天的涨跌家数差。

独立分析脚本：不被 app.py / stats.py / summarize.py import，
坏了不影响每天 15:35 的采集和 /summary 接口。

两个口径（踩过的坑写在代码里，不靠记性）：
1. 分组键是 CSV 的「数据源」列，不是行数。同花顺 90 行、东财 496 行只是当前现状，
   任一方扩表（比如同花顺上到 300 个板块），按行数分组就会把一个源劈成两组。
2. 同源两天之间的空档分两种，分开标：
     异源   ＝那天有快照，但不是本源抓的（可以换源对照，不是丢数）
     缺快照＝那天任何源都没有（可能是休市，也可能是漏采，要对照交易日历才知道）
"""
import utf8stdout  # noqa: F401  强制本进程 stdout 用 UTF-8
from datetime import date, timedelta
from pathlib import Path
import re

from data_repo import load_csv

DATA = Path(__file__).parent / "data"

FILE_RE = re.compile(r"industry_(\d{8})_(\d{6})\.csv")


def _source(path):
    """读「数据源」列，返回唯一源名。列缺失或一行里混多个源 → 抛错，不猜。"""
    df = load_csv(path)
    if "数据源" not in df.columns:
        raise ValueError(f"{Path(path).name} 缺「数据源」列")
    源s = [str(x).strip() for x in df["数据源"].dropna().unique().tolist()]
    if len(源s) != 1:
        raise ValueError(f"{Path(path).name}「数据源」不唯一：{源s}")
    return 源s[0]


def load_snapshots():
    """返回 {数据源: {日期: (时间, 文件名)}}，同一天多份只留时间最晚的。"""
    files = sorted(DATA.glob("industry_*.csv"))
    groups = {}

    for f in files:
        # 从文件名拿日期和时间：industry_20261106_153501.csv
        m = FILE_RE.match(f.name)
        if not m:
            continue
        日期, 时间 = m.group(1), m.group(2)

        组 = groups.setdefault(_source(f), {})
        # 同一天多份：比时间字符串，留大的
        if 日期 not in 组 or 时间 > 组[日期][0]:
            组[日期] = (时间, f.name)
    return groups


def _count(文件名):
    """读一份快照，返回 (上涨家数, 下跌家数)。涨跌幅==0 的平盘，两边都不算。"""
    df = load_csv(DATA / 文件名)
    return int((df["涨跌幅"] > 0).sum()), int((df["涨跌幅"] < 0).sum())


def _days_between(前, 后):
    """前(不含) 到 后(不含) 之间的每一个日历日，返回 date 列表。"""
    d0 = date(int(前[:4]), int(前[4:6]), int(前[6:]))
    d1 = date(int(后[:4]), int(后[4:6]), int(后[6:]))
    return [d0 + timedelta(days=i) for i in range(1, (d1 - d0).days)]


def _notes(源, 前, 后, groups):
    """同源两日之间被跳过的日子：异源、缺快照，分开列。

    周末不算缺快照（本来不该有快照）；节假日会被误标，所以口径里写明要对日历。
    """
    中间 = _days_between(前, 后)
    别的源 = set()
    for s, 组 in groups.items():
        if s != 源:
            别的源.update(组)
    有快照 = set().union(*groups.values()) if groups else set()

    段 = []
    异源 = [d.strftime("%Y%m%d") for d in 中间 if d.strftime("%Y%m%d") in 别的源]
    缺日 = [d.strftime("%Y%m%d") for d in 中间
            if d.weekday() < 5 and d.strftime("%Y%m%d") not in 有快照]
    if 异源:
        段.append(f"跳过异源 {'/'.join(异源)}")
    if 缺日:
        段.append(f"缺快照 {'/'.join(缺日)}")
    return f"（{'；'.join(段)}）" if 段 else ""


def diffs(groups):
    """同源内相邻两天的涨跌家数差。

    返回 [(源, 前日期, 后日期, Δ上涨, Δ下跌, 说明)]
    """
    结果 = []

    for 源 in sorted(groups):
        组 = groups[源]
        日期列表 = sorted(组)

        for 前, 后 in zip(日期列表, 日期列表[1:]):
            前up, 前down = _count(组[前][1])
            后up, 后down = _count(组[后][1])

            # Δ下跌 不从 -Δ上涨 反推：平盘（涨跌幅==0）两边都不算，
            # 平盘数一变，Δ涨 + Δ跌 就不为 0，两条都得单独算、单独打。
            结果.append((源, 前, 后, 后up - 前up, 后down - 前down, _notes(源, 前, 后, groups)))

    return 结果


def main():
    groups = load_snapshots()

    for 源 in sorted(groups):
        组 = groups[源]
        print(f"{源}：{len(组)} 份")
        for 日期 in sorted(组):
            时间, 文件名 = 组[日期]
            print(f"  {日期[:4]}-{日期[4:6]}-{日期[6:]}  取 {时间}  {文件名}")
        print()

    结果 = diffs(groups)
    print("=== 日环比（同源内）===")
    print("口径：涨跌幅>0 记涨、<0 记跌，平盘两边都不算；Δ下跌不取 -Δ上涨（平盘数会变）")
    print("空档：异源＝那天有别的源的快照；缺快照＝那天是工作日但任何源都没有（周末不算，节假日会误标，要对日历）")
    for 源, 前, 后, du, dd, 说明 in 结果:
        print(f"[{源}] {前} → {后}  Δ上涨 {du:+d}  Δ下跌 {dd:+d}  {说明}")
    print(f"共 {len(结果)} 对")



if __name__ == "__main__":
    main()
