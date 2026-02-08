"""
Tengwar AI — Brain (LLM Interface)
Dual-backend architecture:
  - Claude Haiku (Anthropic API) for conversations — smart, follows instructions
  - Ollama local model for background thinking — fast, free, always running
"""
import httpx
import asyncio
import json
import os
from typing import AsyncIterator, Optional
from pathlib import Path

OLLAMA_URL = "http://localhost:11434"

# Load config
_config_path = Path(__file__).parent.parent / "config.json"
_config = {}
if _config_path.exists():
    with open(_config_path) as f:
        _config = json.load(f)

# API config
ANTHROPIC_API_KEY = _config.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
CONVERSATION_MODEL = _config.get("conversation_model", "claude-haiku-4-5-20251001")
THOUGHT_MODEL = _config.get("thought_model", "qwen2.5:3b")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# Backwards-compatible aliases for server.py
FAST_MODEL = THOUGHT_MODEL
SMART_MODEL = CONVERSATION_MODEL

def _has_api_key():
    return bool(ANTHROPIC_API_KEY) and ANTHROPIC_API_KEY != "YOUR_API_KEY_HERE"


# --- Ollama (local, for thoughts) ---

async def check_ollama():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            return r.status_code == 200
    except Exception:
        return False


async def list_models():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            data = r.json()
            return [m['name'] for m in data.get('models', [])]
    except Exception:
        return []


async def ollama_generate(prompt, model=None, system=None,
                          temperature=0.7, max_tokens=512):
    model = model or THOUGHT_MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    }
    if system:
        payload["system"] = system
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
            data = r.json()
            return data.get("response", "").strip()
    except Exception as e:
        return f"[Brain error: {e}]"


async def ollama_stream(prompt, model=None, system=None,
                        temperature=0.7, max_tokens=1024):
    model = model or "qwen2.5:7b"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": max_tokens}
    }
    if system:
        payload["system"] = system
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{OLLAMA_URL}/api/generate",
                                     json=payload, timeout=120) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done"):
                            break
    except Exception as e:
        yield f"[Brain error: {e}]"


# --- Anthropic API (for conversations) ---

async def anthropic_generate(prompt, system=None, temperature=0.7, max_tokens=1024):
    if not _has_api_key():
        print("[brain] No API key. Falling back to Ollama.")
        return await ollama_generate(prompt, model="qwen2.5:7b", system=system,
                                     temperature=temperature, max_tokens=max_tokens)
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": CONVERSATION_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=30)
            if r.status_code != 200:
                print(f"[brain] API error {r.status_code}: {r.text[:200]}")
                return await ollama_generate(prompt, model="qwen2.5:7b", system=system,
                                             temperature=temperature, max_tokens=max_tokens)
            data = r.json()
            text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")
            return text.strip()
    except Exception as e:
        print(f"[brain] API error: {e}. Falling back to Ollama.")
        return await ollama_generate(prompt, model="qwen2.5:7b", system=system,
                                     temperature=temperature, max_tokens=max_tokens)


async def anthropic_stream(prompt, system=None, temperature=0.7, max_tokens=1024):
    if not _has_api_key():
        print("[brain] No API key. Falling back to Ollama stream.")
        async for token in ollama_stream(prompt, system=system,
                                         temperature=temperature, max_tokens=max_tokens):
            yield token
        return

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": CONVERSATION_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", ANTHROPIC_URL,
                                     headers=headers, json=payload, timeout=60) as response:
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        evt = data.get("type", "")
                        if evt == "content_block_delta":
                            text = data.get("delta", {}).get("text", "")
                            if text:
                                yield text
                        elif evt == "message_stop":
                            break
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"[brain] Stream error: {e}. Falling back to Ollama.")
        async for token in ollama_stream(prompt, system=system,
                                         temperature=temperature, max_tokens=max_tokens):
            yield token


# --- Public API ---

async def think(prompt, temperature=0.8, max_tokens=256):
    """Thought daemon — local Ollama, fast and free."""
    return await ollama_generate(prompt=prompt, model=THOUGHT_MODEL,
                                temperature=temperature, max_tokens=max_tokens)


async def respond(prompt, system=None, temperature=0.7, max_tokens=1024):
    """Conversation — Claude Haiku via API."""
    return await anthropic_generate(prompt=prompt, system=system,
                                    temperature=temperature, max_tokens=max_tokens)


async def respond_stream(prompt, system=None, temperature=0.7, max_tokens=1024):
    """Streaming conversation — Claude Haiku via API."""
    async for token in anthropic_stream(prompt=prompt, system=system,
                                        temperature=temperature, max_tokens=max_tokens):
        yield token
