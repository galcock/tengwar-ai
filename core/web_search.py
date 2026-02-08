"""
Tengwar AI — Web Search
Gives Gary access to current events and real-time information.
Uses DuckDuckGo HTML search via httpx (no extra package needed).
"""
import re
import httpx
from datetime import datetime

# Keywords/patterns that suggest a search would help
SEARCH_TRIGGERS = [
    r'\b(who is|who are|who won|who\'s playing|whos playing)\b',
    r'\b(what happened|what\'s happening)\b',
    r'\b(current|latest|recent|today|tonight|yesterday|this week)\b',
    r'\b(score|scores|playing|game|match|super bowl|world cup|championship|nfl|nba)\b',
    r'\b(news|headline|breaking)\b',
    r'\b(price|stock|market|bitcoin|crypto)\b',
    r'\b(weather|forecast)\b',
    r'\b(released|launched|announced|died|elected)\b',
    r'\b(do you know about|have you heard|did you see|did you hear)\b',
    r'\b(search|look up|look it up|google|find out)\b',
    r'\b(president|prime minister|ceo|governor|mayor)\b',
]


def should_search(message: str) -> bool:
    """Detect if a message would benefit from a web search."""
    msg_lower = message.lower()
    for pattern in SEARCH_TRIGGERS:
        if re.search(pattern, msg_lower):
            return True
    return False


def extract_query(message: str) -> str:
    """Extract the best search query from the user's message."""
    q = message.strip()
    for prefix in ['do you know ', 'can you tell me ', 'what do you think about ',
                   'have you heard about ', 'did you see ', 'did you hear about ',
                   'search for ', 'look up ', 'google ', 'find out about ']:
        if q.lower().startswith(prefix):
            q = q[len(prefix):]
    q = q.strip('?!. ')
    # Add current date context for time-sensitive queries
    today = datetime.now().strftime("%B %Y")
    year = datetime.now().strftime("%Y")
    time_words = ['today', 'tonight', 'current', 'latest', 'now', 'this week', 'score']
    leadership_words = ['president', 'prime minister', 'ceo', 'governor', 'mayor', 'who is']
    if any(w in q.lower() for w in time_words):
        q = f"{q} {today}"
    elif any(w in q.lower() for w in leadership_words):
        q = f"{q} {year}"
    return q


def search(query: str, max_results: int = 3) -> list[dict]:
    """Search via DuckDuckGo HTML (no API key, no extra package)."""
    try:
        url = "https://html.duckduckgo.com/html/"
        resp = httpx.post(url, data={"q": query}, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        }, timeout=5.0)
        if resp.status_code != 200:
            print(f"[web_search] HTTP {resp.status_code}")
            return []

        # Parse results from HTML
        results = []
        text = resp.text
        # Find result snippets
        import re as _re
        blocks = _re.findall(r'<a rel="nofollow" class="result__a".*?>(.*?)</a>.*?<a class="result__snippet".*?>(.*?)</a>', text, _re.DOTALL)
        for title_html, snippet_html in blocks[:max_results]:
            title = _re.sub(r'<.*?>', '', title_html).strip()
            snippet = _re.sub(r'<.*?>', '', snippet_html).strip()
            if title and snippet:
                results.append({"title": title, "body": snippet})

        print(f"[web_search] Query: '{query}' -> {len(results)} results")
        return results

    except Exception as e:
        print(f"[web_search] Error: {e}")
        return []


def format_results(results: list[dict]) -> str:
    """Format search results as direct facts for the model."""
    if not results:
        return ""
    lines = []
    for r in results:
        title = r.get('title', '')
        body = r.get('body', '')[:300]
        lines.append(f"- {title}: {body}")
    return "\n".join(lines)


def search_and_format(message: str, conversation_context: str = "") -> str:
    """Full pipeline: detect, search, format."""
    msg_lower = message.lower().strip()

    # Handle "look it up" style commands - use conversation context
    look_phrases = ['look it up', 'look it up!', 'look it up...', 'search it',
                    'google it', 'look it up bro', 'just look it up']
    if msg_lower.rstrip('!. ') in look_phrases or msg_lower in look_phrases:
        if conversation_context:
            query = extract_query(conversation_context)
            if len(query) >= 3:
                print(f"[web_search] Context search: '{query}'")
                results = search(query)
                return format_results(results)
        return ""

    if not should_search(message):
        print(f"[web_search] No trigger for: '{message[:50]}'")
        return ""
    query = extract_query(message)
    if len(query) < 3:
        return ""
    print(f"[web_search] Searching: '{query}'")
    results = search(query)
    formatted = format_results(results)
    if formatted:
        print(f"[web_search] Injecting {len(results)} results into prompt")
    else:
        print(f"[web_search] No results found")
    return formatted
