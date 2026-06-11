"""Web dashboard: streaming chat, browser voice mode, body control,
personality tuning, knowledge inspector and vitals."""
import json
import logging
import os
import secrets
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from flask import Flask, Response, jsonify, request, send_file, send_from_directory

from .. import characters, stt, tts
from ..config import DATA_DIR, Settings
from ..llm import Brain
from ..skills.system import read_battery, read_cpu_temp, battery_percent
from ..voice import VoiceLoop

log = logging.getLogger("tars.web")
STATIC = Path(__file__).parent / "static"


def _to_wav(path: str) -> str | None:
    """Convert browser audio (webm/ogg) to 16 kHz mono wav for offline STT."""
    if not shutil.which("ffmpeg"):
        return None
    out = tempfile.mktemp(suffix=".wav", prefix="tars_web_")
    result = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", path,
         "-ar", "16000", "-ac", "1", out], capture_output=True)
    return out if result.returncode == 0 else None


def create_app(s: Settings, brain: Brain, gaits, voice: VoiceLoop) -> Flask:
    app = Flask("tars", static_folder=None)
    sessions: set[str] = set()

    @app.before_request
    def auth_gate():
        """Optional shared-password login (set TARS_WEB_PASSWORD)."""
        if not s.web_password:
            return None
        if request.remote_addr == "127.0.0.1":
            return None  # the robot's own kiosk screen never needs login
        if request.path in ("/", "/display", "/api/login") \
                or request.path.startswith("/images/"):
            return None
        token = request.cookies.get("tars_session", "")
        if token in sessions:
            return None
        return jsonify(error="login required"), 401

    @app.post("/api/login")
    def login():
        if not s.web_password:
            return jsonify(ok=True)
        if (request.json or {}).get("password", "") != s.web_password:
            return jsonify(error="wrong password"), 403
        token = secrets.token_hex(16)
        sessions.add(token)
        resp = jsonify(ok=True)
        resp.set_cookie("tars_session", token, httponly=True, samesite="Lax")
        return resp

    @app.get("/")
    def index():
        return send_from_directory(STATIC, "index.html")

    @app.get("/display")
    def display():
        """Movie-style onboard readout for the robot's own DSI screen
        (open in a kiosk browser: chromium --kiosk http://localhost:8000/display)."""
        return send_from_directory(STATIC, "display.html")

    @app.get("/images/<path:fname>")
    def images(fname):
        return send_from_directory(DATA_DIR / "images", fname)

    @app.get("/api/characters")
    def get_characters():
        return jsonify(available=characters.list_characters(), active=s.character)

    @app.post("/api/characters")
    def post_character():
        name = (request.json or {}).get("name", "")
        if not characters.apply_character(name, s):
            return jsonify(error="unknown character"), 404
        return jsonify(ok=True, active=s.character, robot_name=s.robot_name)

    @app.post("/api/chat")
    def chat():
        text = (request.json or {}).get("message", "").strip()
        if not text:
            return jsonify(error="empty message"), 400
        return jsonify(reply=brain.chat(text))

    @app.post("/api/chat/stream")
    def chat_stream():
        text = (request.json or {}).get("message", "").strip()
        if not text:
            return jsonify(error="empty message"), 400

        def generate():
            for chunk in brain.chat_stream(text):
                yield f"data: {json.dumps({'delta': chunk})}\n\n"
            yield "data: {\"done\": true}\n\n"

        return Response(generate(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache",
                                 "X-Accel-Buffering": "no"})

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
        battery = read_battery()
        return jsonify(
            voice=voice.state,
            sim=gaits is None or gaits.d.sim,
            name=s.robot_name, humor=s.humor, honesty=s.honesty,
            cpu_temp=read_cpu_temp(),
            battery_pct=battery_percent(battery["voltage"]) if battery else None)

    @app.get("/api/memory")
    def memory():
        notes = [{k: v for k, v in n.items() if k != "emb"}
                 for n in brain.memory.notes[-50:]]
        return jsonify(notes=notes, turns=brain.memory.turns[-20:])

    @app.get("/api/training")
    def training():
        from ..learn.training_log import TrainingLog
        return jsonify(TrainingLog.load() or {})

    @app.get("/api/knowledge")
    def knowledge():
        kg = brain.ctx.extras.get("knowledge")
        return jsonify(triples=kg.triples[-100:] if kg else [])

    @app.post("/api/voice/chat")
    def browser_voice_chat():
        """Browser voice mode: audio blob in, transcript + reply out."""
        upload = request.files.get("audio")
        if upload is None:
            return jsonify(error="no audio file"), 400
        suffix = Path(upload.filename or "clip.webm").suffix or ".webm"
        raw = tempfile.mktemp(suffix=suffix, prefix="tars_web_")
        upload.save(raw)
        wav = None
        try:
            # OpenAI Whisper accepts webm directly; Vosk needs 16k wav
            engine = s.stt_engine
            if engine == "auto":
                engine = "openai" if s.openai_api_key else "vosk"
            source = raw
            if engine == "vosk" and suffix != ".wav":
                wav = _to_wav(raw)
                if wav is None:
                    return jsonify(error="offline STT needs ffmpeg for browser audio"), 503
                source = wav
            heard = stt.transcribe(source, s)
            if not heard:
                return jsonify(error="could not understand the audio"), 422
            return jsonify(heard=heard, reply=brain.chat(heard))
        except Exception as e:
            log.exception("browser voice chat failed")
            return jsonify(error=str(e)), 500
        finally:
            for p in (raw, wav):
                if p and os.path.exists(p):
                    os.unlink(p)

    @app.post("/api/tts")
    def tts_endpoint():
        """Synthesize text and return the audio file (for browser playback)."""
        text = (request.json or {}).get("text", "").strip()
        if not text:
            return jsonify(error="empty text"), 400
        path = tts.synthesize(text[:600], s)
        if path is None:
            return jsonify(error="no TTS engine available"), 503
        mime = "audio/wav" if path.endswith(".wav") else "audio/mpeg"
        resp = send_file(path, mimetype=mime)
        resp.call_on_close(lambda: os.path.exists(path) and os.unlink(path))
        return resp

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
