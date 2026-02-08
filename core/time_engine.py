"""
Tengwar AI — Time Engine
Real temporal awareness. Knows what time it is, how long since events,
and develops a sense of time passing like a human.
"""
from datetime import datetime, timezone, timedelta
from . import memory


def now():
    return datetime.now(timezone.utc)


def format_time(dt=None):
    dt = dt or now()
    return dt.strftime("%A, %B %d, %Y at %I:%M %p UTC")


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f"{mins} minute{'s' if mins != 1 else ''}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        if mins > 0:
            return f"{hours}h {mins}m"
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        if hours > 0:
            return f"{days}d {hours}h"
        return f"{days} day{'s' if days != 1 else ''}"


def time_since_last_interaction() -> str:
    last = memory.get_last_user_interaction()
    if not last:
        return "no previous interactions"
    last_time = datetime.fromisoformat(last['timestamp'])
    delta = now() - last_time
    return format_duration(delta.total_seconds())


def time_since_boot() -> str:
    first = memory.get_first_memory()
    if not first:
        return "just booted"
    first_time = datetime.fromisoformat(first['timestamp'])
    delta = now() - first_time
    return format_duration(delta.total_seconds())


def get_time_context() -> dict:
    """Full temporal context for thought/dialogue generation."""
    n = now()
    hour = n.hour
    if 5 <= hour < 12:
        period = "morning"
    elif 12 <= hour < 17:
        period = "afternoon"
    elif 17 <= hour < 21:
        period = "evening"
    else:
        period = "late night"

    return {
        "current_time": format_time(n),
        "time_of_day": period,
        "day_of_week": n.strftime("%A"),
        "since_last_interaction": time_since_last_interaction(),
        "since_boot": time_since_boot(),
        "total_thoughts": memory.get_total_thought_count(),
        "total_memories": memory.get_total_memory_count(),
    }
