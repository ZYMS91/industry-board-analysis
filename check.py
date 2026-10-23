# -*- coding: utf-8 -*-
r"""
代码体检：揪出会让你报语法错误的中文全角标点。

用法（在 D:\work\day01 下）：
    .venv\Scripts\python.exe check.py analyze.py

不给文件名时默认检查 analyze.py。
"""
import re
import sys

# 全角/中文标点 → 应该用的英文半角
FULL = {
    "（": "(", "）": ")", "，": ",", "：": ":", "；": ";",
    "［": "[", "］": "]", "｛": "{", "｝": "}",
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "！": "!", "？": "?", "。": ".", "　": "<全角空格>",
}

STR_LIT = re.compile(r'"[^"]*"|\'[^\']*\'')


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "analyze.py"
    try:
        lines = open(path, encoding="utf-8-sig").read().splitlines()
    except FileNotFoundError:
        print(f"找不到文件：{path}")
        return

    bad_lines = 0
    in_doc = False
    for no, line in enumerate(lines, 1):
        stripped = line.strip()
        if line.count('"""') % 2 == 1:    # 进入/离开三引号说明块
            in_doc = not in_doc
            continue
        if in_doc:
            continue
        if stripped.startswith("#") or not stripped:
            continue                      # 纯注释和空行不用查
        code = line.split("  #")[0]       # 去掉行尾注释
        code = STR_LIT.sub('""', code)    # 去掉字符串内容，避免误报
        hits = sorted({c for c in code if c in FULL})
        if not hits:
            continue
        bad_lines += 1
        print(f"第 {no} 行有问题：")
        print(f"    {line}")
        for c in hits:
            print(f"    '{c}' 是全角，应改成半角 '{FULL[c]}'")
        print()

    print("-" * 46)
    if bad_lines:
        print(f"共 {bad_lines} 行有全角标点，改完再运行脚本。")
    else:
        print("没有发现全角标点，可以运行了。")


if __name__ == "__main__":
    main()
