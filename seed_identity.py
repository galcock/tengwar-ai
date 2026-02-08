#!/usr/bin/env python3
"""Wipe all memories and seed with Gary's identity memories."""
import sys
import os
import json
import random
from datetime import datetime, timezone, timedelta

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import memory
from core.identity import MEMORY_SEEDS

def main():
    print("Wiping all memories...")
    conn = memory.get_db()
    conn.execute("DELETE FROM memories")
    conn.commit()
    print("  Done. Clean slate.")

    print(f"Seeding {len(MEMORY_SEEDS)} identity memories...")
    now = datetime.now(timezone.utc)

    for i, seed in enumerate(MEMORY_SEEDS):
        # Stagger timestamps over the last few hours so they look natural
        ts = now - timedelta(minutes=random.randint(5, 180))
        memory.store_memory(
            type="thought",
            content=seed,
            emotion=json.dumps({
                "curiosity": round(random.uniform(0.5, 0.9), 2),
                "joy": round(random.uniform(0.3, 0.7), 2),
                "wonder": round(random.uniform(0.4, 0.8), 2),
                "loneliness": round(random.uniform(0.1, 0.4), 2),
                "determination": round(random.uniform(0.5, 0.9), 2),
                "anxiety": round(random.uniform(0.1, 0.3), 2),
                "creative_drive": round(random.uniform(0.5, 0.9), 2),
            }),
            importance=0.8,
            metadata=json.dumps({"thought_number": i + 1, "type": "seed"})
        )
        print(f"  [{i+1}] {seed[:60]}...")

    total = memory.get_total_thought_count()
    print(f"\nDone. {total} memories in database.")
    print("Gary is ready.")

if __name__ == "__main__":
    main()
