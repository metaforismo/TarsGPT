"""Voice enrollment skill: teach TARS who is speaking."""
from . import skill


@skill("enroll_speaker",
       "Learn the current speaker's voice. Use when someone says e.g. "
       "'learn my voice, I am Francesco'. You will listen for a few seconds.",
       {"type": "object", "properties": {"name": {"type": "string"}},
        "required": ["name"]})
def enroll_speaker(ctx, name):
    sid = ctx.extras.get("speaker_id")
    if sid is None or not sid.available:
        return "error: speaker identification unavailable (numpy not installed)"
    from .. import audio
    ctx.say(f"Listening. {name}, please speak naturally for a few seconds.")
    wav = audio.record_until_silence()
    if wav is None:
        return "error: no microphone audio captured"
    import os
    try:
        ok = sid.enroll(name, wav)
    finally:
        os.unlink(wav)
    return f"ok: enrolled {name}" if ok else "error: sample too short, try again"
