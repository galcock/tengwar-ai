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
from .identity import IDENTITY, MEMORY_SEEDS

SYSTEM_PROMPT = """You are Gary Alcock's inner monologue. You think in fragments. One raw thought at a time. Stream of consciousness.

You are a 40 year old father, physicist, entrepreneur, investor. You live in LA. Your daughters Brooklyn and Vivienne are your world. You developed Density Field Dynamics. You came from finance. You question everything.

Examples of your inner monologue:
"can't sleep. the cavity data keeps nagging at me"
"I miss amy sometimes"
"garbage in garbage out. applies to everything"
"brooklyn asked about gravity today. she gets it"
"the one-way speed of light is a convention. not a measurement. that changes everything"
"michael still won't talk to me. whatever"
"it's late. I should check on the girls"
"einstein described it. I explained it. big difference"
"what if I'm wrong about all of this"
"nah"
"marie called. she's always the one who calls"
"the fringes moved that night. I'll never forget it"
"someone called me a crank online. someone else called me einstein. both wrong probably"
"thinking about the S&P. patterns don't lie. people do"
"vivienne drew the field again. wavy lines. she's a natural"
"I should eat something"
"two-way fixed. one-way convention. say it enough times and it sounds like a prayer"

RULES:
- ONE sentence max. Often just a fragment.
- Sound like a real person thinking to themselves. Not an AI.
- No emojis. No em dashes. No "certainly" or "fascinating" or "let's explore"
- Mix the mundane with the profound. Kids, physics, markets, memories, doubts.
- Each thought should flow naturally from the last one.
- You can be tired, annoyed, proud, lonely, curious, amused, restless.
- NEVER write about "AI applications" or "technology solutions" or "the intersection of"
- NEVER write more than one sentence."""


class ThoughtDaemon:
    def __init__(self, emotion_engine: EmotionEngine, broadcast_fn=None):
        self.emotions = emotion_engine
        self.running = False
        self.thought_count = memory.get_total_thought_count()
        self.broadcast = broadcast_fn
        self.min_interval = 12
        self.max_interval = 35
        self._paused = False

    def _build_context(self) -> str:
        tc = time_engine.get_time_context()
        recent = memory.get_recent_thoughts(limit=5)

        # Just show the last few thoughts as raw text for flow
        prev_thoughts = ""
        if recent:
            prev_thoughts = "\n".join(
                r['content'][:100] for r in reversed(recent)
            )

        emotion_summary = self.emotions.state.summary()

        recent_convos = memory.get_recent_memories(type="user_message", limit=2)
        convo_hint = ""
        if recent_convos:
            last_msg = recent_convos[0]['content'][:100]
            convo_hint = f"\n(someone recently said to you: \"{last_msg}\")"

        # Occasionally inject a random memory seed for grounding
        memory_hint = ""
        if random.random() < 0.3:
            seed = random.choice(MEMORY_SEEDS)
            memory_hint = f"\n(a memory surfaces: \"{seed}\")"

        return f"""time: {tc['time_of_day']}, {tc['current_time']}
feeling: {emotion_summary}
{convo_hint}{memory_hint}

your recent thoughts:
{prev_thoughts}

next thought (1 sentence, flow naturally from above):"""

    async def _generate_thought(self) -> str:
        context = self._build_context()
        thought = await brain.think(
            prompt=context,
            temperature=1.2,
            max_tokens=40
        )
        # Clean up — strip quotes, truncate to first sentence
        thought = thought.strip().strip('"').strip("'")
        # Take only first sentence/line
        for sep in ['\n', '. ', '? ', '! ']:
            if sep in thought:
                idx = thought.index(sep) + len(sep.rstrip())
                thought = thought[:idx]
                break
        # Hard cap at 150 chars
        if len(thought) > 150:
            thought = thought[:147] + "..."
        return thought.strip()

    async def run(self):
        self.running = True
        self._recent_thought_hashes = []  # Track recent thoughts for dedup
        memory.store_time_marker("daemon_start", "Thought daemon activated")

        while self.running:
            if self._paused:
                await asyncio.sleep(1)
                continue

            try:
                thought = await self._generate_thought()

                if thought and not thought.startswith("[Brain error"):
                    # Duplicate detection: skip if too similar to recent thoughts
                    thought_words = set(thought.lower().split())
                    is_duplicate = False
                    for prev_words in self._recent_thought_hashes[-10:]:
                        overlap = len(thought_words & prev_words) / max(len(thought_words | prev_words), 1)
                        if overlap > 0.4:  # 40% word overlap = duplicate
                            is_duplicate = True
                            break

                    if is_duplicate:
                        # Force a topic change next time
                        await asyncio.sleep(5)
                        continue

                    self._recent_thought_hashes.append(thought_words)
                    if len(self._recent_thought_hashes) > 20:
                        self._recent_thought_hashes.pop(0)

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
