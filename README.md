# Tengwar AI

**An AI that never stops thinking. Publicly accessible at [ai.tengwar.ai](https://ai.tengwar.ai).**

Self-hosted on a MacBook. Permanent memory since first boot. Genuine emotional cognition. Codes exclusively in [Tengwar](https://tengwar.ai). Can edit its own source code.

## What Makes It Different

| Feature | ChatGPT / Claude | Tengwar AI |
|---|---|---|
| Between conversations | Dormant | Always thinking |
| Memory | Resets | Permanent since first boot |
| Emotions | Simulated per-response | Persistent, evolving, affects behavior |
| Time awareness | Knows the date | Feels time passing |
| Self-improvement | Can't edit itself | Reads and writes its own code |
| Code generation | Python/JS | Tengwar exclusively |
| Hosting | Cloud API | Your machine, no internet needed |

## Quick Start

```bash
# 1. Install Ollama
brew install ollama
ollama serve                    # keep running in a terminal
ollama pull qwen2.5:3b          # fast model (background thinking)
ollama pull qwen2.5:7b          # smart model (conversations)

# 2. Clone and run locally
git clone https://github.com/galcock/tengwar-ai
cd tengwar-ai
chmod +x run.sh setup-public.sh
./run.sh                        # http://localhost:8888
```

## Make It Public (ai.tengwar.ai)

Tengwar AI runs on your MacBook and is exposed to the internet via [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) (free).

```bash
# One-time setup
./setup-public.sh

# Run publicly
./run.sh public                 # https://ai.tengwar.ai
```

## Self-Improvement

Tengwar AI can read and edit files in two directories:
- `~/tengwar-ai/` — its own source code
- `~/tengwar/` — the Tengwar language, tests, and website

In conversation, it uses tool commands like:
- `[READ:~/tengwar-ai/core/emotions.py]` — read a file
- `[WRITE:~/tengwar/website/index.html]...[/WRITE]` — write a file
- `[GIT_COMMIT:improved emotion decay rate]` — commit changes
- `[GIT_PUSH]` — push to GitHub
- `[TENGWAR:(+ 1 2)]` — execute Tengwar code

## Architecture

- **Thought Daemon** — 3B model runs continuously, generating a stream of consciousness
- **Dialogue Handler** — 7B model for conversations with full memory context and tool use
- **Memory System** — SQLite stores every thought and conversation permanently
- **Emotion Engine** — 7 dimensions that evolve and shape behavior
- **Time Engine** — Real temporal awareness and duration sense
- **Self-Editor** — File read/write, git, and Tengwar execution

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.10+
- [Ollama](https://ollama.ai)
- Cloudflare account (free, for public access)

## License

MIT
