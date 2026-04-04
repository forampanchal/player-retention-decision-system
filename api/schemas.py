from pydantic import BaseModel
from typing import List

class PlayerFeatures(BaseModel):
    steam_id: str
    playtime_forever: int
    playtime_2weeks: int
    last_logoff: int
    game_count: int
    persona_state: int
    engagement_ratio: float
    high_value_player: int
    avg_playtime_per_game: float

class PredictionResponse(BaseModel):
    steam_id: str
    churn_probability: float
    churn_risk_tier: str
    player_value_tier: str
    segment: str
    recommendation: str
    action_urgency: str

class BatchPredictionRequest(BaseModel):
    players: List[PlayerFeatures]

class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
