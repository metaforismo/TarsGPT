"""Web search skill: quick factual lookups with no API key.

Tries DuckDuckGo's Instant Answer API first (abstracts, definitions),
then falls back to Wikipedia's REST summary. Both are stable, keyless
public APIs - this is for "who is / what is / when did" questions, not
deep research.
"""
import json
import urllib.parse
import urllib.request
from . import skill

TIMEOUT = 8
UA = {"User-Agent": "TarsGPT/1.x (https://github.com/metaforismo/TarsGPT)"}


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.load(response)


def _duckduckgo(query: str) -> str | None:
    data = _get_json("https://api.duckduckgo.com/?format=json&no_html=1&q="
                     + urllib.parse.quote(query))
    abstract = data.get("AbstractText") or data.get("Answer") \
        or data.get("Definition")
    if abstract:
        source = data.get("AbstractSource") or data.get("DefinitionSource") or ""
        return f"{abstract}" + (f" (source: {source})" if source else "")
    for topic in data.get("RelatedTopics", []):
        if isinstance(topic, dict) and topic.get("Text"):
            return topic["Text"]
    return None


def _wikipedia(query: str) -> str | None:
    hits = _get_json("https://en.wikipedia.org/w/api.php?action=opensearch"
                     "&limit=1&format=json&search=" + urllib.parse.quote(query))
    if not (len(hits) > 1 and hits[1]):
        return None
    title = hits[1][0]
    page = _get_json("https://en.wikipedia.org/api/rest_v1/page/summary/"
                     + urllib.parse.quote(title))
    extract = page.get("extract")
    return f"{extract} (source: Wikipedia)" if extract else None


@skill("web_search",
       "Look up a current or factual topic on the web (people, places, "
       "events, definitions). Use when you are unsure or the user asks "
       "about something after your knowledge.",
       {"type": "object", "properties": {"query": {"type": "string"}},
        "required": ["query"]})
def web_search(ctx, query):
    for backend in (_duckduckgo, _wikipedia):
        try:
            result = backend(query)
            if result:
                return result[:900]
        except Exception:
            continue
    return f"error: no result found for '{query}' (network down?)"
