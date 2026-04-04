from src.data_pipeline.collector import SteamDataCollector

collector = SteamDataCollector()

steam_ids = [
    "76561197960434622",
    "76561198000000000",
    "76561198000000001",
    "76561198000000002"
]

for sid in steam_ids:
    collector.collect_player_data(sid)
