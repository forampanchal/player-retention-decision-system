from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        print("\n--- HEALTH CHECK ---")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

def test_predict():
    payload = {
      "steam_id": "76561198XXXXXXX",
      "playtime_forever": 120000,
      "playtime_2weeks": 0,
      "last_logoff": 1700000000,
      "game_count": 120,
      "persona_state": 0,
      "engagement_ratio": 0.0,
      "high_value_player": 1,
      "avg_playtime_per_game": 1000.0
    }
    with TestClient(app) as client:
        response = client.post("/predict", json=payload)
        print("\n--- PREDICT ---")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_health()
    test_predict()
