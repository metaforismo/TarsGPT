# TARS Software — Architecture & Manual

> The `tars/` package in this repo is an **original, self-contained implementation** of a full AI robot runtime: wake word, speech recognition, streaming LLM personality with a plugin skill system, sentence-streamed text-to-speech, semantic long-term memory, multimodal vision, servo gaits, gamepad driving, a heartbeat scheduler and a web dashboard. 🇮🇹 [Versione italiana](../it/SOFTWARE.md)

## Feature overview

| Feature | How it works | Module |
|---|---|---|
| **Skills plugin system** | Drop a Python file in `tars/skills/`, decorate a function with `@skill` — it auto-registers as an LLM tool at startup. 7 built-in skills | `tars/skills/` |
| **Streaming voice pipeline** | LLM tokens stream in, get cut at sentence boundaries and spoken immediately — TARS starts answering while still "thinking" the rest | `tars/llm.py` + `tars/speech.py` |
| **Wake word** ("TARS") | Offline, Vosk small model with a restricted grammar | `tars/voice.py` |
| **Speech-to-text** | OpenAI Whisper API or fully offline Vosk | `tars/stt.py` |
| **AI personality** | Humor/honesty/sarcasm 0–100%, adjustable live from the dashboard or by *asking TARS* (`set_personality` skill) | `tars/personality.py`, `tars/skills/persona.py` |
| **Semantic long-term memory** | Notes are embedded (OpenAI `text-embedding-3-small`) and retrieved by cosine similarity against what you just said; offline it falls back to keyword matching. Explicit `remember`/`recall` skills | `tars/memory.py`, `tars/skills/memory_notes.py` |
| **Vision** | `look` skill: camera frame (rpicam/libcamera/fswebcam/OpenCV) → multimodal GPT description, optionally answering a question about the scene | `tars/skills/vision.py` |
| **Voice-commanded movement** | The LLM calls the `move` skill (step/turn/pose) when you ask it to move | `tars/skills/movement.py` → `tars/movement/gaits.py` |
| **Timers & proactive speech** | "TARS, remind me in 10 minutes…" → heartbeat scheduler fires → TARS *speaks up on its own* | `tars/skills/timers.py`, `tars/scheduler.py` |
| **Self-monitoring** | `system_status` skill (battery via INA260, CPU temp, uptime, disk) + a battery watchdog that announces low charge | `tars/skills/system.py` |
| **Text-to-speech** | ElevenLabs (closest to the movie voice) → OpenAI TTS → espeak-ng fallback chain | `tars/tts.py` |
| **Multi-language** | `TARS_LANGUAGE=it` (or en/es/fr/de/pt/ja): replies, STT and TTS all switch | `tars/config.py` |
| **Web dashboard** | Streaming chat (SSE), movement pad, personality sliders, voice control, battery/CPU vitals, memory inspector | `tars/web/` |
| **Gamepad driving** | 8BitDo Zero 2 via evdev: d-pad = walk/turn/pose, buttons = arms | `tars/movement/gamepad.py` |
| **Simulation mode** | No hardware? Everything runs with logged servo moves (`--sim`) | `tars/movement/driver.py` |

## Architecture

```
   microphone ──▶ VoiceLoop ──▶ STT ─┐                       ┌─▶ Speaker ──▶ TTS ──▶ 🔊
                 (wake word)         │   ┌───────────────┐   │   (sentence-streamed)
   web chat ──▶ SSE /api/chat/stream ┼──▶│ Brain (LLM)   │───┤
                                     │   │ + persona     │   └─▶ streamed text to UI
   skills can speak proactively ─────┘   │ + memory      │
   (timers, battery watchdog)            └──────┬────────┘
                                                │ tool calls
                                  ┌─────────────▼─────────────┐
                                  │ Skill registry (plugins)  │
                                  │ move · remember · recall  │
                                  │ set_timer · look ·        │
                                  │ system_status · persona   │
                                  └──────┬──────────┬─────────┘
                                         ▼          ▼
   gamepad (evdev) ────────────▶ Gaits ▶ PCA9685   Scheduler (heartbeat)
```

Every layer degrades gracefully: no PCA9685 → simulation; no Vosk → push-to-talk from the web UI; no ElevenLabs → OpenAI TTS → espeak-ng; no API keys at all → offline Vosk + espeak-ng + keyword memory.

## Installation & running

```bash
git clone https://github.com/metaforismo/TarsGPT
cd TarsGPT
./install.sh                 # apt deps + venv + pip; detects a Raspberry Pi
cp .env.example .env         # add your OPENAI_API_KEY
source .venv/bin/activate
python -m tars.app           # full robot   (--sim on a laptop, --no-voice, --no-web)
python servo_tester.py       # calibrate servos first!
```

Dashboard: `http://<pi-address>:8000`

### First-run checklist

1. `sudo raspi-config` → enable **I2C** (and the camera if installed).
2. `python servo_tester.py` → find min/neutral/max PWM for every channel; **never force a servo past a mechanical stop**.
3. Put your calibrated values in `data/settings.json` under `"pwm"`.
4. Start with `--no-voice`, verify movement from the dashboard.
5. Add the API keys, enable voice, say "TARS".

## Writing a skill (the whole point)

Create `tars/skills/weather.py`:

```python
from . import skill

@skill("weather", "Get the current weather for a city",
       {"type": "object", "properties": {"city": {"type": "string"}},
        "required": ["city"]})
def weather(ctx, city):
    # ctx gives you: settings, memory, gaits, scheduler, speaker (ctx.say(...))
    return f"Sunny in {city}, 22 degrees."   # the LLM weaves this into its reply
```

Restart. That's it — no registration files, no dispatch chain to edit. The LLM now checks the weather when asked.

## HTTP API

| Endpoint | Method | Body | Purpose |
|---|---|---|---|
| `/api/chat` | POST | `{"message": "..."}` | Single-shot reply |
| `/api/chat/stream` | POST | `{"message": "..."}` | **SSE stream** of reply deltas |
| `/api/move` | POST | `{"action": "step_forward\|turn_left\|turn_right\|pose\|neutral"}` | Drive the body |
| `/api/settings` | GET/POST | `{"humor": 75, ...}` | Read/update personality |
| `/api/status` | GET | — | Voice state, sim mode, battery %, CPU temp |
| `/api/memory` | GET | — | Recent turns + long-term notes |
| `/api/voice/start\|stop\|ptt` | POST | — | Voice loop control / push-to-talk |

## Configuration reference

All via `.env` (see `.env.example`): `OPENAI_API_KEY`, `TARS_MODEL`, `TARS_EMBEDDING_MODEL`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `TARS_LANGUAGE`, `TARS_WAKE_WORD`, `TARS_TTS`, `TARS_STT`, `TARS_SIM`, `TARS_GAMEPAD`, `TARS_WEB_PORT`. Personality and PWM calibration persist in `data/settings.json`; long-term memory (with embeddings) in `data/memory.json`.

## Design notes — how this compares to the reference community project

The most complete community implementation organizes its code as `character/memory/modules/skills/stt/tts/www` and pioneered ideas we embraced: a skills plugin system, sentence-based streaming TTS, a heartbeat scheduler, INA260 monitoring. This runtime keeps those ideas but rethinks the execution:

- **One process, ~15 small modules** instead of a large multi-app codebase — easier to read end-to-end and to hack on.
- **Skills are a single decorated function** with auto-discovery; no config files or dispatch chains.
- **Vision uses the multimodal LLM** (one API, can answer questions about the scene) instead of a separate local BLIP captioning model.
- **Memory retrieval is semantic** (embeddings + cosine) with a zero-dependency offline fallback, and the LLM can also search it explicitly via `recall`.
- **Everything degrades gracefully** down to a fully offline, zero-cost stack (Vosk + espeak-ng + keyword memory).
- Same Pi 5 hardware, PCA9685 wiring and PWM calibration model, so it runs on a standard V3-style build unchanged.

Ideas for the next round: speaker identification, a persistent knowledge graph, Home Assistant and music skills, browser-microphone voice mode.
