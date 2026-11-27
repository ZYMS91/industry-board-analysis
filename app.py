from fastapi import FastAPI, HTTPException
import pandas as pd
from summarize import build_nums, generate, CSV_latest, NumberMismatch
from data_repo import load_csv

app = FastAPI()


@app.get("/summary")
def get_summary():
    nums = build_nums(CSV_latest)

    df = load_csv(CSV_latest)
    data_date = df["抓取时间"][0]

    # 文案校验在 generate() 里（唯一入口），失败会抛 NumberMismatch。
    # 必须显式捕获：它是 SystemExit 子类，FastAPI 不处理，不接住会把整个 worker 带走。
    try:
        summary = generate(nums)
    except NumberMismatch as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "文案校验未通过",
                "无法溯源": e.offenders,      # 文案里出现、但白名单没有的数字
                "缺少字段值": e.missing,      # 白名单有、但文案没写出来的值
                "message": str(e),
            },
        )

    return {
        "date": data_date,
        "nums": nums,
        "summary": summary,
    }
