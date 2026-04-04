import logging
import json
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

from src.db.database import SessionLocal
from src.pipeline.steam_refresh import refresh_players
from src.ml.scorer import batch_score_snapshots
from src.notifications.discord_alert import send_churn_alert

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def get_target_steam_ids():
    """Retrieve Steam IDs to process from collection progress as a fallback seed."""
    try:
        with open("data/collection_progress.json", "r") as f:
            data = json.load(f)
            return list(data.get("collected", []))[:100]  # Take a small manageable batch for testing
    except FileNotFoundError:
        # Fallback to a hardcoded test if no data crawler file exists
        return ["76561198081375397"]

def run_pipeline():
    """Main pipeline strictly executing Phase 3C steps."""
    logger.info("=== STARTING WEEKLY CHURN PIPELINE ===")
    
    steam_ids = get_target_steam_ids()
    if not steam_ids:
        logger.warning("No Steam IDs found to process!")
        return

    # Create short-lived DB session
    db = SessionLocal()
    
    try:
        # Step 2-4: Fetch and snapshot
        logger.info(f"Fetching metrics for {len(steam_ids)} players from Steam API...")
        new_snapshots = refresh_players(db, steam_ids)
        
        # Save explicitly to DB
        db.add_all(new_snapshots)
        db.commit()
        logger.info(f"Committed {len(new_snapshots)} PlayerSnapshots to PostgreSQL.")

        # Step 5-8: Score Player Data
        logger.info("Loading XGBoost Model and analyzing batches...")
        new_predictions = batch_score_snapshots(db, new_snapshots)
        
        # Save explicitly to DB
        db.add_all(new_predictions)
        db.commit()
        logger.info(f"Committed {len(new_predictions)} PredictionHistorical records to PostgreSQL.")
        
        # Step 9-10: Filter for notifications (.churn_probability > 0.70)
        high_risk_list = [p for p in new_predictions if p.churn_probability > 0.70]
        logger.info(f"Identified {len(high_risk_list)} high-risk players requiring interception.")
        
        if high_risk_list:
            send_churn_alert(high_risk_list, len(new_predictions))
            
    except Exception as e:
        db.rollback()
        logger.error(f"Pipeline crashed: {e}")
    finally:
        db.close()
        logger.info("=== PIPELINE RUN COMPLETE ===")


if __name__ == "__main__":
    # If run directly as a script module, execute immediately or boot up scheduler
    import sys
    if "--run-now" in sys.argv:
        run_pipeline()
    else:
        logger.info("Starting APScheduler... Setup to trigger every 7 days.")
        scheduler = BlockingScheduler()
        # "Every 7 days, automatically re-fetch the same Steam IDs"
        scheduler.add_job(run_pipeline, 'interval', days=7)
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            pass
