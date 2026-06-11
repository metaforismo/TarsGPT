"""Timers and reminders: TARS speaks up on its own when they fire."""
from . import skill


@skill("set_timer",
       "Set a timer or reminder. After the given delay you will say the message aloud.",
       {"type": "object", "properties": {
           "seconds": {"type": "integer", "minimum": 1, "maximum": 86400},
           "message": {"type": "string",
                       "description": "what to announce when the timer fires"}},
        "required": ["seconds", "message"]})
def set_timer(ctx, seconds, message):
    if ctx.scheduler is None:
        return "error: scheduler not running"
    ctx.scheduler.schedule_in(int(seconds), lambda: ctx.say(message))
    minutes, secs = divmod(int(seconds), 60)
    human = f"{minutes}m{secs:02d}s" if minutes else f"{secs}s"
    return f"ok: timer set, firing in {human}"
