# -*- coding: utf-8 -*-
"""
Day 01 —— 把一份真实数据拿到手，先看清它长什么样。
数据源：东方财富「行业板块」实时行情，单次请求约 2 秒，86 行左右。
"""
import akshare as ak

print("正在请求真实数据（行业板块行情），约 2 秒...\n")
df = ak.stock_board_industry_name_em()

line = "=" * 52

print(line)
print("1) 数据规模：", df.shape[0], "行 ×", df.shape[1], "列")
print(line)

print("2) 有哪些字段：")
for i, c in enumerate(df.columns, 1):
    print(f"   {i:2d}. {c}")

print(line)
print("3) 前 5 行长什么样：")
print(df.head().to_string())

print(line)
print("4) 每个字段的类型：")
print(df.dtypes.to_string())

print(line)
print("如果上面中文正常显示、并且有 496 行 × 12 列 —— 你的环境就通了。")
