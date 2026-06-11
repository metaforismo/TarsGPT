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
                   "home_assistant", "enroll_speaker", "perform",
                   "set_character", "set_volume", "generate_image"}

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


def test_sequences():
    ctx = make_ctx()
    assert skills.run("perform", {"name": "wiggle"}, ctx) == "ok: performed wiggle"
    result = skills.run("perform", {"name": "moonwalk"}, ctx)
    assert result.startswith("error") and "greet" in result


def test_characters():
    from tars import characters
    from tars.personality import system_prompt
    assert set(characters.list_characters()) >= {"tars", "case", "kipp"}
    ctx = make_ctx()
    assert "CASE" in skills.run("set_character", {"name": "case"}, ctx)
    assert settings.robot_name == "CASE" and settings.humor == 25
    assert "CASE" in system_prompt(settings) and "reserved" in system_prompt(settings)
    bad = skills.run("set_character", {"name": "hal9000"}, ctx)
    assert bad.startswith("error") and "kipp" in bad
    assert characters.apply_character("tars", settings)  # restore default
    assert settings.robot_name == "TARS"


def test_tts_engine_chain():
    from tars import tts
    old_engine, old_el, old_oa = settings.tts_engine, settings.elevenlabs_api_key, \
        settings.openai_api_key
    try:
        settings.tts_engine = "espeak"
        assert tts.engine_chain(settings) == ["espeak", "piper"]
        settings.tts_engine = "auto"
        settings.elevenlabs_api_key = "x"
        settings.openai_api_key = "y"
        chain = tts.engine_chain(settings)
        assert chain == ["elevenlabs", "openai", "piper", "espeak"]
        assert len(chain) == len(set(chain))  # no duplicates
    finally:
        settings.tts_engine, settings.elevenlabs_api_key = old_engine, old_el
        settings.openai_api_key = old_oa


def test_vosk_lang_and_battery_math():
    from tars.stt import vosk_lang
    from tars.skills.system import battery_percent
    assert vosk_lang("en") == "en-us"
    assert vosk_lang("it") == "it"
    assert battery_percent(12.6) == 100   # 3S full
    assert battery_percent(9.0) == 0      # 3S empty
    assert 40 < battery_percent(11.1) < 70


def test_pwm_settings_merge():
    import json
    from tars.config import Settings, SETTINGS_FILE, DATA_DIR
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps({"pwm": {"up_height": 999}}))
    fresh = Settings().load()
    assert fresh.pwm["up_height"] == 999          # stored value wins
    assert "neutral_port" in fresh.pwm            # new defaults survive
    SETTINGS_FILE.unlink()


def test_volume_and_gamepad_paths():
    ctx = make_ctx()
    result = skills.run("set_volume", {"percent": 50}, ctx)
    assert result.startswith(("ok", "error"))     # depends on mixer presence
    from tars.movement.gamepad import find_gamepad
    assert find_gamepad() is None or isinstance(find_gamepad(), str)


def test_image_generation_requires_key():
    ctx = make_ctx()
    if not settings.openai_api_key:
        assert "API key" in skills.run("generate_image", {"prompt": "a robot"}, ctx)


def test_web_auth():
    settings.web_password = "secret"
    try:
        ctx = make_ctx()
        brain = Brain(settings, ctx.memory, ctx)
        spk = Speaker(settings)
        spk.muted = True
        app = create_app(settings, brain, ctx.gaits, VoiceLoop(settings, brain, spk))
        c = app.test_client()
        remote = {"REMOTE_ADDR": "203.0.113.9"}   # simulate a LAN client
        assert c.get("/", environ_overrides=remote).status_code == 200
        assert c.get("/api/status", environ_overrides=remote).status_code == 401
        assert c.post("/api/login", json={"password": "nope"},
                      environ_overrides=remote).status_code == 403
        assert c.post("/api/login", json={"password": "secret"},
                      environ_overrides=remote).status_code == 200
        assert c.get("/api/status", environ_overrides=remote).status_code == 200
        # the robot's own kiosk screen (localhost) is always exempt
        assert c.get("/api/status").status_code == 200
    finally:
        settings.web_password = ""


def test_sweep_pair_asymmetric():
    """Both channels must land exactly on their own end value even when the
    two ranges have different lengths (asymmetric calibration)."""
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    seen = {}
    gaits.d.set_pwm = lambda ch, v: seen.__setitem__(ch, v)
    gaits._sweep_pair(1, 100, 200, 2, 500, 530, 0)   # 100 steps vs 30 steps
    assert seen[1] == 200 and seen[2] == 530, seen
    gaits._sweep_pair(1, 200, 100, 2, 530, 500, 0)   # reverse direction
    assert seen[1] == 100 and seen[2] == 500, seen
    gaits._sweep_pair(1, 50, 50, 2, 60, 60, 0)       # zero-length: no crash


def test_nudge_arm_clamped():
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    for _ in range(200):
        gaits.nudge_arm("star_main", 1)              # try to overdrive it
    assert gaits.arm["star_main"] == Gaits.SAFE_MAX
    for _ in range(400):
        gaits.nudge_arm("star_main", -1)
    assert gaits.arm["star_main"] == Gaits.SAFE_MIN


def test_skill_arg_validation_vs_crash():
    ctx = make_ctx()
    # wrong call shape -> bad arguments
    assert "bad arguments" in skills.run("move", {"bogus": 1}, ctx)
    # a TypeError raised INSIDE a handler must be reported as a crash
    @skills.skill("_crashy", "test-only")
    def _crashy(c):
        raise TypeError("internal bug")
    try:
        result = skills.run("_crashy", {}, ctx)
        assert "failed" in result and "bad arguments" not in result, result
    finally:
        skills.REGISTRY.pop("_crashy", None)


def test_knowledge_whole_word_match():
    kg = KnowledgeGraph()
    kg.add("Chrome", "is", "a web browser")
    try:
        assert kg.about("rome") == []                 # no substring bleed
        assert len(kg.about("chrome")) == 1
    finally:
        kg.forget("Chrome")


def test_character_boot_restore_keeps_dials():
    from tars import characters
    ctx = make_ctx()
    skills.run("set_character", {"name": "case"}, ctx)   # sets humor to 25
    settings.humor = 99                                   # user tunes it later
    characters.apply_character("case", settings, dials=False)  # boot restore
    assert settings.robot_name == "CASE" and settings.humor == 99
    characters.apply_character("tars", settings)          # restore default


def test_gait_optimizer_converges():
    """With a deterministic (verifiable) reward the optimizer must improve on
    the starting gait and respect the search-space bounds."""
    from tars.learn import GaitOptimizer, SimReward, SEARCH_SPACE
    reward = SimReward(noise=0.0)                 # deterministic landscape
    worst = {spec.name: spec.lo for spec in SEARCH_SPACE}  # far corner
    baseline = reward(worst)
    result = GaitOptimizer(reward, seed=7).optimize(
        start=dict(worst), iterations=80)
    assert result.best_reward > baseline + 1.0, \
        f"no improvement: {baseline:.2f} -> {result.best_reward:.2f}"
    assert result.best_reward > 8.0               # close to the optimum (10)
    for spec in SEARCH_SPACE:
        assert spec.lo <= result.best_params[spec.name] <= spec.hi
    assert len(result.history) == 81              # baseline + 80 candidates
    # determinism: same seed, same outcome
    again = GaitOptimizer(SimReward(noise=0.0), seed=7).optimize(
        start=dict(worst), iterations=80)
    assert again.best_reward == result.best_reward


def test_measured_reward_flow():
    """MeasuredReward must drive the robot and parse the operator's input."""
    from tars.learn import MeasuredReward
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    answers = iter(["", "not-a-number", "12,5"])  # Enter, junk, then valid
    printed = []
    reward = MeasuredReward(gaits, steps=2, input_fn=lambda _: next(answers),
                            print_fn=printed.append)
    value = reward(dict(gaits.gp))
    assert value == 12.5 / 2
    assert any("step 2/2" in str(line) for line in printed)


def test_gait_params_persistence():
    from tars.movement.gaits import GAIT_PARAMS_FILE, DEFAULT_GAIT_PARAMS
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    gaits.apply_gait_params({"lift_delay": 0.002, "not_a_param": 99})
    assert gaits.gp["lift_delay"] == 0.002
    assert "not_a_param" not in gaits.gp
    gaits.save_gait_params()
    reloaded = Gaits(ServoDriver(60, sim=True), settings)
    assert reloaded.gp["lift_delay"] == 0.002
    GAIT_PARAMS_FILE.write_text("{broken json")   # corrupt file is ignored
    survivor = Gaits(ServoDriver(60, sim=True), settings)
    assert survivor.gp["lift_delay"] == DEFAULT_GAIT_PARAMS["lift_delay"]
    GAIT_PARAMS_FILE.unlink()


def test_display_route():
    ctx = make_ctx()
    brain = Brain(settings, ctx.memory, ctx)
    spk = Speaker(settings)
    spk.muted = True
    app = create_app(settings, brain, ctx.gaits, VoiceLoop(settings, brain, spk))
    c = app.test_client()
    page = c.get("/display")
    assert page.status_code == 200 and b"ONBOARD" in page.data
    # kiosk page stays reachable even with the password gate on
    settings.web_password = "x"
    try:
        assert c.get("/display").status_code == 200
    finally:
        settings.web_password = ""


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

    assert "tars" in c.get("/api/characters").json["available"]
    assert c.get("/images/nope.png").status_code == 404
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
