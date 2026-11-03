from summarize import check_numbers, template_summary

nums = {"行数": 90, "上涨": 7, "下跌": 83, "r": -0.263, "top5_集中度": 30.0}

# 探针 1：5 个相同数字，能不能骗过数量下限
try:
    check_numbers("90 90 90 90 90", nums)
    print("DUPES_EXIT=0    <-- 漏洞存在：重复数字骗过了")
except SystemExit as e:
    print("DUPES_EXIT=", e.code)

# 探针 2：字段对调后，裸子串断言是否还能过

swapped = {"行数": 90, "上涨": 83, "下跌": 7, "r": -0.263, "top5_集中度": 30.0}
text = template_summary(swapped)
print("SWAP_FAILED=", (f"上涨 {7} 个" in text))   # False = 新断言能抓住对调


