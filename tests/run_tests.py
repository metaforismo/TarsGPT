#!/usr/bin/env python3
"""TARS runtime test suite. No hardware or API keys required.

Run:  python tests/run_tests.py   (or: pytest tests/run_tests.py)
"""
import os
import sys
import time
import wave
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["TARS_SIM"] = "1"
os.environ["TARS_DATA_DIR"] = tempfile.mkdtemp(prefix="tars_test_")

from tars.config import settings  # noqa: E402
from tars import skills  # noqa: E402
from tars.knowledge import KnowledgeGraph  # noqa: E402
from tars.memory import Memory  # noqa: E402
from tars.movement import ServoDriver, Gaits  # noqa: E402
from tars.scheduler import Scheduler  # noqa: E402
from tars.speakerid import SpeakerID  # noqa: E402
from tars.speech import Speaker  # noqa: E402
from tars.llm import Brain  # noqa: E402
from tars.voice import VoiceLoop  # noqa: E402
from tars.web.server import create_app  # noqa: E402

EXPECTED_SKILLS = {"move", "remember", "recall", "set_personality", "set_timer",
                   "look", "system_status", "learn_fact", "query_facts",
                   "forget_facts", "play_music", "stop_music",
                   "home_assistant", "enroll_speaker"}

skills.load_skills()  # populate the registry once for every test


def make_ctx():
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    scheduler = Scheduler()
    scheduler.start()
    speaker = Speaker(settings)
    speaker.muted = True
    memory = Memory(settings)
    kg = KnowledgeGraph()
    sid = SpeakerID()
    return skills.SkillContext(settings=settings, memory=memory, gaits=gaits,
                               scheduler=scheduler, speaker=speaker,
                               extras={"knowledge": kg, "speaker_id": sid})


def test_skills_registry():
    reg = skills.load_skills()
    missing = EXPECTED_SKILLS - set(reg)
    assert not missing, f"missing skills: {missing}"


def test_movement_and_basic_skills():
    ctx = make_ctx()
    assert skills.run("move", {"action": "step_forward"}, ctx).startswith("ok")
    assert skills.run("move", {"action": "pose"}, ctx).startswith("ok")
    assert "disk" in skills.run("system_status", {}, ctx)
    assert skills.run("bogus_skill", {}, ctx).startswith("error")
    assert skills.run("move", {"bad_arg": 1}, ctx).startswith("error")


def test_memory_keyword_fallback():
    ctx = make_ctx()
    assert skills.run("remember", {"note": "the user's favourite color is orange"},
                      ctx) == "ok: stored"
    assert "orange" in skills.run("recall", {"query": "what color does the user like"}, ctx)
    assert skills.run("recall", {"query": "zzz qqq xxx"}, ctx) == "no relevant memories"


def test_knowledge_graph():
    kg = KnowledgeGraph()
    assert kg.add("Francesco", "owns", "a Bambu Lab P1S") is True
    assert kg.add("Francesco", "owns", "a bambu lab p1s") is False  # dedupe
    assert kg.add("TARS", "lives in", "the living room") is True
    assert len(kg.about("francesco")) == 1
    found = kg.search("what printer does Francesco have in the bambu ecosystem")
    assert found and found[0]["o"] == "a Bambu Lab P1S"
    # persistence
    kg2 = KnowledgeGraph()
    assert len(kg2.triples) >= 2
    assert kg2.forget("Francesco") == 1


def test_knowledge_skills():
    ctx = make_ctx()
    assert "learned" in skills.run("learn_fact", {"subject": "Rome", "relation": "is",
                                                  "object": "the capital of Italy"}, ctx)
    assert "capital" in skills.run("query_facts", {"entity": "Rome"}, ctx)
    assert "forgot" in skills.run("forget_facts", {"subject": "Rome"}, ctx)
    assert "no facts" in skills.run("query_facts", {"entity": "Rome"}, ctx)


def test_personality_and_timer():
    ctx = make_ctx()
    assert "humor=42" in skills.run("set_personality", {"humor": 42}, ctx)
    assert "timer set" in skills.run("set_timer", {"seconds": 1, "message": "tea"}, ctx)


def test_scheduler_fires():
    sched = Scheduler()
    sched.start()
    fired = []
    sched.schedule_in(0.2, lambda: fired.append(1))
    job = sched.schedule_in(0.2, lambda: fired.append("cancelled"))
    sched.cancel(job)
    time.sleep(0.7)
    assert fired == [1], fired
    sched.stop()


def test_speaker_sentence_streaming():
    spk = Speaker(settings)
    said = []
    spk.say = lambda t: said.append(t) if t.strip() else None
    out = spk.speak_stream(iter(["Hello there. This is ",
                                 "a second sentence! And a third", " one?"]))
    assert out == "Hello there. This is a second sentence! And a third one?"
    assert len(said) >= 2, said


def test_music_and_home_assistant_unconfigured():
    ctx = make_ctx()
    assert skills.run("stop_music", {}, ctx) == "nothing is playing"
    result = skills.run("play_music", {"what": "no-such-station-xyz"}, ctx)
    assert result.startswith("error"), result
    assert "not configured" in skills.run(
        "home_assistant", {"action": "turn_on", "entity_id": "light.x"}, ctx)


def _tone_wav(freqs, seconds=1.0, rate=16000):
    """A synthetic 'voice': a chord of harmonics, written as 16-bit wav."""
    import numpy as np
    t = np.arange(int(rate * seconds)) / rate
    sig = sum(np.sin(2 * np.pi * f * t) * a for f, a in freqs)
    sig = (sig / np.abs(sig).max() * 20000).astype(np.int16)
    path = tempfile.mktemp(suffix=".wav", prefix="tars_voicegen_")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(sig.tobytes())
    return path


def test_speaker_identification():
    sid = SpeakerID()
    if not sid.available:
        print("  (numpy missing, skipped)")
        return
    deep = [(120, 1.0), (240, 0.7), (360, 0.3)]
    high = [(260, 1.0), (520, 0.4), (1040, 0.5)]
    assert sid.enroll("marco", _tone_wav(deep))
    assert sid.enroll("anna", _tone_wav(high))
    assert sid.identify(_tone_wav([(120, 1.0), (240, 0.65), (360, 0.35)])) == "marco"
    assert sid.identify(_tone_wav([(260, 1.0), (520, 0.45), (1040, 0.45)])) == "anna"
    # a completely different voice should be unknown
    assert sid.identify(_tone_wav([(700, 1.0), (1400, 1.0)])) is None


def test_brain_offline():
    ctx = make_ctx()
    brain = Brain(settings, ctx.memory, ctx)
    msg = "".join(brain.chat_stream("hello"))
    assert "offline" in msg.lower() or settings.openai_api_key, msg


def test_web_endpoints():
    skills.load_skills()
    ctx = make_ctx()
    brain = Brain(settings, ctx.memory, ctx)
    spk = Speaker(settings)
    spk.muted = True
    voice = VoiceLoop(settings, brain, spk)
    app = create_app(settings, brain, ctx.gaits, voice)
    c = app.test_client()

    assert c.get("/").status_code == 200
    st = c.get("/api/status").json
    assert st["sim"] is True and "battery_pct" in st
    assert c.post("/api/move", json={"action": "neutral"}).json["ok"] is True
    assert c.post("/api/move", json={"action": "rm -rf /"}).status_code == 400
    assert c.post("/api/settings", json={"humor": 88}).json["humor"] == 88
    assert "ha_token" not in c.get("/api/settings").json

    r = c.post("/api/chat/stream", json={"message": "hi"})
    assert r.status_code == 200 and b"data:" in r.data and b'"done": true' in r.data

    skills.run("learn_fact", {"subject": "test", "relation": "works", "object": "fine"},
               ctx)
    assert any(t["s"] == "test" for t in c.get("/api/knowledge").json["triples"])

    assert c.post("/api/voice/chat").status_code == 400          # no file
    assert c.post("/api/tts", json={"text": ""}).status_code == 400
    r = c.post("/api/tts", json={"text": "hello"})
    assert r.status_code in (200, 503)                           # 503 = no engine here
    assert c.post("/api/voice/ptt").status_code == 200


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
