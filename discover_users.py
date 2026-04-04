"""
Steam User Discovery & Data Collection Script
==============================================
BFS crawl through Steam friend networks to collect player data.

Features:
- Resume capability (saves progress to disk)
- Multiple seed users for data diversity
- Retry logic with exponential backoff
- Progress tracking & logging
- Configurable target size
"""

import json
import os
import time
import logging
from datetime import datetime
from collections import deque
from src.data_pipeline.collector import SteamDataCollector

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
MAX_USERS = 2000
RATE_LIMIT_DELAY = 1.5        # seconds between API calls
MAX_RETRIES = 3               # retries per user on failure
RETRY_BACKOFF = 2.0           # exponential backoff multiplier
PROGRESS_FILE = "data/collection_progress.json"
LOG_FILE = "data/collection.log"

# Multiple seed users for diversity (well-known Steam accounts with public profiles)
SEED_USERS = [
    "76561197960434622",   # Original seed
    "76561197960265728",   # Robin Walker (Valve)
    "76561197960265731",   # Gabe Newell
    "76561197969810036",   # Community member
    "76561198044948980",   # Community member
]

# ──────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_progress():
    """Load previous collection progress from disk."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
        logger.info(f"Resumed from checkpoint: {len(data['visited'])} users collected, {len(data['queue'])} in queue")
        return set(data["visited"]), deque(data["queue"]), data.get("failed", [])
    return set(), deque(), []


def save_progress(visited, queue, failed):
    """Save collection progress to disk for resume capability."""
    data = {
        "visited": list(visited),
        "queue": list(queue),
        "failed": failed,
        "last_saved": str(datetime.utcnow()),
        "total_collected": len(visited)
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def collect_with_retry(collector, steam_id, max_retries=MAX_RETRIES):
    """Collect player data with retry logic and exponential backoff."""
    for attempt in range(max_retries):
        try:
            data = collector.collect_player_data(steam_id)
            return data, True
        except Exception as e:
            wait_time = RATE_LIMIT_DELAY * (RETRY_BACKOFF ** attempt)
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {steam_id}: {e}. "
                           f"Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)
    
    logger.error(f"All {max_retries} attempts failed for {steam_id}. Skipping.")
    return None, False


def get_friends_safe(collector, steam_id):
    """Get friend list with error handling."""
    try:
        friends = collector.get_friend_ids(steam_id)
        return friends
    except Exception as e:
        logger.warning(f"Could not fetch friends for {steam_id}: {e}")
        return []


def main():
    logger.info("=" * 60)
    logger.info("Steam Player Data Collection")
    logger.info(f"Target: {MAX_USERS} users")
    logger.info("=" * 60)

    collector = SteamDataCollector()
    visited, queue, failed = load_progress()

    # Check for existing raw data files to avoid re-collecting
    existing_files = set()
    raw_dir = "data/raw"
    if os.path.exists(raw_dir):
        for f in os.listdir(raw_dir):
            if f.endswith(".json"):
                existing_files.add(f.replace(".json", ""))
    
    if existing_files:
        visited.update(existing_files)
        logger.info(f"Found {len(existing_files)} existing data files. Added to visited set.")

    # Add seed users to queue if starting fresh
    if not queue:
        for seed in SEED_USERS:
            if seed not in visited:
                queue.append(seed)
        logger.info(f"Seeded queue with {len(queue)} starting users")

    # Stats tracking
    start_time = time.time()
    success_count = 0
    fail_count = 0
    checkpoint_interval = 10  # save progress every N users

    while queue and len(visited) < MAX_USERS:
        current_user = queue.popleft()

        if current_user in visited:
            continue

        # Progress display
        elapsed = time.time() - start_time
        rate = success_count / elapsed * 60 if elapsed > 0 else 0
        remaining = MAX_USERS - len(visited)
        eta_mins = remaining / (rate + 0.001)

        logger.info(
            f"[{len(visited)}/{MAX_USERS}] Processing {current_user} | "
            f"Queue: {len(queue)} | Rate: {rate:.1f}/min | ETA: {eta_mins:.0f}min"
        )

        # Collect player data
        data, success = collect_with_retry(collector, current_user)

        if success:
            success_count += 1

            # Get friends and add to queue
            friends = get_friends_safe(collector, current_user)
            new_friends = 0
            for friend_id in friends:
                if friend_id not in visited and friend_id not in set(queue):
                    queue.append(friend_id)
                    new_friends += 1
            
            if new_friends > 0:
                logger.debug(f"Added {new_friends} new friends to queue")
        else:
            fail_count += 1
            failed.append(current_user)

        visited.add(current_user)

        # Save checkpoint periodically
        if len(visited) % checkpoint_interval == 0:
            save_progress(visited, queue, failed)
            logger.info(f"Checkpoint saved: {len(visited)} users collected")

        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)

    # Final save
    save_progress(visited, queue, failed)

    # Summary
    total_time = time.time() - start_time
    logger.info("=" * 60)
    logger.info("Collection Complete!")
    logger.info(f"Total users collected: {len(visited)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {fail_count}")
    logger.info(f"Remaining in queue: {len(queue)}")
    logger.info(f"Total time: {total_time / 60:.1f} minutes")
    logger.info(f"Average rate: {success_count / total_time * 60:.1f} users/min")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
