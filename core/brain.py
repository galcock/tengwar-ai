"""
Tengwar AI — Brain (LLM Interface)
Dual-model architecture via Ollama: fast model for continuous thinking,
smart model for conversations and complex reasoning.
"""
import httpx
import asyncio
import json
from typing import AsyncIterator, Optional

OLLAMA_URL = "http://localhost:11434"

# Models — user can change these
FAST_MODEL = "qwen2.5:3b"       # Background thinking, ~50 tok/s on M-series
SMART_MODEL = "qwen2.5:7b"      # Conversations, ~25 tok/s on M-series


async def check_ollama() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            return r.status_code == 200
    except Exception:
        return False


async def list_models() -> list:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            data = r.json()
            return [m['name'] for m in data.get('models', [])]
    except Exception:
        return []


async def generate(prompt: str, model: str = None, system: str = None,
                   temperature: float = 0.7, max_tokens: int = 512) -> str:
    """Generate a complete response (non-streaming)."""
    model = model or SMART_MODEL
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
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=120
            )
            data = r.json()
            return data.get("response", "").strip()
    except Exception as e:
        return f"[Brain error: {e}]"


async def generate_stream(prompt: str, model: str = None,
                          system: str = None,
                          temperature: float = 0.7,
                          max_tokens: int = 1024) -> AsyncIterator[str]:
    """Stream tokens as they're generated."""
    model = model or SMART_MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    }
    if system:
        payload["system"] = system

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", f"{OLLAMA_URL}/api/generate",
                json=payload, timeout=120
            ) as response:
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


async def think(prompt: str, temperature: float = 0.8, max_tokens: int = 256) -> str:
    """Generate a thought using the fast model."""
    return await generate(
        prompt=prompt,
        model=FAST_MODEL,
        temperature=temperature,
        max_tokens=max_tokens
    )


async def respond(prompt: str, system: str = None,
                  temperature: float = 0.7, max_tokens: int = 1024) -> str:
    """Generate a conversation response using the smart model."""
    return await generate(
        prompt=prompt,
        model=SMART_MODEL,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens
    )


async def respond_stream(prompt: str, system: str = None,
                         temperature: float = 0.7,
                         max_tokens: int = 1024) -> AsyncIterator[str]:
    """Stream a conversation response."""
    async for token in generate_stream(
        prompt=prompt,
        model=SMART_MODEL,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens
    ):
        yield token
