def get_recommendation(churn_prob: float, high_value_player: int) -> dict:
    """
    Apply business rules to segment players and recommend actions based on
    their churn probability and player value.
    """
    
    churn_risk_tier = "high" if churn_prob >= 0.7 else ("medium" if churn_prob >= 0.4 else "low")
    player_value_tier = "high" if high_value_player == 1 else "low"
    
    if churn_prob > 0.7 and high_value_player == 1:
        return {
            "churn_risk_tier": churn_risk_tier,
            "player_value_tier": player_value_tier,
            "segment": "priority_save",
            "recommendation": "Send personalised re-engagement offer immediately",
            "action_urgency": "immediate"
        }
    
    elif churn_prob > 0.7 and high_value_player == 0:
        return {
            "churn_risk_tier": churn_risk_tier,
            "player_value_tier": player_value_tier,
            "segment": "monitor",
            "recommendation": "Send generic win-back email",
            "action_urgency": "high"
        }
    
    elif 0.4 <= churn_prob <= 0.7 and high_value_player == 1:
        return {
            "churn_risk_tier": churn_risk_tier,
            "player_value_tier": player_value_tier,
            "segment": "at_risk_vip",
            "recommendation": "Send loyalty reward or discount",
            "action_urgency": "medium"
        }
        
    elif 0.4 <= churn_prob <= 0.7 and high_value_player == 0:
        return {
            "churn_risk_tier": churn_risk_tier,
            "player_value_tier": player_value_tier,
            "segment": "at_risk",
            "recommendation": "Show in-game notification",
            "action_urgency": "low"
        }
        
    else:
        return {
            "churn_risk_tier": churn_risk_tier,
            "player_value_tier": player_value_tier,
            "segment": "healthy",
            "recommendation": "No action needed",
            "action_urgency": "none"
        }
