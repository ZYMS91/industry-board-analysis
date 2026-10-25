import pandas as pd
from utils import pick
def test_pick_skips_empty_column():
    df=pd.DataFrame({
        "板块名称":["芯片","电气"],
         "总市值":   [None, None],
         "成交额":   ["300", "400"],
    })
    assert pick(df, ["总市值", "成交额"]) == "成交额"

def test_pick_missing_columns():
    df=pd.DataFrame({
        "板块名称":["芯片","电气"],
        "涨跌幅":   [1.5, -0.8],
    })
    assert pick(df,["总市值","换手率"])is None

def test_pick_all_empty_columns():
        df=pd.DataFrame({
            "总市值": [None, None],
            "换手率": [None, None],
        })
        assert pick(df,["总市值", "换手率"])is None
