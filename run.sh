#!/bin/bash
# Tengwar AI — Start Script
# Run: ./run.sh

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
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found."
    echo "   Install: brew install ollama"
    echo "   Then:    ollama serve"
    echo ""
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running."
    echo "   Start:   ollama serve"
    echo "   Pull:    ollama pull qwen2.5:3b"
    echo "           ollama pull qwen2.5:7b"
    echo ""
    echo "   Starting anyway — chat will be unavailable until Ollama is running."
    echo ""
fi

# Install dependencies
echo "📦 Checking dependencies..."
pip3 install -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt 2>/dev/null

# Create data dir
mkdir -p data

echo ""
echo "🧠 Starting Tengwar AI..."
echo "🌐 Open http://localhost:8888 in your browser"
echo ""

# Run server
python3 server.py
