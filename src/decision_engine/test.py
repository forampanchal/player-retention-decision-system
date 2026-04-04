import pandas as pd
from src.decision_engine.decision_logic import recommend_action

df = pd.read_csv("data/processed/player_data.csv")

df["action"] = df.apply(recommend_action, axis=1)

print(df[["steam_id", "churn", "high_value_player", "action"]].head())
