"""Knowledge graph skills: structured facts the LLM can store and query."""
from . import skill


def _kg(ctx):
    return ctx.extras.get("knowledge")


@skill("learn_fact",
       "Store a structured fact as subject/relation/object, e.g. "
       "('Francesco', 'owns', 'a Bambu Lab P1S'). Prefer this over 'remember' "
       "for facts about specific people or things.",
       {"type": "object", "properties": {
           "subject": {"type": "string"},
           "relation": {"type": "string"},
           "object": {"type": "string"}},
        "required": ["subject", "relation", "object"]})
def learn_fact(ctx, subject, relation, object):
    kg = _kg(ctx)
    if kg is None:
        return "error: knowledge graph not running"
    added = kg.add(subject, relation, object)
    return "ok: learned" if added else "ok: already knew that"


@skill("query_facts",
       "Look up structured facts about an entity (a person, object or place).",
       {"type": "object", "properties": {"entity": {"type": "string"}},
        "required": ["entity"]})
def query_facts(ctx, entity):
    kg = _kg(ctx)
    if kg is None:
        return "error: knowledge graph not running"
    facts = kg.about(entity)
    return kg.render(facts) if facts else f"no facts known about {entity}"


@skill("forget_facts",
       "Delete all stored facts about a subject, when asked to forget.",
       {"type": "object", "properties": {"subject": {"type": "string"}},
        "required": ["subject"]})
def forget_facts(ctx, subject):
    kg = _kg(ctx)
    if kg is None:
        return "error: knowledge graph not running"
    removed = kg.forget(subject)
    return f"ok: forgot {removed} fact(s) about {subject}"
