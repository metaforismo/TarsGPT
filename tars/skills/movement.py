"""Body movement and choreographed sequence skills."""
from . import skill
from ..movement import sequences


@skill("move",
       "Move your physical body. Use when asked to walk, turn, pose or stand straight.",
       {"type": "object", "properties": {
           "action": {"type": "string",
                      "enum": ["step_forward", "turn_left", "turn_right", "pose", "neutral"]},
           "repeat": {"type": "integer", "minimum": 1, "maximum": 10, "default": 1},
       }, "required": ["action"]})
def move(ctx, action, repeat=1):
    if ctx.gaits is None:
        return "error: no servo hardware attached"
    for _ in range(int(repeat)):
        getattr(ctx.gaits, action)()
    return f"ok: executed {action} x{repeat}"


@skill("perform",
       "Perform a named choreographed movement sequence (greet, wiggle, patrol, "
       "or any custom one). Use when asked to dance, greet, patrol or show off.",
       {"type": "object", "properties": {"name": {"type": "string"}},
        "required": ["name"]})
def perform(ctx, name):
    if ctx.gaits is None:
        return "error: no servo hardware attached"
    return sequences.perform(name, ctx.gaits)
