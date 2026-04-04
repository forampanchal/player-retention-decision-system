import time
from sqlalchemy.orm import Session
from datetime import datetime

from src.data_pipeline.steam_api import SteamAPI
from src.db.models import PlayerSnapshot

def refresh_players(db: Session, steam_ids: list[str]) -> list[PlayerSnapshot]:
    """
    Given a list of Steam IDs, re-fetches their current status from the Steam Web API,
    computes standard engagement metrics, and returns a list of ORM PlayerSnapshot objects.
    """
    api = SteamAPI()
    snapshots = []
    
    print(f"Refreshing snapshot data for {len(steam_ids)} players...")
    
    for steam_id in steam_ids:
        try:
            # Add a small delay to respect Steam API rate limits
            time.sleep(0.5)
            
            # Fetch raw data
            # Summary returns a dict with 'response': {'players': [...]}
            summary_raw = api.get_player_summary([steam_id])
            if not summary_raw or "response" not in summary_raw or not summary_raw["response"].get("players"):
                continue
                
            player_data = summary_raw["response"]["players"][0]
            last_logoff = player_data.get("lastlogoff")
            persona_state = player_data.get("personastate", 0)
            
            # Owned games
            games_raw = api.get_owned_games(steam_id)
            total_playtime = 0
            game_count = 0
            if games_raw and "response" in games_raw and "games" in games_raw["response"]:
                games = games_raw["response"]["games"]
                total_playtime = sum(g.get("playtime_forever", 0) for g in games)
                game_count = len(games)
                
            # Recent playtime
            recent_raw = api.get_recent_games(steam_id)
            recent_playtime = 0
            if recent_raw and "response" in recent_raw and "games" in recent_raw["response"]:
                recent_games = recent_raw["response"]["games"]
                recent_playtime = sum(g.get("playtime_2weeks", 0) for g in recent_games)
                
            # Derived feature engineering equivalent to process_data.py
            engagement_ratio = 0.0
            if total_playtime > 0:
                engagement_ratio = recent_playtime / total_playtime
                
            high_value_player = 1 if total_playtime > 100 else 0
            
            avg_playtime_per_game = 0.0
            if game_count > 0:
                avg_playtime_per_game = total_playtime / game_count
                
            snap = PlayerSnapshot(
                steam_id=steam_id,
                collected_at=datetime.utcnow(),
                playtime_forever=total_playtime,
                playtime_2weeks=recent_playtime,
                last_logoff=last_logoff,
                game_count=game_count,
                persona_state=persona_state,
                engagement_ratio=engagement_ratio,
                high_value_player=high_value_player,
                avg_playtime_per_game=avg_playtime_per_game
            )
            snapshots.append(snap)
            
        except Exception as e:
            print(f"Error fetching data for {steam_id}: {e}")
            
    return snapshots
