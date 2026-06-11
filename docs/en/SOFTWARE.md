# TARS Software — Architecture & Manual

> The `tars/` package in this repo is an **original, self-contained implementation** of a full AI robot runtime: wake word, speech recognition, LLM personality with tool-calling, text-to-speech, servo gaits, gamepad driving and a web dashboard. 🇮🇹 [Versione italiana](../it/SOFTWARE.md)

## Feature overview

| Feature | How it works | Module |
|---|---|---|
| **Wake word** ("TARS") | Offline, Vosk small model with a restricted grammar | `tars/voice.py` |
| **Speech-to-text** | OpenAI Whisper API or fully offline Vosk | `tars/stt.py` |
| **AI personality** | OpenAI chat with a TARS persona; humor/honesty/sarcasm 0–100%, adjustable live (even by *asking TARS* to change them — it has a `set_personality` tool) | `tars/llm.py`, `tars/personality.py` |
| **Voice-controlled movement** | The LLM calls a `move` tool (step/turn/pose) when you ask it to move | `tars/llm.py` → `tars/movement/gaits.py` |
| **Long-term memory** | The LLM stores facts with a `remember` tool; persisted to `data/memory.json` and injected into every conversation | `tars/memory.py` |
| **Text-to-speech** | ElevenLabs (closest to the movie voice) → OpenAI TTS → espeak-ng fallback chain | `tars/tts.py` |
| **Multi-language** | Set `TARS_LANGUAGE=it` (or en/es/fr/de/pt/ja): replies, STT and TTS all switch | `tars/config.py` |
| **Web dashboard** | Chat, movement pad, voice control, personality sliders, live status | `tars/web/` |
| **Gamepad driving** | 8BitDo Zero 2 via evdev: d-pad = walk/turn/pose, buttons = arms | `tars/movement/gamepad.py` |
| **Walking gaits** | Lift → leg rotation → torso bump → parallel return; turns and the "monolith" pose | `tars/movement/gaits.py` |
| **Simulation mode** | No hardware? Everything runs with logged servo moves (`--sim`) | `tars/movement/driver.py` |
| **Servo calibration** | Interactive PWM tester with safe limits | `servo_tester.py` |

## Architecture

```
                ┌─────────────────────────────────────────┐
   microphone ─▶│ VoiceLoop: wake word ▶ record ▶ STT     │
                └──────────────┬──────────────────────────┘
                               ▼
  web chat ───▶ ┌─────────────────────────────────────────┐      ┌─────────────┐
  (Flask UI)    │ Brain (LLM + persona + memory)          │─────▶│ TTS ▶ speaker│
                │   tools: move / remember / personality  │      └─────────────┘
                └──────────────┬──────────────────────────┘
                               ▼
  gamepad ────▶ ┌─────────────────────────────────────────┐
  (evdev)       │ Gaits ▶ ServoDriver ▶ PCA9685 ▶ servos  │
                └─────────────────────────────────────────┘
```

Every layer degrades gracefully: no PCA9685 → simulation; no Vosk → push-to-talk from the web UI; no ElevenLabs → OpenAI TTS; no API keys at all → offline Vosk + espeak-ng.

## Installation

```bash
git clone https://github.com/metaforismo/TarsGPT
cd TarsGPT
./install.sh                 # apt deps + venv + pip; detects a Raspberry Pi
cp .env.example .env         # then add your OPENAI_API_KEY
```

## Running

```bash
source .venv/bin/activate
python -m tars.app                  # full robot
python -m tars.app --sim            # on a laptop, no hardware
python -m tars.app --no-voice       # text/web only
python servo_tester.py              # calibrate servos first!
```

Dashboard: `http://<pi-address>:8000`

### First-run checklist

1. `sudo raspi-config` → enable **I2C** (and the camera if installed).
2. `python servo_tester.py` → find min/neutral/max PWM for every channel; **never force a servo past a mechanical stop**.
3. Put your calibrated values in `data/settings.json` under `"pwm"`.
4. Start with `--no-voice`, verify movement from the dashboard.
5. Add the API keys, enable voice, say "TARS".

## HTTP API

| Endpoint | Method | Body | Purpose |
|---|---|---|---|
| `/api/chat` | POST | `{"message": "..."}` | Talk to TARS, returns `{"reply": ...}` |
| `/api/move` | POST | `{"action": "step_forward\|turn_left\|turn_right\|pose\|neutral"}` | Drive the body |
| `/api/settings` | GET/POST | `{"humor": 75, ...}` | Read/update personality |
| `/api/status` | GET | — | Voice state, sim mode |
| `/api/voice/start\|stop\|ptt` | POST | — | Voice loop control / push-to-talk |

## Configuration reference

All via `.env` (see `.env.example`): `OPENAI_API_KEY`, `TARS_MODEL`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `TARS_LANGUAGE`, `TARS_WAKE_WORD`, `TARS_TTS`, `TARS_STT`, `TARS_SIM`, `TARS_GAMEPAD`, `TARS_WEB_PORT`. Personality and PWM calibration persist in `data/settings.json`; long-term memory in `data/memory.json`.

## Extending TARS

- **New LLM tools** (≈ skills): add a schema to `TOOLS` and a branch in `Brain._run_tool` (`tars/llm.py`). Ideas: weather, timers, Home Assistant, camera snapshot.
- **New gaits**: compose the primitives in `Gaits` (sweeps of the lift/drive servos).
- **The movie voice**: create a custom ElevenLabs voice (deep, dry, slightly clipped) and set `ELEVENLABS_VOICE_ID`.
- **Vision**: the OV5647 camera + `opencv-python` face detection slots naturally into a `look` tool.
