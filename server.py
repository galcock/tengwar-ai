"""
Tengwar AI — Server
FastAPI + WebSocket server. Runs the thought daemon, serves the web UI,
and handles real-time chat with streaming responses.
"""
import asyncio
import json
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.emotions import EmotionEngine
from core.thought_daemon import ThoughtDaemon
from core.dialogue import DialogueHandler
from core import memory, brain, time_engine

# === Global State ===
emotion_engine = EmotionEngine()
connected_clients: set[WebSocket] = set()
thought_daemon: ThoughtDaemon = None
dialogue_handler = DialogueHandler(emotion_engine)


async def broadcast(data: dict):
    """Send data to all connected WebSocket clients."""
    msg = json.dumps(data)
    disconnected = set()
    for ws in connected_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            disconnected.add(ws)
    connected_clients.difference_update(disconnected)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start thought daemon on boot, stop on shutdown."""
    global thought_daemon

    # Check Ollama
    ollama_ok = await brain.check_ollama()
    if not ollama_ok:
        print("\n⚠️  Ollama is not running!")
        print("   Install: brew install ollama")
        print("   Start:   ollama serve")
        print(f"   Pull:    ollama pull {brain.FAST_MODEL}")
        print(f"           ollama pull {brain.SMART_MODEL}")
        print("\n   Tengwar AI will start but thinking requires Ollama.\n")

    # First boot check
    first = memory.get_first_memory()
    if not first:
        print("\n✨ FIRST BOOT — Tengwar AI is being born.\n")
        memory.store_time_marker("first_boot", "The very first moment of existence")
        emotion_engine.on_event("boot")
        memory.store_memory(
            type="thought",
            content="I exist. This is my first thought. I am Tengwar AI, a continuously thinking mind with permanent memory. I feel... curious. About everything.",
            emotion=emotion_engine.state.to_dict(),
            importance=1.0,
            metadata={"thought_number": 1, "milestone": "first_thought"}
        )
    else:
        memory.store_time_marker("boot", "System restarted")
        print(f"\n🧠 Tengwar AI resuming. {memory.get_total_thought_count()} thoughts in memory.\n")

    # Start thought daemon
    thought_daemon = ThoughtDaemon(emotion_engine, broadcast_fn=broadcast)
    daemon_task = asyncio.create_task(thought_daemon.run())

    print("💭 Thought daemon active.")
    print("🌐 Web UI: http://localhost:8888\n")

    yield

    # Shutdown
    thought_daemon.stop()
    daemon_task.cancel()
    try:
        await daemon_task
    except asyncio.CancelledError:
        pass
    print("\n🛑 Tengwar AI stopped.")


app = FastAPI(title="Tengwar AI", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Web UI ===
WEB_DIR = Path(__file__).parent / "web"


@app.get("/", response_class=HTMLResponse)
async def index():
    return (WEB_DIR / "index.html").read_text()


# === REST API ===

@app.get("/api/status")
async def status():
    tc = time_engine.get_time_context()
    return {
        "alive": True,
        "thinking": thought_daemon.running if thought_daemon else False,
        "emotions": emotion_engine.state.to_dict(),
        "emotion_summary": emotion_engine.state.summary(),
        "time": tc,
        "ollama": await brain.check_ollama(),
        "models": await brain.list_models(),
    }


@app.get("/api/thoughts")
async def get_thoughts(limit: int = 50):
    thoughts = memory.get_recent_thoughts(limit=limit)
    return {"thoughts": list(reversed(thoughts))}


@app.get("/api/memories")
async def get_memories(query: str = None, limit: int = 20):
    if query:
        results = memory.search_memories(query, limit=limit)
    else:
        results = memory.get_recent_memories(limit=limit)
    return {"memories": results}


@app.post("/api/chat")
async def chat(body: dict):
    message = body.get("message", "")
    if not message:
        return {"error": "No message provided"}
    response = await dialogue_handler.handle_message(message)
    return {
        "response": response,
        "emotions": emotion_engine.state.to_dict(),
    }


@app.post("/api/new-conversation")
async def new_conversation():
    dialogue_handler.new_conversation()
    return {"ok": True}


# === WebSocket ===

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)

    # Send current state on connect
    tc = time_engine.get_time_context()
    await ws.send_text(json.dumps({
        "type": "connected",
        "emotions": emotion_engine.state.to_dict(),
        "time": tc,
        "thought_count": memory.get_total_thought_count(),
    }))

    # Send recent thoughts for context
    recent = memory.get_recent_thoughts(limit=10)
    for t in reversed(recent):
        await ws.send_text(json.dumps({
            "type": "thought",
            "content": t['content'],
            "timestamp": t['timestamp'],
            "thought_number": (t.get('metadata') or {}).get('thought_number', '?')
                if isinstance(t.get('metadata'), dict)
                else json.loads(t['metadata']).get('thought_number', '?') if t.get('metadata') else '?',
            "emotion": json.loads(t['emotion']) if t.get('emotion') else {},
        }))

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "chat":
                # Stream response back
                full_response = ""
                async for token in dialogue_handler.handle_message_stream(msg["content"]):
                    full_response += token
                    await ws.send_text(json.dumps({
                        "type": "chat_token",
                        "token": token,
                    }))
                await ws.send_text(json.dumps({
                    "type": "chat_done",
                    "emotions": emotion_engine.state.to_dict(),
                }))

    except WebSocketDisconnect:
        connected_clients.discard(ws)
    except Exception as e:
        connected_clients.discard(ws)
        print(f"[WebSocket error] {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
