import json
import os
from datetime import datetime
from src.data_pipeline.steam_api import SteamAPI

OUTPUT_DIR = "data/raw"


class SteamDataCollector:
    def __init__(self):
        self.api = SteamAPI()

    def collect_player_data(self, steam_id):
        print(f"Collecting data for {steam_id}...")

        summary = self.api.get_player_summary([steam_id])
        owned_games = self.api.get_owned_games(steam_id)
        recent_games = self.api.get_recent_games(steam_id)

        data = {
            "steam_id": steam_id,
            "collected_at": str(datetime.utcnow()),
            "summary": summary,
            "owned_games": owned_games,
            "recent_games": recent_games
        }

        filename = f"{steam_id}.json"
        self.save_json(data, filename)

        print(f"Saved {filename}")
        return data

    def save_json(self, data, filename):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def get_friend_ids(self, steam_id):
        data = self.api.get_friends(steam_id)

        try:
            friends = data["friendslist"]["friends"]
            return [f["steamid"] for f in friends]
        except:
            return []
