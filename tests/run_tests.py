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
                   "set_character", "set_volume", "generate_image",
                   "web_search", "calculate"}

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


def test_camera_shift_estimation():
    """Phase correlation must recover a known synthetic translation."""
    try:
        import cv2  # noqa: F401
        import numpy as np
    except ImportError:
        print("  (opencv missing, skipped)")
        return
    from tars.learn import estimate_shift
    rng = np.random.default_rng(0)
    scene = (rng.random((240, 320)) * 255).astype(np.uint8)
    shifted = np.roll(scene, shift=(7, 12), axis=(0, 1))   # dy=7, dx=12
    dx, dy = estimate_shift(scene, shifted)
    assert abs(abs(dx) - 12) < 1.0 and abs(abs(dy) - 7) < 1.0, (dx, dy)


def test_camera_reward_flow():
    try:
        import numpy as np
    except ImportError:
        print("  (numpy missing, skipped)")
        return
    try:
        import cv2  # noqa: F401
    except ImportError:
        print("  (opencv missing, skipped)")
        return
    from tars.learn import CameraReward
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    rng = np.random.default_rng(1)
    scene = (rng.random((120, 160)) * 255).astype(np.uint8)
    frames = iter([scene, np.roll(scene, 9, axis=1)])      # 9 px of travel
    reward = CameraReward(gaits, steps=3, capture_fn=lambda: next(frames),
                          print_fn=lambda *_: None)
    value = reward(dict(gaits.gp))
    assert 2.5 < value < 3.5, value                        # ~9 px / 3 steps


def test_eased_sweep_lands_exactly():
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    seen = {}
    gaits.d.set_pwm = lambda ch, v: seen.__setitem__(ch, v)
    gaits._sweep(0, 300, 340, 0)
    assert seen[0] == 340
    gaits._sweep(0, 340, 300, 0)
    assert seen[0] == 300
    gaits._sweep(0, 300, 300, 0)                           # zero-length
    assert seen[0] == 300
    # easing: gentle at the ends, fast mid-travel, dwell capped at 4x
    delays = [Gaits._eased_delay(1.0, i, 100) for i in range(1, 101)]
    assert delays[0] > delays[50] and delays[-1] > delays[50]
    assert max(delays) <= 4.0 and min(delays) >= 1.0


def test_optimizer_keyboard_interrupt():
    """Ctrl-C during a hardware session must keep the best gait found."""
    from tars.learn import GaitOptimizer, SimReward, SEARCH_SPACE
    sim = SimReward(noise=0.0)
    calls = {"n": 0}
    def reward(params):
        calls["n"] += 1
        if calls["n"] >= 5:
            raise KeyboardInterrupt
        return sim(params)
    result = GaitOptimizer(reward, seed=1).optimize(
        start={spec.name: spec.lo for spec in SEARCH_SPACE}, iterations=50)
    assert len(result.history) == 4                        # baseline + 3 done
    assert result.best_reward == max(r for _, r in result.history)


def test_imu_graceful_without_hardware():
    from tars.sensors import Imu, get_imu
    imu = Imu()
    assert imu.available is False           # no smbus in the test environment
    assert imu.read_accel() is None
    assert imu.is_upright() is None
    assert get_imu() is get_imu()           # singleton


def test_fall_guard():
    from tars.learn import FallGuard
    class FakeImu:
        def __init__(self, upright):
            self.upright = upright
        def is_upright(self):
            return self.upright
    inner = lambda params: 7.5  # noqa: E731
    said = []
    assert FallGuard(inner, FakeImu(True), print_fn=said.append)({}) == 7.5
    assert FallGuard(inner, FakeImu(False), print_fn=said.append)({}) == -5.0
    assert any("fall" in str(s) for s in said)
    # sensor missing mid-session (None) must NOT penalize
    assert FallGuard(inner, FakeImu(None), print_fn=said.append)({}) == 7.5


def test_optimizer_skips_failed_evaluations():
    from tars.learn import GaitOptimizer, SimReward, SEARCH_SPACE
    sim = SimReward(noise=0.0)
    calls = {"n": 0}
    def flaky(params):
        calls["n"] += 1
        if calls["n"] == 3:
            raise RuntimeError("camera glitch")
        return sim(params)
    result = GaitOptimizer(flaky, seed=2).optimize(
        start={spec.name: spec.lo for spec in SEARCH_SPACE}, iterations=10)
    assert calls["n"] == 11                       # baseline + 10 attempted
    assert len(result.history) == 10              # one evaluation was skipped
    assert result.best_reward == max(r for _, r in result.history)


def test_camera_axis_signed():
    try:
        import cv2  # noqa: F401
        import numpy as np
    except ImportError:
        print("  (opencv missing, skipped)")
        return
    from tars.learn import CameraReward
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    rng = np.random.default_rng(2)
    scene = (rng.random((120, 160)) * 255).astype(np.uint8)
    def make(axis):
        frames = iter([scene, np.roll(scene, 9, axis=1)])
        return CameraReward(gaits, steps=3, capture_fn=lambda: next(frames),
                            print_fn=lambda *_: None, axis=axis)
    vx = make("x")(dict(gaits.gp))
    vneg = make("-x")(dict(gaits.gp))
    assert abs(abs(vx) - 3) < 0.5 and vneg == -vx  # signed and consistent
    try:
        CameraReward(gaits, axis="diagonal")
        raise AssertionError("invalid axis accepted")
    except ValueError:
        pass


def test_training_log_and_endpoint():
    from tars.learn import TrainingLog
    from tars.learn.training_log import TRAINING_LOG_FILE
    train_log = TrainingLog("sim")
    train_log.record(1, 2.5, 2.5)
    train_log.record(2, 1.0, 2.5)
    loaded = TrainingLog.load()
    assert loaded["mode"] == "sim" and len(loaded["entries"]) == 2
    assert loaded["entries"][1]["best"] == 2.5
    ctx = make_ctx()
    brain = Brain(settings, ctx.memory, ctx)
    spk = Speaker(settings)
    spk.muted = True
    app = create_app(settings, brain, ctx.gaits, VoiceLoop(settings, brain, spk))
    data = app.test_client().get("/api/training").json
    assert len(data["entries"]) == 2
    TRAINING_LOG_FILE.unlink()


def test_gyro_graceful_and_doctor():
    from tars.sensors import Imu
    assert Imu().read_gyro() is None          # no hardware here
    from tars.doctor import run_checks, OK, WARN, FAIL
    checks = run_checks(settings)
    names = {c.name for c in checks}
    assert {"Python", "PCA9685 servo driver", "LLM brain",
            "Microphone", "Disk space"} <= names
    assert all(c.status in (OK, WARN, FAIL) and c.detail for c in checks)
    assert next(c for c in checks if c.name == "Python").status == OK


def test_camera_scale_calibration():
    try:
        import cv2  # noqa: F401
        import numpy as np
    except ImportError:
        print("  (opencv missing, skipped)")
        return
    from tars.learn import CameraReward
    from tars.learn.vision_reward import (save_camera_scale, load_camera_scale,
                                          CAMERA_SCALE_FILE)
    from tars.learn.__main__ import calibrate_camera
    import tempfile
    rng = np.random.default_rng(3)
    scene = (rng.random((120, 160)) * 255).astype(np.uint8)

    def frame_writer(images):
        frames = iter(images)
        def capture():
            path = tempfile.mktemp(suffix=".png", prefix="tars_cal_")
            cv2.imwrite(path, next(frames))
            return path
        return capture

    # calibration flow: 10 px of shift declared as 5 cm -> 2 px/cm
    answers = iter(["", "5"])
    code = calibrate_camera(input_fn=lambda _: next(answers),
                            print_fn=lambda *_: None,
                            capture_fn=frame_writer([scene, np.roll(scene, 10, axis=1)]))
    assert code == 0 and abs(load_camera_scale() - 2.0) < 0.2
    # the reward now speaks centimeters: 10 px / 2 px/cm / 2 steps = 2.5
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    frames = iter([scene, np.roll(scene, 10, axis=1)])
    reward = CameraReward(gaits, steps=2, capture_fn=lambda: next(frames),
                          print_fn=lambda *_: None)
    assert abs(reward(dict(gaits.gp)) - 2.5) < 0.3
    CAMERA_SCALE_FILE.unlink()
    save_camera_scale(-1)                      # invalid scale is rejected
    assert load_camera_scale() is None
    CAMERA_SCALE_FILE.unlink()


def test_wake_ack_resolution():
    from tars.voice import resolve_ack
    old_ack, old_lang = settings.ack, settings.language
    try:
        settings.ack, settings.language = "auto", "it"
        assert resolve_ack(settings) == "Sì?"
        settings.language = "xx"               # unknown language falls back
        assert resolve_ack(settings) == "Yes?"
        settings.ack = "off"
        assert resolve_ack(settings) is None
        settings.ack = "At your service."
        assert resolve_ack(settings) == "At your service."
    finally:
        settings.ack, settings.language = old_ack, old_lang


def test_conversation_survives_restart():
    mem = Memory(settings)
    mem.clear()
    mem.add_turn("user", "remember this across reboots")
    mem.add_turn("assistant", "noted")
    reborn = Memory(settings)
    assert [t["content"] for t in reborn.turns[-2:]] == \
        ["remember this across reboots", "noted"]
    reborn.clear()
    assert Memory(settings).turns == []


def test_fall_guard_stability_tax():
    import time as _time
    from tars.learn import FallGuard
    class WobblyImu:
        def is_upright(self):
            return True
        def read_gyro(self):
            return (30.0, 40.0, 0.0)            # magnitude 50 deg/s
    def slow_inner(params):
        _time.sleep(0.12)                       # let the sampler collect
        return 10.0
    guard = FallGuard(slow_inner, WobblyImu(), wobble_weight=0.01,
                      print_fn=lambda *_: None)
    taxed = guard({})
    assert abs(taxed - 9.5) < 1e-9, taxed       # 10 - 0.01 * 50
    # weight 0 disables sampling entirely
    assert FallGuard(slow_inner, WobblyImu(), wobble_weight=0.0,
                     print_fn=lambda *_: None)({}) == 10.0
    # a fall still wins over any wobble math
    class FallenImu(WobblyImu):
        def is_upright(self):
            return False
    assert FallGuard(slow_inner, FallenImu(), wobble_weight=0.01,
                     print_fn=lambda *_: None)({}) == -5.0


def test_benchmark_skips_gracefully():
    from tars.benchmark import run_benchmark, OK, SKIP
    results = run_benchmark(settings)
    assert [r.name for r in results] == ["LLM reply", "TTS synthesis",
                                         "STT transcription"]
    assert all(r.status in (OK, SKIP) and r.detail for r in results)
    if not (settings.openai_api_key or settings.llm_base_url):
        assert results[0].status == SKIP        # unconfigured = skip, not crash


def test_display_waveform_markup():
    page = open("tars/web/static/display.html").read()
    assert 'id="wave"' in page and "voiceState" in page


def test_mujoco_driver_and_locomotion():
    try:
        import mujoco  # noqa: F401
    except ImportError:
        print("  (mujoco missing, skipped)")
        return
    from tars.learn.mujoco_sim import MujocoDriver
    driver = MujocoDriver(settings)
    assert driver.parallel_safe is False
    t0 = driver.d.time
    driver.sleep(0.1)
    assert abs((driver.d.time - t0) - 0.1) < 0.01   # sleep advances physics
    driver.set_pwm(99, 400)                          # unknown channel ignored
    # the baseline gait must walk FORWARD in the default world
    gaits = Gaits(driver, settings)
    x0 = driver.torso_x
    for _ in range(3):
        gaits.step_forward()
    driver.sleep(0.4)
    per_step = (driver.torso_x - x0) * 100 / 3
    assert 0.2 < per_step < 2.0, f"{per_step:.2f} cm/step"
    assert driver.upright is True
    # tipping the torso must be detected
    driver.d.qpos[3:7] = [0.7071, 0.7071, 0, 0]      # 90 deg roll
    import mujoco as mj
    mj.mj_forward(driver.m, driver.d)
    assert driver.upright is False


def test_mujoco_reward_deterministic_and_randomized():
    try:
        import mujoco  # noqa: F401
    except ImportError:
        print("  (mujoco missing, skipped)")
        return
    from tars.learn.mujoco_reward import MujocoReward
    from tars.movement.gaits import DEFAULT_GAIT_PARAMS
    reward = MujocoReward(settings, steps=2, randomizations=3, seed=11)
    assert len(reward.worlds) == 3
    assert reward.worlds[0] != reward.worlds[1]      # worlds actually differ
    a = reward(dict(DEFAULT_GAIT_PARAMS))
    b = MujocoReward(settings, steps=2, randomizations=3,
                     seed=11)(dict(DEFAULT_GAIT_PARAMS))
    assert a == b                                    # common random numbers
    assert -10 < a < 10 and a == a                   # finite, sane


def test_mujoco_slew_limit_and_reset():
    try:
        import mujoco  # noqa: F401
    except ImportError:
        print("  (mujoco missing, skipped)")
        return
    from tars.learn.mujoco_sim import MujocoDriver, HINGE_MAX_RATE
    driver = MujocoDriver(settings)
    # command a big jump: ctrl must ramp at the servo's max rate, not teleport
    ctrl_before = float(driver.d.ctrl[1])
    driver.set_pwm(settings.ch_port_drive, settings.pwm["forward_port"])
    driver.sleep(0.05)
    moved = abs(float(driver.d.ctrl[1]) - ctrl_before)
    assert moved <= HINGE_MAX_RATE * 0.05 + 1e-9, moved
    assert moved > 0.1                            # but it IS moving
    # reset() restores the settled stance exactly
    driver.sleep(0.5)
    driver.reset()
    assert abs(driver.torso_x) < 1e-6
    assert driver.upright and driver.angvel_samples == []


def test_mujoco_reward_reuse_and_fail_fast():
    try:
        import mujoco  # noqa: F401
    except ImportError:
        print("  (mujoco missing, skipped)")
        return
    from tars.learn.mujoco_reward import MujocoReward
    from tars.movement.gaits import DEFAULT_GAIT_PARAMS
    reward = MujocoReward(settings, steps=2, randomizations=2, seed=5)
    a = reward(dict(DEFAULT_GAIT_PARAMS))
    b = reward(dict(DEFAULT_GAIT_PARAMS))
    assert a == b, (a, b)                         # reused worlds, same result
    # fail-fast: a falling first world short-circuits the remaining ones
    calls = {"n": 0}
    original = reward._episode
    def falling(params, index):
        calls["n"] += 1
        return reward.fall_penalty
    reward._episode = falling
    assert reward(dict(DEFAULT_GAIT_PARAMS)) == reward.fall_penalty
    assert calls["n"] == 1
    reward._episode = original


def test_fit_sim_machinery():
    from tars.learn.fit import fit_sim, CONSTANT_RANGES
    from tars.learn.mujoco_reward import (save_sim_calibration,
                                          load_sim_calibration,
                                          SIM_CALIBRATION_FILE)
    # synthetic "reality": a hidden linear judge of friction-like params
    def make_judge(true_friction):
        def factory(constants):
            def score(params):
                # candidates rank by lift_delay, modulated by how close the
                # trial's friction is to the truth
                gap = abs(constants["friction"] - true_friction)
                sign = 1 if gap < 0.2 else -1
                return sign * params["lift_delay"]
            return score
        return factory
    entries = [{"params": {"lift_delay": v}, "reward": v}
               for v in (0.001, 0.002, 0.003, 0.004, 0.005)]
    result = fit_sim(settings, {"entries": entries}, trials=25, seed=3,
                     print_fn=lambda *_: None,
                     reward_factory=make_judge(0.9))
    assert abs(result["rho"] - 1.0) < 1e-9        # found a well-ranking config
    assert abs(result["friction"] - 0.9) < 0.2    # near the hidden truth
    assert result["samples"] == 5
    for key, (lo, hi) in CONSTANT_RANGES.items():
        assert lo <= result[key] <= hi
    # persistence round-trip used by MujocoReward's world centering
    save_sim_calibration(result)
    assert load_sim_calibration()["rho"] == result["rho"]
    SIM_CALIBRATION_FILE.unlink()


def test_bump_pause_default_is_noop():
    from tars.movement.gaits import DEFAULT_GAIT_PARAMS
    from tars.learn import SEARCH_SPACE
    assert DEFAULT_GAIT_PARAMS["bump_pause"] <= 1e-3
    assert {spec.name for spec in SEARCH_SPACE} == set(DEFAULT_GAIT_PARAMS)
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    gaits.step_forward()                          # new param breaks nothing


def test_fall_watchdog_runtime():
    from tars.app import make_fall_watchdog
    relaxed, neutraled, said = [], [], []
    class FakeImu:
        def __init__(self):
            self.upright = True
        def is_upright(self):
            return self.upright
    class FakeGaits:
        def relax_legs(self):
            relaxed.append(1)
        def neutral(self):
            neutraled.append(1)
    class FakeSpeaker:
        def say(self, text):
            said.append(text)
    imu = FakeImu()
    check = make_fall_watchdog(imu, FakeGaits(), FakeSpeaker(), confirmations=2)
    check()                                   # upright: nothing happens
    imu.upright = False
    check()                                   # 1st bad reading: not yet
    assert relaxed == []
    check()                                   # confirmed fall
    check()                                   # stays down: no repeat
    assert relaxed == [1] and len(said) == 1 and "fallen" in said[0]
    imu.upright = True
    check()                                   # recovery: stance + announce
    assert neutraled == [1] and len(said) == 2
    imu.upright = None                        # sensor gone: never crash
    check()


def test_tls_context_resolution():
    from tars.web.server import resolve_ssl_context
    settings.tls = False
    assert resolve_ssl_context(settings) is None
    settings.tls = True
    try:
        import OpenSSL  # noqa: F401
        assert resolve_ssl_context(settings) == "adhoc"
    except ImportError:
        assert resolve_ssl_context(settings) is None   # graceful HTTP fallback
    finally:
        settings.tls = False


def test_dashboard_config_panel():
    page = open("tars/web/static/index.html").read()
    for needle in ("cfgName", "cfgWake", "cfgLang", "saveConfig"):
        assert needle in page, needle
    # the API behind it accepts identity fields
    ctx = make_ctx()
    brain = Brain(settings, ctx.memory, ctx)
    spk = Speaker(settings)
    spk.muted = True
    app = create_app(settings, brain, ctx.gaits, VoiceLoop(settings, brain, spk))
    old = (settings.robot_name, settings.wake_word, settings.language)
    try:
        data = app.test_client().post("/api/settings", json={
            "robot_name": "BOT", "wake_word": "robot", "language": "it"}).json
        assert (data["robot_name"], data["wake_word"], data["language"]) == \
            ("BOT", "robot", "it")
    finally:
        settings.robot_name, settings.wake_word, settings.language = old
        settings.save()


def test_shopping_lists_have_buy_links():
    for path, label in (("docs/en/SHOPPING_LIST.md", "[Buy]("),
                        ("docs/it/LISTA_ACQUISTI.md", "[Compra](")):
        text = open(path).read()
        assert text.count(label) >= 27, f"{path}: {text.count(label)} links"


def test_calculator_safe_eval():
    ctx = make_ctx()
    assert skills.run("calculate", {"expression": "12.5 * 6 / 5"}, ctx).endswith("= 15")
    assert skills.run("calculate", {"expression": "sqrt(2)**2"}, ctx)\
        .endswith("= 2.0000000000000004")
    assert skills.run("calculate", {"expression": "round(pi, 2)"}, ctx).endswith("= 3.14")
    # everything dangerous must be rejected, never executed
    for evil in ("__import__('os')", "open('/etc/passwd')", "x", "2**9999",
                 "(1).__class__", "1; print(1)", "1/0"):
        assert skills.run("calculate", {"expression": evil}, ctx).startswith("error"), evil


def test_web_search_graceful():
    # offline sandbox: must fail with a message, never raise
    ctx = make_ctx()
    result = skills.run("web_search", {"query": "interstellar movie"}, ctx)
    assert isinstance(result, str) and result
    if result.startswith("error"):
        assert "no result" in result


def test_network_camera_fallback():
    from tars.skills.vision import _capture_from_url, capture
    assert _capture_from_url("rtsp://192.0.2.1/none") is None   # dead cam: None, fast
    old = settings.camera_url
    try:
        settings.camera_url = "rtsp://192.0.2.1/none"
        assert capture() is None      # falls through to local tools (absent here)
    finally:
        settings.camera_url = old


def test_calibration_endpoint():
    ctx = make_ctx()
    brain = Brain(settings, ctx.memory, ctx)
    spk = Speaker(settings)
    spk.muted = True
    app = create_app(settings, brain, ctx.gaits, VoiceLoop(settings, brain, spk))
    c = app.test_client()
    assert c.post("/api/calibrate", json={"channel": 0, "value": 300}).json["ok"]
    assert c.post("/api/calibrate", json={"channel": 0, "value": 9999}).json["value"] == 680
    assert c.post("/api/calibrate", json={"channel": 99, "value": 300}).status_code == 400
    assert c.post("/api/calibrate", json={}).status_code == 400
    assert c.post("/api/calibrate",
                  json={"channel": 0, "value": 300, "save_as": "nope"}).status_code == 400
    old = settings.pwm["neutral_height"]
    try:
        data = c.post("/api/calibrate", json={"channel": 0, "value": 280,
                                              "save_as": "neutral_height"}).json
        assert data["saved"] == "neutral_height"
        assert settings.pwm["neutral_height"] == 280
    finally:
        settings.pwm["neutral_height"] = old
        settings.save()
    page = open("tars/web/static/index.html").read()
    assert "calDrive" in page and "kgCanvas" in page


def test_dashboard_restores_history():
    page = open("tars/web/static/index.html").read()
    assert "loadHistory" in page and "is speaking" in page


def test_version_flag():
    import subprocess
    import tars
    out = subprocess.run([sys.executable, "-m", "tars.app", "--version"],
                         capture_output=True, text=True,
                         cwd=Path(__file__).resolve().parent.parent,
                         env={**os.environ, "TARS_SIM": "1"})
    assert out.returncode == 0 and tars.__version__ in out.stdout


def test_strafing():
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    calls = []
    for name in ("turn_left", "turn_right", "step_forward"):
        setattr(gaits, name, lambda n=name: calls.append(n))
    gaits.strafe_left()
    assert calls == ["turn_left", "step_forward", "turn_right"]
    calls.clear()
    gaits.strafe_right()
    assert calls == ["turn_right", "step_forward", "turn_left"]
    # exposed everywhere: skill, web, sequences
    ctx = make_ctx()
    assert skills.run("move", {"action": "strafe_left"}, ctx).startswith("ok")
    assert skills.run("perform", {"name": "slalom"}, ctx) == "ok: performed slalom"
    brain = Brain(settings, ctx.memory, ctx)
    spk = Speaker(settings)
    spk.muted = True
    app = create_app(settings, brain, ctx.gaits, VoiceLoop(settings, brain, spk))
    r = app.test_client().post("/api/move", json={"action": "strafe_right"})
    assert r.json["ok"] is True


def test_relax_legs():
    gaits = Gaits(ServoDriver(60, sim=True), settings)
    relaxed = []
    gaits.d.relax = lambda ch: relaxed.append(ch)
    gaits.relax_legs()
    assert relaxed == [settings.ch_center_lift, settings.ch_port_drive,
                       settings.ch_star_drive]


def test_spearman_and_correlate():
    from tars.learn.correlate import spearman, correlate_log, verdict
    assert abs(spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1.0) < 1e-9
    assert abs(spearman([1, 2, 3, 4], [40, 30, 20, 10]) + 1.0) < 1e-9
    assert abs(spearman([1, 2, 2, 4], [1, 2, 2, 4]) - 1.0) < 1e-9  # ties
    try:
        spearman([1, 2], [1, 2])
        raise AssertionError("accepted too few samples")
    except ValueError:
        pass
    # replaying a log through the SAME function must give rho = 1
    from tars.learn import SimReward
    sim = SimReward(noise=0.0)
    from tars.learn import GaitOptimizer, SEARCH_SPACE
    start = {spec.name: spec.lo for spec in SEARCH_SPACE}
    result = GaitOptimizer(sim, seed=4).optimize(start=start, iterations=8)
    log_data = {"entries": [{"params": p, "reward": r}
                            for p, r in result.history]}
    rho, n = correlate_log(sim, log_data)
    assert abs(rho - 1.0) < 1e-9 and n == 9
    assert "useful" in verdict(0.8) and "real" in verdict(0.1)
    try:
        correlate_log(sim, {"entries": [{"reward": 1.0}] * 5})  # no params
        raise AssertionError("accepted entries without params")
    except ValueError:
        pass


def test_training_log_stores_params():
    from tars.learn import TrainingLog
    from tars.learn.training_log import TRAINING_LOG_FILE
    train_log = TrainingLog("measured")
    train_log.record(1, 3.0, 3.0, params={"lift_delay": 0.001})
    loaded = TrainingLog.load()
    assert loaded["entries"][0]["params"]["lift_delay"] == 0.001
    TRAINING_LOG_FILE.unlink()


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
