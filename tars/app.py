"""TARS entrypoint: wires servos, brain, voice loop, gamepad and web dashboard.

Usage:
    python -m tars.app                 # everything
    python -m tars.app --sim           # no hardware (develop on a laptop)
    python -m tars.app --no-voice      # web/text only
    python -m tars.app --no-web        # voice + gamepad only
"""
import argparse
import logging
import threading

from .config import settings
from .llm import Brain
from .memory import Memory
from .movement import ServoDriver, Gaits
from .movement import gamepad
from .voice import VoiceLoop


def main():
    parser = argparse.ArgumentParser(description="TARS robot runtime")
    parser.add_argument("--sim", action="store_true", help="simulate servos (no hardware)")
    parser.add_argument("--no-voice", action="store_true", help="disable the voice loop")
    parser.add_argument("--no-web", action="store_true", help="disable the web dashboard")
    parser.add_argument("--no-gamepad", action="store_true", help="disable gamepad control")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    log = logging.getLogger("tars")

    driver = ServoDriver(settings.pwm_frequency, sim=args.sim or settings.sim_mode)
    gaits = Gaits(driver, settings)
    gaits.neutral()

    memory = Memory()
    brain = Brain(settings, memory, gaits)
    voice = VoiceLoop(settings, brain)

    if not args.no_gamepad:
        threading.Thread(target=gamepad.run,
                         args=(gaits, settings.gamepad_device), daemon=True).start()
    if not args.no_voice:
        voice.start()

    log.info("%s online. Humor %d%%, honesty %d%%.",
             settings.robot_name, settings.humor, settings.honesty)

    if args.no_web:
        threading.Event().wait()  # keep daemon threads alive
    else:
        from .web.server import create_app
        app = create_app(settings, brain, gaits, voice)
        log.info("Dashboard: http://%s:%d", settings.web_host, settings.web_port)
        app.run(host=settings.web_host, port=settings.web_port, threaded=True)


if __name__ == "__main__":
    main()
