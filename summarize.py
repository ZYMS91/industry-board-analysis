import pandas as pd
from pathlib import Path
CSV=Path(__file__).parent/"data"/"latest.csv"
df=pd.read_csv(CSV,encoding="utf-8-sig")
n=len(df)
up=(df["涨跌幅"]>0).sum()
down=(df["涨跌幅"]<0).sum()
r=df["涨跌幅"].corr(df["成交额"])
r=round(r,3)
top5=df.sort_values("成交额",ascending=False).head(5)
conc=round(top5["成交额"].sum()/df["成交额"].sum()*100,1)

print("行数:",n)
print("上涨:",up)
print("下跌:",down)
print("r=",r)
print("top5_集中度:",conc)
