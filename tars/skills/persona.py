"""Self-adjustable personality skill."""
from . import skill


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
