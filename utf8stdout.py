"""保证本进程的 stdout / stderr 一律以 UTF-8 输出。

为什么需要它：
  Windows 中文系统控制台代码页是 936（GBK）。当入口脚本被别的程序
  用管道拉起来（subprocess、CI、任务计划）时，Python 会按代码页输出
  GBK 字节；父进程若用 encoding="utf-8" 解码，就会抛
  UnicodeDecodeError，读输出那一端拿到 None，错误还会推迟到下一行才爆。

  之前靠 PYTHONUTF8=1 / PYTHONIOENCODING=utf-8 这两个环境变量兜住，
  但那是「跑的人碰巧设了」，换台机器、换个终端就挂五条测试。

做法：谁输出谁负责。入口脚本 import 本模块，立刻把编码钉成 UTF-8。
"""

import sys

_UTF8 = ("utf-8", "utf8")


def enable():
    """把 stdout / stderr 重设成 UTF-8；已经是 UTF-8 就不动。返回改了几个流。"""
    changed = 0
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        reconf = getattr(stream, "reconfigure", None)
        if reconf is None:
            continue  # 被重定向成不支持 reconfigure 的对象时跳过
        if (getattr(stream, "encoding", "") or "").lower() in _UTF8:
            continue
        reconf(encoding="utf-8")
        changed += 1
    return changed


enable()
