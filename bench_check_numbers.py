"""check_numbers 拦截率基准（一次真实实验，不是估算）。

做法：拿今天的真实 nums 生成一段合规摘要，再逐条注入 5 类错误，看 check_numbers 是否拦下。
结果写入 reports/check-numbers-bench.txt。
"""
import io
import sys
import contextlib

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from summarize import check_numbers, template_summary  # noqa: E402

NUMS = {"行数": 496, "上涨": 72, "下跌": 423}
BASE = template_summary(NUMS)

CASES = [
    ("① 改一个数字", BASE.replace("496 个板块", "495 个板块")),
    ("② 多加一个数字", BASE + "，成交额约 12 亿。"),
    ("③ 两个数对调位置", BASE.replace("上涨 72 个，下跌 423 个", "上涨 423 个，下跌 72 个")),
    ("④ 删掉一个字段值", BASE.replace("今日 496 个板块中，", "今日整体中，")),
    ("⑤ 数字改写成中文", BASE.replace("496 个板块", "四百九十六个板块")),
]


def run(text):
    """跑 check_numbers，返回 (是否拦下, 输出)。"""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            check_numbers(text, NUMS)
        return False, buf.getvalue().strip()
    except SystemExit:
        return True, buf.getvalue().strip()


def main():
    lines = [
        "# check_numbers 拦截率基准（真实实验，非估算）",
        "",
        f"基准文本：{BASE}",
        f"白名单 nums：{NUMS}",
        "",
        "| 注入的错 | 拦下 | 输出 |",
        "|---|---|---|",
    ]
    caught = 0
    for name, text in CASES:
        blocked, out = run(text)
        caught += blocked
        lines.append(f"| {name} | {'✅ 拦下' if blocked else '❌ 漏过'} | `{out}` |")
    lines += [
        "",
        f"**结果：5 类错误拦下 {caught}/5。**",
        "",
        "边界（要主动说，别等面试官问）：`check_numbers` 只做**白名单集合比对**——",
        "文案里的每个数字必须在 nums 里、nums 里每个值必须出现一次。",
        "所以它能拦「编造 / 多写 / 漏写」，**拦不住「位置对调」这种数值都在、语义反了的错**。",
    ]
    out_path = __import__("pathlib").Path(__file__).parent / "reports" / "check-numbers-bench.txt"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
