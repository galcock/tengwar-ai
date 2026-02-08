#!/bin/bash
# Tengwar AI — Setup API Key
# Run this once to configure your Anthropic API key

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║     TENGWAR AI — API Setup           ║"
echo "  ║   Claude Haiku for conversations     ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

if [ -f config.json ] && grep -q "sk-ant-" config.json 2>/dev/null; then
    echo "API key already configured."
    echo "To change it, edit config.json directly."
    exit 0
fi

echo "Get your API key from: https://console.anthropic.com/settings/keys"
echo ""
read -p "Paste your Anthropic API key: " API_KEY

if [ -z "$API_KEY" ]; then
    echo "No key entered. Exiting."
    exit 1
fi

cat > config.json << EOF
{
    "anthropic_api_key": "$API_KEY",
    "conversation_model": "claude-haiku-4-5-20251001",
    "thought_model": "qwen2.5:3b",
    "thought_backend": "ollama"
}
EOF

echo ""
echo "Config saved to config.json"
echo "Conversations: Claude Haiku (API)"
echo "Thoughts: qwen2.5:3b (local Ollama)"
echo ""
echo "Run ./run.sh public to start."
