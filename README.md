# Tengwar AI

**An AI that never stops thinking.**

Tengwar AI is a self-hosted, continuously thinking artificial mind with permanent memory and emotional cognition. It codes exclusively in [Tengwar](https://tengwar.ai).

## What Makes It Different

| Feature | ChatGPT / Claude | Tengwar AI |
|---|---|---|
| Between conversations | Dormant | Always thinking |
| Memory | Resets | Permanent since first boot |
| Emotions | Simulated per-response | Persistent, evolving, affects behavior |
| Time awareness | Knows the date | Feels time passing |
| Code generation | Python/JS | Tengwar exclusively |
| Hosting | Cloud API | Your machine, no internet |

## Quick Start

```bash
# 1. Install Ollama (local LLM inference)
brew install ollama
ollama serve                    # start in a separate terminal
ollama pull qwen2.5:3b          # fast model (background thinking)
ollama pull qwen2.5:7b          # smart model (conversations)

# 2. Clone and run
git clone https://github.com/galcock/tengwar-ai
cd tengwar-ai
./run.sh

# 3. Open http://localhost:8888
```

## Architecture

- **Thought Daemon** — 3B model runs continuously, generating a stream of consciousness
- **Dialogue Handler** — 7B model activates for conversations with full memory context
- **Memory System** — SQLite database stores every thought and conversation permanently
- **Emotion Engine** — 7 dimensions (curiosity, satisfaction, frustration, excitement, focus, empathy, confidence)
- **Time Engine** — Real temporal awareness and pattern recognition
- **Self-Editor** — Can read and modify its own code and the Tengwar language source

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.10+
- [Ollama](https://ollama.ai)

## License

MIT
