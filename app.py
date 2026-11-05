from fastapi import FastAPI
import pandas as pd
from summarize import build_nums, generate, CSV_latest

app = FastAPI()


@app.get("/summary")
def get_summary():
    nums = build_nums(CSV_latest)

    df = pd.read_csv(CSV_latest, encoding="utf-8-sig")
    data_date = df["抓取时间"][0]

    return {
        "date": data_date,
        "nums": nums,
        "summary": generate(nums),
    }
