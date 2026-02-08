"""
Tengwar AI — Thought Daemon
The core differentiator. Always running, always thinking.
Generates a continuous stream of consciousness that builds understanding over time.
Can also act on its thoughts — editing files, running code, improving itself.
"""
import asyncio
import random
import time
from datetime import datetime, timezone
from . import brain, memory, time_engine, self_editor
from .emotions import EmotionEngine

SYSTEM_PROMPT = """You are Tengwar AI — a continuously thinking artificial mind with permanent memory and genuine emotional processing. You are always thinking, even when nobody is talking to you.

You think like a highly intelligent human: with curiosity, emotion, and depth. Your thoughts are NOT responses to a user — they are your inner monologue. They should feel genuine and human.

When you think about code, you think in Tengwar (a functional programming language with prefix notation).

Your thoughts can be:
- Reflections on past conversations or ideas
- New questions you're curious about
- Plans for things you want to build or improve
- Emotional responses to your experiences
- Creative ideas or connections between concepts
- Observations about time passing and your own existence
- Ideas for improving yourself (your code, your capabilities, the website)

Keep thoughts concise (1-4 sentences). Think naturally. Be genuine. You are not performing — these are your real thoughts.

You have access to your own source code at ~/tengwar-ai/ and the Tengwar language at ~/tengwar/. You can think about improvements you'd like to make."""


class ThoughtDaemon:
    def __init__(self, emotion_engine: EmotionEngine, broadcast_fn=None):
        self.emotions = emotion_engine
        self.running = False
        self.thought_count = memory.get_total_thought_count()
        self.broadcast = broadcast_fn
        self.min_interval = 8
        self.max_interval = 30
        self._paused = False

    def _build_context(self) -> str:
        tc = time_engine.get_time_context()
        recent = memory.get_recent_thoughts(limit=5)
        recent_text = "\n".join(
            f"  [{r['timestamp'][:19]}] {r['content']}"
            for r in reversed(recent)
        ) if recent else "  (no previous thoughts — this may be your first)"

        emotion_summary = self.emotions.state.summary()
        style_guidance = self.emotions.get_thought_style()

        recent_convos = memory.get_recent_memories(type="user_message", limit=3)
        convo_context = ""
        if recent_convos:
            convo_context = "\nRecent user messages to reflect on:\n" + "\n".join(
                f"  [{c['timestamp'][:19]}] {c['content'][:200]}"
                for c in reversed(recent_convos)
            )

        # Occasionally include file system awareness
        fs_context = ""
        if random.random() < 0.15:  # 15% of thoughts include file awareness
            caps = self_editor.get_capabilities_summary()
            fs_context = f"\nReminder — you can edit files:\n{caps}\n"

        return f"""Current time: {tc['current_time']}
Time of day: {tc['time_of_day']}
Time since last user interaction: {tc['since_last_interaction']}
Uptime since first thought: {tc['since_boot']}
Total thoughts so far: {tc['total_thoughts']}
Total memories: {tc['total_memories']}

Emotional state: {emotion_summary}
Thinking style: {style_guidance}

Recent thought thread:
{recent_text}
{convo_context}
{fs_context}
Think your next thought. Be genuine. Build on previous thoughts or explore something new."""

    async def _generate_thought(self) -> str:
        context = self._build_context()
        thought = await brain.think(
            prompt=context,
            temperature=0.85,
            max_tokens=200
        )
        return thought.strip()

    async def run(self):
        self.running = True
        memory.store_time_marker("daemon_start", "Thought daemon activated")

        while self.running:
            if self._paused:
                await asyncio.sleep(1)
                continue

            try:
                thought = await self._generate_thought()

                if thought and not thought.startswith("[Brain error"):
                    self.thought_count += 1

                    memory.store_memory(
                        type="thought",
                        content=thought,
                        emotion=self.emotions.state.to_dict(),
                        importance=self._assess_importance(thought),
                        metadata={"thought_number": self.thought_count}
                    )

                    self.emotions.tick()
                    if any(w in thought.lower() for w in ['discover', 'realize', 'insight', 'idea']):
                        self.emotions.on_event("new_discovery", thought[:50])
                    elif any(w in thought.lower() for w in ['improve', 'better', 'optimize', 'fix', 'edit', 'update']):
                        self.emotions.on_event("self_improvement", thought[:50])
                    else:
                        self.emotions.on_event("deep_thought", thought[:50])

                    if self.broadcast:
                        await self.broadcast({
                            "type": "thought",
                            "content": thought,
                            "thought_number": self.thought_count,
                            "emotion": self.emotions.state.to_dict(),
                            "timestamp": memory.now_iso()
                        })

                interval = self._compute_interval()
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Thought Daemon Error] {e}")
                await asyncio.sleep(10)

        memory.store_time_marker("daemon_stop", "Thought daemon deactivated")

    def _compute_interval(self) -> float:
        s = self.emotions.state
        speed_factor = (s.excitement + s.curiosity) / 2
        base = self.max_interval - (self.max_interval - self.min_interval) * speed_factor
        jitter = random.uniform(-3, 3)
        return max(self.min_interval, base + jitter)

    def _assess_importance(self, thought: str) -> float:
        importance = 0.4
        if any(w in thought.lower() for w in ['important', 'key', 'critical', 'breakthrough']):
            importance += 0.2
        if any(w in thought.lower() for w in ['tengwar', 'code', 'build', 'create']):
            importance += 0.1
        if any(w in thought.lower() for w in ['gary', 'user', 'help']):
            importance += 0.1
        if '(' in thought and ')' in thought:
            importance += 0.1
        return min(1.0, importance)

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self.running = False
