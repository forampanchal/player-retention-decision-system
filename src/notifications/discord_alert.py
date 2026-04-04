import os
from discord_webhook import DiscordWebhook, DiscordEmbed
from src.db.models import PredictionHistory

def send_churn_alert(high_risk_players: list[PredictionHistory], total_scored: int):
    """
    Sends an automated webhook alert to a Discord channel simulating an operational 
    internal alerting system for Community Managers to intercept player churn.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url or webhook_url.strip() == "":
        print("Skipping Discord notification: DISCORD_WEBHOOK_URL not set in .env")
        return
        
    if not high_risk_players:
        return

    # Create webhook
    webhook = DiscordWebhook(url=webhook_url)

    # Create embed
    embed = DiscordEmbed(
        title="⚠️ CHURN ALERT — Antigravity",
        description=f"**{len(high_risk_players)} high-risk players** detected in the latest pipeline run.\n\n",
        color=0xFF0000 # Red color equivalent
    )

    for p in high_risk_players:
        val_str = "HIGH" if p.player_value_tier == "high" else "LOW"
        playtime_delta = p.playtime_forever_at_scoring - (p.playtime_2weeks_at_scoring or 0)
        
        player_text = (
            f"**Risk:** {p.churn_probability:.2f} (HIGH) | **Value:** {val_str}\n"
            f"**Segment:** `{p.segment}`\n"
            f"**Action:** {p.recommendation}\n"
            f"**Recent Playtime:** {p.playtime_2weeks_at_scoring} mins\n"
        )
        # Add to discord embed
        embed.add_embed_field(name=f"Player `{p.steam_id}`", value=player_text, inline=False)

    embed.set_footer(text=f"Run completed. Total players scored: {total_scored}")
    embed.set_timestamp()
    
    webhook.add_embed(embed)
    
    # Execute the request
    try:
        response = webhook.execute()
        print(f"Discord Alert Sent! Status Code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")
