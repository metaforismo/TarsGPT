"""Self-adjustable personality and switchable character cards."""
from . import skill
from .. import characters


@skill("set_personality",
       "Adjust your own humor/honesty/sarcasm settings (0-100) when the user asks.",
       {"type": "object", "properties": {
           "humor": {"type": "integer"}, "honesty": {"type": "integer"},
           "sarcasm": {"type": "integer"}}})
def set_personality(ctx, humor=None, honesty=None, sarcasm=None):
    s = ctx.settings
    for key, value in (("humor", humor), ("honesty", honesty), ("sarcasm", sarcasm)):
        if value is not None:
            setattr(s, key, max(0, min(100, int(value))))
    s.save()
    return f"ok: humor={s.humor} honesty={s.honesty} sarcasm={s.sarcasm}"


@skill("set_character",
       "Switch to another character card (e.g. when asked to 'become CASE'). "
       "Changes your name, persona and default personality dials.",
       {"type": "object", "properties": {"name": {"type": "string"}},
        "required": ["name"]})
def set_character(ctx, name):
    if characters.apply_character(name, ctx.settings):
        return f"ok: now operating as {ctx.settings.robot_name}"
    available = ", ".join(characters.list_characters()) or "(none installed)"
    return f"error: unknown character '{name}'. Available: {available}"
