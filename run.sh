#!/bin/bash
# Tengwar AI — Start Script
# Usage:
#   ./run.sh          — local only (http://localhost:8888)
#   ./run.sh public   — local + Cloudflare Tunnel (https://ai.tengwar.ai)

set -e

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║         TENGWAR AI — v1.0            ║"
echo "  ║    Always Thinking. Always Growing.   ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 required. Install from python.org"
    exit 1
fi

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running."
    echo "   Start in another terminal:  ollama serve"
    echo "   Then pull models:           ollama pull qwen2.5:3b && ollama pull qwen2.5:7b"
    echo ""
    echo "   Starting anyway — thinking requires Ollama."
    echo ""
fi

# Install deps if needed
pip3 install -q fastapi uvicorn httpx websockets 2>/dev/null || true

# Create data dir
mkdir -p data

if [ "$1" = "public" ]; then
    echo "🌍 Starting in PUBLIC mode (ai.tengwar.ai)"
    echo ""

    if ! command -v cloudflared &> /dev/null; then
        echo "❌ cloudflared not installed. Run: brew install cloudflared"
        echo "   Then run: ./setup-public.sh"
        exit 1
    fi

    # Start server in background
    python3 server.py &
    SERVER_PID=$!
    sleep 2

    echo "🚇 Starting Cloudflare Tunnel..."
    echo "   Public URL: https://ai.tengwar.ai"
    echo ""

    # Run tunnel (foreground — Ctrl+C stops everything)
    cloudflared tunnel run tengwar-ai

    # Cleanup on exit
    kill $SERVER_PID 2>/dev/null
else
    echo "🧠 Starting in LOCAL mode"
    echo "🌐 Open http://localhost:8888"
    echo ""
    echo "   For public access: ./run.sh public"
    echo ""
    python3 server.py
fi
