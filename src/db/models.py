from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from datetime import datetime
from src.db.database import Base

class PlayerSnapshot(Base):
    __tablename__ = "player_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String(20), index=True, nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    playtime_forever = Column(Integer)
    playtime_2weeks = Column(Integer)
    last_logoff = Column(BigInteger)
    game_count = Column(Integer)
    persona_state = Column(Integer)
    
    engagement_ratio = Column(Float)
    high_value_player = Column(Integer)
    avg_playtime_per_game = Column(Float)


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String(20), index=True, nullable=False)
    scored_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    churn_probability = Column(Float)
    churn_risk_tier = Column(String(10))
    player_value_tier = Column(String(10))
    segment = Column(String(30))
    recommendation = Column(String(255))
    
    playtime_2weeks_at_scoring = Column(Integer)
    playtime_forever_at_scoring = Column(Integer)
