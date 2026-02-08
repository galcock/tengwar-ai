#!/bin/bash
# Tengwar AI — Public Access Setup
# Makes your local Tengwar AI accessible at ai.tengwar.ai
#
# Uses Cloudflare Tunnel (free) to expose localhost:8888 to the internet.
# Your MacBook stays the server — no cloud hosting needed.

set -e

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║    TENGWAR AI — Public Access Setup   ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# Step 1: Install cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing Cloudflare Tunnel (cloudflared)..."
    brew install cloudflared
else
    echo "✅ cloudflared already installed"
fi

# Step 2: Check if logged in
echo ""
echo "🔑 Cloudflare login required (one-time setup)."
echo "   This opens a browser — log in with your Cloudflare account."
echo "   If you don't have one, sign up free at cloudflare.com"
echo ""
read -p "   Press Enter to continue..."
cloudflared tunnel login

# Step 3: Create tunnel
TUNNEL_NAME="tengwar-ai"
echo ""
echo "🚇 Creating tunnel '${TUNNEL_NAME}'..."
cloudflared tunnel create ${TUNNEL_NAME} 2>/dev/null || echo "   (tunnel may already exist)"

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep ${TUNNEL_NAME} | awk '{print $1}')
echo "   Tunnel ID: ${TUNNEL_ID}"

# Step 4: Create config
CONFIG_DIR="$HOME/.cloudflared"
mkdir -p ${CONFIG_DIR}

cat > ${CONFIG_DIR}/config.yml << EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${CONFIG_DIR}/${TUNNEL_ID}.json

ingress:
  - hostname: ai.tengwar.ai
    service: http://localhost:8888
  - service: http_status:404
EOF

echo "✅ Config written to ${CONFIG_DIR}/config.yml"

# Step 5: DNS setup instructions
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 MANUAL STEP — Add DNS record:"
echo ""
echo "   If tengwar.ai uses Cloudflare DNS:"
echo "   Run: cloudflared tunnel route dns ${TUNNEL_NAME} ai.tengwar.ai"
echo ""
echo "   If tengwar.ai uses another DNS provider:"
echo "   Add a CNAME record:"
echo "     Name:   ai"
echo "     Target: ${TUNNEL_ID}.cfargotunnel.com"
echo "     TTL:    Auto"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 To start Tengwar AI publicly:"
echo ""
echo "   Terminal 1:  cd ~/tengwar-ai && python3 server.py"
echo "   Terminal 2:  cloudflared tunnel run tengwar-ai"
echo ""
echo "   Then visit: https://ai.tengwar.ai"
echo ""
