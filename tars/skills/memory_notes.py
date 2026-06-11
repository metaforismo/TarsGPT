"""Long-term memory skills: store facts and search them back explicitly."""
from . import skill


@skill("remember",
       "Store a fact about the user or the world in your long-term memory.",
       {"type": "object", "properties": {"note": {"type": "string"}},
        "required": ["note"]})
def remember(ctx, note):
    ctx.memory.add_note(note)
    return "ok: stored"


@skill("recall",
       "Search your long-term memory for facts relevant to a query. "
       "Use when you might know something but it is not in the conversation.",
       {"type": "object", "properties": {"query": {"type": "string"}},
        "required": ["query"]})
def recall(ctx, query):
    notes = ctx.memory.relevant_notes(query, k=8)
    if not notes:
        return "no relevant memories"
    return "\n".join(f"- ({n['ts']}) {n['note']}" for n in notes)
