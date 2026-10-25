def pick(df, candidates):
    """从候选字段名里，挑出第一个「存在且有值」的。都没有就返回 None。

    为什么需要这个：不同数据源字段不一样。东财有总市值/换手率，
    同花顺没有。如果直接 df['换手率']，拿到的是全空列，
    算出来的结果看着正常、其实是错的 —— 这种静默错误最危险。
    """
    for col in candidates:
        if col in df.columns and df[col].notna().any():
            return col
    return None
