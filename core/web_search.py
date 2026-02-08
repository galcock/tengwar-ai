"""
Tengwar AI — Web Search
Gives Gary access to current events and real-time information.
Uses DuckDuckGo for zero-config search.
"""
import re
import asyncio
from datetime import datetime

try:
    from duckduckgo_search import DDGS
    HAS_SEARCH = True
except ImportError:
    HAS_SEARCH = False
    print("[web_search] duckduckgo-search not installed. Run: pip3 install duckduckgo-search --break-system-packages")


# Keywords/patterns that suggest a search would help
SEARCH_TRIGGERS = [
    r'\b(who is|who are|who won|who\'s)\b',
    r'\b(what happened|what\'s happening|what is happening)\b',
    r'\b(current|latest|recent|today|tonight|yesterday|this week|this month)\b',
    r'\b(score|scores|playing|game|match|super bowl|world cup|championship)\b',
    r'\b(news|headline|breaking)\b',
    r'\b(price|stock|market|bitcoin|crypto)\b',
    r'\b(weather|forecast)\b',
    r'\b(released|launched|announced|died|elected|fired|hired)\b',
    r'\b(do you know about|have you heard|did you see|did you hear)\b',
    r'\b(search|look up|google|find out)\b',
]


def should_search(message: str) -> bool:
    """Detect if a message would benefit from a web search."""
    if not HAS_SEARCH:
        return False
    msg_lower = message.lower()
    for pattern in SEARCH_TRIGGERS:
        if re.search(pattern, msg_lower):
            return True
    return False


def extract_query(message: str) -> str:
    """Extract the best search query from the user's message."""
    # Clean up for search - remove conversational fluff
    q = message.strip()
    # Remove common prefixes
    for prefix in ['do you know ', 'can you tell me ', 'what do you think about ',
                   'have you heard about ', 'did you see ', 'did you hear about ',
                   'search for ', 'look up ', 'google ', 'find out about ']:
        if q.lower().startswith(prefix):
            q = q[len(prefix):]
    return q.strip('?!. ')


def search(query: str, max_results: int = 3) -> list[dict]:
    """Search the web and return results."""
    if not HAS_SEARCH:
        return []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return results
    except Exception as e:
        print(f"[web_search] Error: {e}")
        return []


def format_results(results: list[dict]) -> str:
    """Format search results for injection into the prompt."""
    if not results:
        return ""
    lines = ["Web search results:"]
    for i, r in enumerate(results, 1):
        title = r.get('title', '')
        body = r.get('body', '')[:200]
        lines.append(f"  {i}. {title}: {body}")
    return "\n".join(lines)


def search_and_format(message: str) -> str:
    """Full pipeline: detect, search, format."""
    if not should_search(message):
        return ""
    query = extract_query(message)
    if len(query) < 3:
        return ""
    results = search(query)
    return format_results(results)
