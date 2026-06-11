"""TARS entrypoint: wires servos, skills, brain, speech, voice loop, gamepad,
scheduler and the web dashboard together.

Usage:
    python -m tars.app                 # everything
    python -m tars.app --sim           # no hardware (develop on a laptop)
    python -m tars.app --no-voice      # web/text only
    python -m tars.app --no-web        # voice + gamepad only
"""
import argparse
import logging
import threading

from . import skills
from .config import settings
from .knowledge import KnowledgeGraph
from .llm import Brain
from .memory import Memory
from .movement import ServoDriver, Gaits
from .movement import gamepad
from .scheduler import Scheduler
from .speakerid import SpeakerID
from .speech import Speaker
from .voice import VoiceLoop


def battery_watchdog(speaker: Speaker):
    """Periodic check; TARS announces when the battery runs low."""
    from .skills.system import read_battery, battery_percent
    state = {"warned": False}

    def check():
        battery = read_battery()
        if battery is None:
            return
        pct = battery_percent(battery["voltage"])
        if pct <= settings.battery_low_pct and not state["warned"]:
            state["warned"] = True
            speaker.say(f"Battery at {pct} percent. I suggest a recharge before I power down dramatically.")
        elif pct > settings.battery_low_pct + 10:
            state["warned"] = False
    return check


def main():
    parser = argparse.ArgumentParser(description="TARS robot runtime")
    parser.add_argument("--sim", action="store_true", help="simulate servos (no hardware)")
    parser.add_argument("--no-voice", action="store_true", help="disable the voice loop")
    parser.add_argument("--no-web", action="store_true", help="disable the web dashboard")
    parser.add_argument("--no-gamepad", action="store_true", help="disable gamepad control")
    parser.add_argument("--doctor", action="store_true",
                        help="run the hardware/software self-test and exit")
    parser.add_argument("--benchmark", action="store_true",
                        help="time the LLM/TTS/STT pipeline and exit")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.doctor:
        from .doctor import print_report
        raise SystemExit(print_report(settings))
    if args.benchmark:
        from .benchmark import print_report
        raise SystemExit(print_report(settings))

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    log = logging.getLogger("tars")

    # restore the persisted character's identity/voice without overriding
    # personality dials the user may have tuned since switching
    from . import characters
    if settings.character:
        characters.apply_character(settings.character, settings, dials=False)

    driver = ServoDriver(settings.pwm_frequency, sim=args.sim or settings.sim_mode)
    gaits = Gaits(driver, settings)
    gaits.neutral()

    scheduler = Scheduler()
    scheduler.start()
    speaker = Speaker(settings)
    memory = Memory(settings)

    knowledge = KnowledgeGraph()
    speaker_id = SpeakerID()
    ctx = skills.SkillContext(settings=settings, memory=memory, gaits=gaits,
                              scheduler=scheduler, speaker=speaker,
                              extras={"knowledge": knowledge,
                                      "speaker_id": speaker_id})
    skills.load_skills()
    brain = Brain(settings, memory, ctx)
    voice = VoiceLoop(settings, brain, speaker,
                      speaker_id=speaker_id if speaker_id.available else None)

    scheduler.every(60, battery_watchdog(speaker))

    if not args.no_gamepad:
        threading.Thread(target=gamepad.run,
                         args=(gaits, settings.gamepad_device), daemon=True).start()
    if not args.no_voice:
        voice.start()

    log.info("%s online. Humor %d%%, honesty %d%%, %d skills.",
             settings.robot_name, settings.humor, settings.honesty,
             len(skills.REGISTRY))

    if args.no_web:
        threading.Event().wait()  # keep daemon threads alive
    else:
        from .web.server import create_app
        app = create_app(settings, brain, gaits, voice)
        log.info("Dashboard: http://%s:%d", settings.web_host, settings.web_port)
        app.run(host=settings.web_host, port=settings.web_port, threaded=True)


if __name__ == "__main__":
    main()
