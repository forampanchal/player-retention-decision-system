def assign_segment(row):
    if row["high_value"] and row["churn_risk"] > 0.7:
        return "high_value_high_risk"
    elif row["high_value"]:
        return "high_value_low_risk"
    elif row["churn_risk"] > 0.7:
        return "low_value_high_risk"
    else:
        return "low_value_low_risk"


def recommend_action(segment):
    actions = {
        "high_value_high_risk": "Send personalized game recommendation",
        "high_value_low_risk": "Monitor engagement",
        "low_value_high_risk": "No intervention",
        "low_value_low_risk": "Passive"
    }
    return actions.get(segment, "Unknown")


def recommend_action(row):
    churn = row["churn"]
    high_value = row["high_value_player"]
    engagement = row["engagement_ratio"]

    if churn == 1 and high_value == 1:
        return "🔥 High Priority: Offer discount / rewards"

    elif churn == 1 and high_value == 0:
        return "⚠️ Low Priority: Send generic notification"

    elif churn == 0 and engagement > 0.1:
        return "✅ Active: No action needed"

    else:
        return "👀 Monitor user"
