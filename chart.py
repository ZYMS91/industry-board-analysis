# -*- coding: utf-8 -*-
r"""
Day 01 出图：行业板块涨跌幅 Top 10。

运行：
    D:
    cd \work\day01
    .venv\Scripts\python.exe chart.py

跑完会生成 top10.png，用图片查看器打开看效果。
"""
import matplotlib
matplotlib.use("Agg")            # 不弹窗口，直接存文件
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# ===== 中文字体配置（不给这三行，中文会变成方块）=====
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False   # 让负号正常显示，不然也是方块

# ===== 管道活：取数据 =====
csv_path = Path(__file__).parent / "data" / "latest.csv"
df = pd.read_csv(csv_path, encoding="utf-8-sig")
print("数据来源:", df["数据源"][0], "| 抓取时间:", df["抓取时间"][0])


# TODO: 取涨幅最高的 10 个行业，只需要 "板块名称" 和 "涨跌幅" 两列。
#       和问题 1 一模一样的套路，只把 5 换成 10。
#       结果必须存进名叫 top10 的变量（否则下面会报 NameError）。
top10 = df.sort_values('涨跌幅',ascending=False)[['板块名称','涨跌幅']].head(10)
print(top10)

# ===== 以下是画图部分，先不用改 =====
fig, ax = plt.subplots(figsize=(9, 6))
colors=["#c03926"if v>=0 else "#27ae60" for v in top10["涨跌幅"]]
ax.barh(top10["板块名称"], top10["涨跌幅"], color=colors)
ax.invert_yaxis()                              # 让第一名在最上面
ax.set_xlabel("涨跌幅 (%)")
ax.set_title("行业板块涨跌幅 Top 10")
ax.grid(axis="x", alpha=0.3)

for y,v in enumerate(top10["涨跌幅"]):
    offset = 0.15 if v>=0 else -0.15
    ax.text(v+offset,y,f"{v:.2f}%",va="center",
            ha="left" if v >=0 else "right",fontsize=9)


plt.tight_layout()
plt.savefig("top10.png", dpi=150)
print("已保存 top10.png")
