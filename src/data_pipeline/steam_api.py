import os
import requests
from dotenv import load_dotenv

load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

BASE_URL = "https://api.steampowered.com"

# Timeout for all API requests (seconds)
REQUEST_TIMEOUT = 15


class SteamAPI:
    def __init__(self, api_key=STEAM_API_KEY):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("STEAM_API_KEY not found. Set it in your .env file.")

    def _get(self, url, params):
        """Make a GET request with timeout and error handling."""
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_player_summary(self, steam_ids):
        url = f"{BASE_URL}/ISteamUser/GetPlayerSummaries/v2/"
        params = {
            "key": self.api_key,
            "steamids": ",".join(steam_ids) if isinstance(steam_ids, list) else steam_ids
        }
        return self._get(url, params)

    def get_owned_games(self, steam_id):
        url = f"{BASE_URL}/IPlayerService/GetOwnedGames/v1/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "include_played_free_games": True
        }
        return self._get(url, params)

    def get_recent_games(self, steam_id):
        url = f"{BASE_URL}/IPlayerService/GetRecentlyPlayedGames/v1/"
        params = {
            "key": self.api_key,
            "steamid": steam_id
        }
        return self._get(url, params)

    def get_friends(self, steam_id):
        url = f"{BASE_URL}/ISteamUser/GetFriendList/v1/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "relationship": "friend"
        }
        return self._get(url, params)
