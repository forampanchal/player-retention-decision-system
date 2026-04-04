import joblib
import pandas as pd
import os
from sqlalchemy.orm import Session
from datetime import datetime

from src.db.models import PlayerSnapshot, PredictionHistory
from api.recommendation import get_recommendation

MODEL_PATH = "models/xgboost_churn_model.pkl"
model = None

def load_local_model():
    global model
    if model is None and os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
    return model

def batch_score_snapshots(db: Session, snapshots: list[PlayerSnapshot]) -> list[PredictionHistory]:
    """
    Takes a batch of raw PlayerSnapshots, scores them through the model, 
    and generates PredictionHistory ORM objects ready for DB insertion.
    Returns the generated PredictionHistory objects.
    """
    current_model = load_local_model()
    if current_model is None:
        raise RuntimeError("Model not found. Cannot score snapshots.")
        
    predictions = []
    
    for snap in snapshots:
        # Prevent completely invalid data from breaking the pipeline
        if snap.playtime_forever is None or snap.game_count is None:
            continue
            
        # The XGBoost model strictly EXCLUDES recent_playtime and engagement_ratio 
        feature_dict = {
            "personastate": [snap.persona_state or 0],
            "total_playtime": [snap.playtime_forever],
            "game_count": [snap.game_count],
            "high_value_player": [snap.high_value_player or 0],
            "avg_playtime_per_game": [snap.avg_playtime_per_game or 0.0]
        }
        X_pred = pd.DataFrame(feature_dict)
        
        prob = float(current_model.predict_proba(X_pred)[0][1])
        
        # Determine recommendations using the exact same logic as our API
        rec = get_recommendation(prob, snap.high_value_player or 0)
        
        history = PredictionHistory(
            steam_id=snap.steam_id,
            scored_at=datetime.utcnow(),
            churn_probability=prob,
            churn_risk_tier=rec["churn_risk_tier"],
            player_value_tier=rec["player_value_tier"],
            segment=rec["segment"],
            recommendation=rec["recommendation"],
            playtime_2weeks_at_scoring=snap.playtime_2weeks,
            playtime_forever_at_scoring=snap.playtime_forever
        )
        predictions.append(history)
        
    return predictions
