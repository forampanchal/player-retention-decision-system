from src.data_pipeline.steam_api import SteamAPI

api = SteamAPI()

data = api.get_player_summary(["76561197960434622"])

print(data)
