import re
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
import requests
from data_repo import load_csv

CSV_latest = Path(__file__).parent / "data" / "latest.csv"
load_dotenv(Path(__file__).parent / ".env")
def build_nums(CSV_latest):
    df = load_csv(CSV_latest)

    # 涨跌幅是必需字段，没有它什么都算不了
    if df["涨跌幅"].notna().sum() == 0:
        raise ValueError("涨跌幅列全为空，本份快照无法使用")

    n = len(df)
    up = int((df["涨跌幅"] > 0).sum())
    down = int((df["涨跌幅"] < 0).sum())
    nums = {"行数": n, "上涨": up, "下跌": down}

    # 成交额是可选的：东财源没有这个字段，此时字典里就不放 r 和集中度
    if "成交额" in df.columns and df["成交额"].notna().any():
        r = round(df["涨跌幅"].corr(df["成交额"]), 3)
        top5 = df.sort_values("成交额", ascending=False).head(5)
        conc = round(top5["成交额"].sum() / df["成交额"].sum() * 100, 1)
        nums["r"] = r
        nums["top5_集中度"] = conc

    return nums

# 校验函数：确认文案里的每个数字都能在 nums 里找到出处
def check_numbers(text, nums):
    found = re.findall(r"-?\d+\.?\d*", text)

    allowed = set()
    for v in nums.values():
        allowed.add(str(v))

    # 逐个核对：文案里的每个数字都必须在白名单里
    for x in found:
        if x not in allowed:
            print("不通过：", x, "无法溯源")
            raise SystemExit(1)

    # 覆盖检查：白名单里的每个值都必须在文案里出现
    missing = allowed - set(found)
    if missing:
        print("不通过：文案缺少这些字段值", missing)
        raise SystemExit(1)
    print(f"校验通过：{len(found)} 个数字全部可溯源")

def market_mood(nums):
    total = nums["上涨"] + nums["下跌"]
    if total == 0:
        return "震荡"
    ratio = nums["上涨"] / total
    if ratio >= 0.7:
        return "普涨"
    if ratio <= 0.3:
        return "普跌"
    return "分化"

def template_summary(nums):
    text = f"今日 {nums['行数']} 个板块中，上涨 {nums['上涨']} 个，下跌 {nums['下跌']} 个。"

    if "r" in nums:
        text += f"涨跌幅与成交额的相关系数 r={nums['r']}，成交额前五板块占全市场 {nums['top5_集中度']}%。"
    else:
        text += "（本数据源不含成交额字段，相关性与集中度指标不可用。）"

    return text


def llm_summary(nums):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY")
    url = "https://api.deepseek.com/chat/completions"
    mood = market_mood(nums)
    prompt = (
        f"今天 A 股行业板块整体呈现{mood}格局。"
        "请用一句中文描述这个行情特征，重点说资金是集中在头部还是分散。"
        "不要出现任何数字、百分比、具体板块名。只输出一句话。"
    )

    resp = requests.post(
    url,
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
    timeout=30,
    )
    resp.raise_for_status()
    comment = resp.json()["choices"][0]["message"]["content"].strip()

    # 评述里出现任何数字 → 模型没遵守约束，丢弃整句评述（局部降级，不影响数字部分）
    if re.search(r"\d", comment):
        raise RuntimeError("LLM 评述含数字，已丢弃")

    return template_summary(nums) + " " + comment
def generate(nums):
    try:
        return llm_summary(nums)
    except Exception as e:
        print(f"LLM 不可用（{e}），已降级为模板文案")
        return template_summary(nums)

if __name__ == "__main__":
    nums = build_nums(CSV_latest)
    # 用算出来的数字拼一段中文文案（f-string 里的 {n} 会被替换成实际数值）
    text = generate(nums)
    print(text)
    check_numbers(text, nums)  # 再校验

