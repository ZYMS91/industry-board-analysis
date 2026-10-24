import pandas as pd
from analyze import pick
def test_pick_skips_empty_column():
    df=pd.DataFrame({
        "板块名称":["芯片","电气"],
         "总市值":   [None, None],
         "成交额":   ["300", "400"],
    })
    assert pick(df, ["总市值", "成交额"]) == "成交额"
