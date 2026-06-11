"""Web dashboard: chat with TARS, drive the body, tune the personality."""
import logging
import threading
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

from ..config import Settings
from ..llm import Brain
from ..voice import VoiceLoop

log = logging.getLogger("tars.web")
STATIC = Path(__file__).parent / "static"


def create_app(s: Settings, brain: Brain, gaits, voice: VoiceLoop) -> Flask:
    app = Flask("tars", static_folder=None)

    @app.get("/")
    def index():
        return send_from_directory(STATIC, "index.html")

    @app.post("/api/chat")
    def chat():
        text = (request.json or {}).get("message", "").strip()
        if not text:
            return jsonify(error="empty message"), 400
        return jsonify(reply=brain.chat(text))

    @app.post("/api/move")
    def move():
        action = (request.json or {}).get("action", "")
        if gaits is None:
            return jsonify(error="no hardware"), 503
        if action not in ("step_forward", "turn_left", "turn_right", "pose", "neutral"):
            return jsonify(error="unknown action"), 400
        threading.Thread(target=getattr(gaits, action), daemon=True).start()
        return jsonify(ok=True, action=action)

    @app.get("/api/settings")
    def get_settings():
        return jsonify(s.public())

    @app.post("/api/settings")
    def set_settings():
        body = request.json or {}
        for key in ("humor", "honesty", "sarcasm"):
            if key in body:
                setattr(s, key, max(0, min(100, int(body[key]))))
        for key in ("robot_name", "wake_word", "language"):
            if key in body and body[key]:
                setattr(s, key, str(body[key]))
        s.save()
        return jsonify(s.public())

    @app.get("/api/status")
    def status():
        return jsonify(voice=voice.state, sim=gaits is None or gaits.d.sim,
                       name=s.robot_name, humor=s.humor, honesty=s.honesty)

    @app.post("/api/voice/<cmd>")
    def voice_cmd(cmd):
        if cmd == "start":
            voice.start()
        elif cmd == "stop":
            voice.stop()
        elif cmd == "ptt":
            voice.push_to_talk()
        else:
            return jsonify(error="unknown command"), 400
        return jsonify(state=voice.state)

    return app
