import os
import json
import pandas as pd

RAW_DATA_PATH = "data/raw"


def extract_features(file_path):
    """Extract player features from a raw JSON data file."""
    with open(file_path, "r") as f:
        data = json.load(f)

    result = {}

    # Steam ID
    result["steam_id"] = data.get("steam_id")

    # -------- Player Summary --------
    try:
        player = data["summary"]["response"]["players"][0]
        result["last_logoff"] = player.get("lastlogoff")
        result["personastate"] = player.get("personastate")
    except (KeyError, IndexError, TypeError):
        result["last_logoff"] = None
        result["personastate"] = None

    # -------- Owned Games --------
    try:
        games = data["owned_games"]["response"]["games"]
        result["total_playtime"] = sum(
            g.get("playtime_forever", 0) for g in games)
        result["game_count"] = len(games)
    except (KeyError, TypeError):
        result["total_playtime"] = 0
        result["game_count"] = 0

    # -------- Recent Games --------
    try:
        recent_games = data["recent_games"]["response"]["games"]
        result["recent_playtime"] = sum(
            g.get("playtime_2weeks", 0) for g in recent_games)
    except (KeyError, TypeError):
        result["recent_playtime"] = 0

    return result


def process_all_data():
    """Process all raw JSON files into a single DataFrame."""
    records = []

    for file in os.listdir(RAW_DATA_PATH):
        if file.endswith(".json"):
            file_path = os.path.join(RAW_DATA_PATH, file)
            features = extract_features(file_path)
            records.append(features)

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    df = process_all_data()

    # Remove invalid/private users
    df = df[df["game_count"] > 0]

    # Churn label: player has significant playtime but no recent activity
    df["churn"] = (
        (df["recent_playtime"] == 0) &
        (df["total_playtime"] > 100)
    ).astype(int)

    # Feature Engineering
    # Engagement ratio (recent vs total)
    df["engagement_ratio"] = df["recent_playtime"] / (df["total_playtime"] + 1)

    # High value player (business importance)
    df["high_value_player"] = (df["total_playtime"] > 100).astype(int)

    # Playtime per game
    df["avg_playtime_per_game"] = df["total_playtime"] / (df["game_count"] + 1)

    print(df.head())

    # Save processed dataset
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/player_data.csv", index=False)

    print("Saved processed dataset!")
