from fastapi import FastAPI, HTTPException
import joblib
import pandas as pd
import os

from api.schemas import PlayerFeatures, PredictionResponse, BatchPredictionRequest, BatchPredictionResponse
from api.recommendation import get_recommendation

app = FastAPI(
    title="Player Retention Decision API",
    description="MLOps API serving XGBoost churn predictions and business rules.",
    version="1.0.0"
)

# Load the trained XGBoost model at startup
MODEL_PATH = "models/xgboost_churn_model.pkl"

# We initialize it as None and load during startup 
# to safely fail over if the file is missing locally
model = None

@app.on_event("startup")
def load_model():
    global model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"SUCCESS: Loaded XGBoost model from {MODEL_PATH}")
    else:
        print(f"WARNING: Model not found at {MODEL_PATH}. Prediction endpoints will fail.")

@app.get("/health")
def health_check():
    """Simple health check endpoint for Docker/Kubernetes."""
    return {"status": "ok", "model_loaded": model is not None}

def score_player(player: PlayerFeatures) -> PredictionResponse:
    if model is None:
        raise HTTPException(status_code=503, detail="Prediction model is not loaded.")
        
    # The XGBoost model expects exact feature names and ordering as created by pandas
    # during training. We map the API schema (playtime_forever) to the CSV feature (total_playtime).
    feature_dict = {
        "personastate": [player.persona_state],
        "total_playtime": [player.playtime_forever],
        "game_count": [player.game_count],
        "high_value_player": [player.high_value_player],
        "avg_playtime_per_game": [player.avg_playtime_per_game]
    }
    
    # Cast to DataFrame to preserve feature names exactly as XGBoost trained them
    X_pred = pd.DataFrame(feature_dict)
    
    # Predict Probability
    prob = float(model.predict_proba(X_pred)[0][1])
    
    # Apply Business Rules
    recommendation_data = get_recommendation(
        churn_prob=prob, 
        high_value_player=player.high_value_player
    )
    
    return PredictionResponse(
        steam_id=player.steam_id,
        churn_probability=prob,
        **recommendation_data
    )

@app.post("/predict", response_model=PredictionResponse)
def predict_churn(player: PlayerFeatures):
    """Predict churn for a single player."""
    try:
        return score_player(player)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_churn_batch(request: BatchPredictionRequest):
    """Predict churn for a batch of players."""
    try:
        predictions = [score_player(p) for p in request.players]
        return BatchPredictionResponse(predictions=predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
