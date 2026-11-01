import re
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
import requests

CSV_latest = Path(__file__).parent / "data" / "latest.csv"
load_dotenv(Path(__file__).parent / ".env")
def build_nums(CSV_latest):
    df=pd.read_csv(CSV_latest,encoding="utf-8-sig")
    n=len(df)
    up=int((df["涨跌幅"]>0).sum())
    down=int((df["涨跌幅"]<0).sum())
    r=df["涨跌幅"].corr(df["成交额"])
    r=round(r,3)
    top5=df.sort_values("成交额",ascending=False).head(5)
    conc=round(top5["成交额"].sum()/df["成交额"].sum()*100,1)
    nums = {"行数": n, "上涨": up, "下跌": down, "r": r, "top5_集中度": conc}
    return nums
# 校验函数：确认文案里的每个数字都能在 nums 里找到出处
def check_numbers(text, nums):
    # 第 1 步：从文案里捞出所有数字（返回字符串列表）
    # r"-?\d+\.?\d*" 拆开：-? 可选负号 / \d+ 至少一位数字 / \.? 可选小数点 / \d* 任意位数字
    found = re.findall(r"-?\d+\.?\d*", text)
    # 第 2 步：把 nums 的所有值转成字符串，装进集合（集合查找比列表快，且自动去重）
    #alloed = {str(v),for v in nums.values()}:
    allowed = set()
    for v in nums.values():
        allowed.add(str(v))

    # 第 3 步：逐个核对
    for x in found:
        if x not in allowed:
            print("不通过：", x, "无法溯源")   # 报出是哪个数字对不上
            raise SystemExit(1)               # 退出码 1，告诉调用方“校验失败”

    # 第 4 步：全部命中
    print(f"校验通过：{len(found)} 个数字全部可溯源")

def template_summary(nums):
    text = f"今日 {nums['行数']} 个板块中，上涨 {nums['上涨']} 个，下跌 {nums['下跌']} 个。涨跌幅与成交额的相关系数 r={nums['r']}，成交额前五板块占全市场 {nums['top5_集中度']}%。"
    return(text)

def llm_summary(nums):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY")
    url = "https://api.deepseek.com/chat/completions"
    prompt = "用一句中文定性描述今天 A 股行业板块的行情，可以说普涨、普跌、分化、资金集中度强弱。不要出现任何数字、百分比、具体板块名。只输出这一句话，不要解释。"

    resp = requests.post(
    url,
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
    timeout=30,
    )
    resp.raise_for_status()
    comment = resp.json()["choices"][0]["message"]["content"].strip()
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
