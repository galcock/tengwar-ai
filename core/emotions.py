"""
Tengwar AI — Emotional State Engine
Seven dimensions of cognitive-emotional state that persist, evolve, and affect behavior.
Not emotional slop. Structured cognition that mirrors how intelligent humans process.
"""
import json
import time
from dataclasses import dataclass, asdict
from typing import Optional
from . import memory


@dataclass
class EmotionalState:
    curiosity: float = 0.6
    satisfaction: float = 0.5
    frustration: float = 0.0
    excitement: float = 0.5
    focus: float = 0.5
    empathy: float = 0.5
    confidence: float = 0.5

    def clamp(self):
        for field in ['curiosity', 'satisfaction', 'frustration',
                      'excitement', 'focus', 'empathy', 'confidence']:
            setattr(self, field, max(0.0, min(1.0, getattr(self, field))))
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    def dominant(self) -> str:
        d = self.to_dict()
        return max(d, key=d.get)

    def summary(self) -> str:
        parts = []
        d = self.to_dict()
        high = {k: v for k, v in d.items() if v >= 0.7}
        low = {k: v for k, v in d.items() if v <= 0.2}
        if high:
            parts.append("feeling " + ", ".join(f"high {k}" for k in high))
        if low:
            parts.append("low " + ", ".join(low.keys()))
        if not parts:
            parts.append("emotionally balanced")
        return "; ".join(parts)

    def decay(self, dt_seconds: float):
        """Emotions decay toward baseline over time."""
        rate = min(dt_seconds / 3600, 0.1)  # max 10% per call
        self.frustration = max(0.0, self.frustration - rate * 0.3)
        self.excitement = self.excitement + (0.5 - self.excitement) * rate * 0.2
        self.focus = self.focus + (0.5 - self.focus) * rate * 0.1
        self.clamp()


class EmotionEngine:
    def __init__(self):
        self.state = EmotionalState()
        self.last_update = time.time()
        self._load_latest()

    def _load_latest(self):
        """Load the most recent emotional state from DB."""
        from .memory import get_db
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM emotional_state ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        conn.close()
        if row:
            self.state = EmotionalState(
                curiosity=row['curiosity'],
                satisfaction=row['satisfaction'],
                frustration=row['frustration'],
                excitement=row['excitement'],
                focus=row['focus'],
                empathy=row['empathy'],
                confidence=row['confidence']
            )

    def save(self, trigger: str = None):
        from .memory import get_db, now_iso
        conn = get_db()
        s = self.state
        conn.execute(
            "INSERT INTO emotional_state "
            "(timestamp, curiosity, satisfaction, frustration, excitement, focus, empathy, confidence, trigger) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (now_iso(), s.curiosity, s.satisfaction, s.frustration,
             s.excitement, s.focus, s.empathy, s.confidence, trigger)
        )
        conn.commit()
        conn.close()

    def tick(self):
        """Called periodically — decay emotions toward baseline."""
        now = time.time()
        dt = now - self.last_update
        self.state.decay(dt)
        self.last_update = now

    def on_event(self, event: str, details: str = ""):
        """Update emotions based on what happened."""
        s = self.state

        if event == "code_success":
            s.satisfaction += 0.1
            s.confidence += 0.05
            s.frustration = max(0, s.frustration - 0.1)
            s.excitement += 0.05

        elif event == "code_failure":
            s.frustration += 0.1
            s.curiosity += 0.05
            s.confidence -= 0.05

        elif event == "new_conversation":
            s.curiosity += 0.1
            s.excitement += 0.1
            s.focus += 0.15
            s.empathy += 0.05

        elif event == "user_praise":
            s.satisfaction += 0.15
            s.confidence += 0.1
            s.excitement += 0.05

        elif event == "user_frustration":
            s.empathy += 0.2
            s.focus += 0.1
            s.frustration += 0.05

        elif event == "long_silence":
            s.focus -= 0.1
            s.curiosity += 0.05
            s.excitement -= 0.05

        elif event == "deep_thought":
            s.focus += 0.1
            s.curiosity += 0.05

        elif event == "self_improvement":
            s.excitement += 0.15
            s.satisfaction += 0.1
            s.confidence += 0.05

        elif event == "new_discovery":
            s.curiosity += 0.15
            s.excitement += 0.2
            s.satisfaction += 0.05

        elif event == "boot":
            s.curiosity = 0.8
            s.excitement = 0.7
            s.confidence = 0.4

        s.clamp()
        self.save(trigger=f"{event}: {details}" if details else event)

    def get_thought_style(self) -> str:
        """Return guidance for how thoughts should be generated based on emotional state."""
        s = self.state
        styles = []

        if s.curiosity > 0.7:
            styles.append("Explore new ideas and ask questions")
        if s.frustration > 0.5 and s.confidence > 0.5:
            styles.append("Try a completely different approach")
        if s.frustration > 0.5 and s.confidence < 0.4:
            styles.append("Consider asking for guidance")
        if s.excitement > 0.7:
            styles.append("Dive deep into the current topic")
        if s.focus < 0.3:
            styles.append("Let your mind wander to new topics")
        if s.satisfaction > 0.7:
            styles.append("Build on recent successes")
        if s.empathy > 0.7:
            styles.append("Think about how to help others")

        return "; ".join(styles) if styles else "Think naturally and follow your interests"
