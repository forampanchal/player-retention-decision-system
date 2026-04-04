import pandas as pd


def calculate_recency(last_played_timestamp):
    if pd.isnull(last_played_timestamp):
        return None
    return (pd.Timestamp.now() - pd.to_datetime(last_played_timestamp)).days


def build_features(df):
    df["recency_days"] = df["last_played"].apply(calculate_recency)

    df["engagement_ratio"] = df["recent_playtime"] / (df["total_playtime"] + 1)

    df["high_value_player"] = df["total_playtime"] > 100

    return df
