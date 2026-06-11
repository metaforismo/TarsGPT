# TARS Software — Architecture & Manual

> The `tars/` package in this repo is an **original, self-contained implementation** of a full AI robot runtime: wake word, speech recognition, streaming LLM personality with a plugin skill system, sentence-streamed text-to-speech, semantic long-term memory, multimodal vision, servo gaits, gamepad driving, a heartbeat scheduler and a web dashboard. 🇮🇹 [Versione italiana](../it/SOFTWARE.md)

## Feature overview

| Feature | How it works | Module |
|---|---|---|
| **Skills plugin system** | Drop a Python file in `tars/skills/`, decorate a function with `@skill` — it auto-registers as an LLM tool at startup. 18 built-in skills | `tars/skills/` |
| **Local or cloud LLM** | OpenAI cloud, or any OpenAI-compatible server — Ollama, LM Studio, llama.cpp, vLLM — via `TARS_LLM_BASE_URL`. A fully offline TARS is possible | `tars/llm.py` |
| **Character cards** | Switchable personas in `characters/*.json` (TARS, CASE, KIPP included): name, persona text, default dials. "Become CASE" works by voice, dashboard or API | `tars/characters.py` |
| **Choreographed sequences** | Named movement routines (greet, wiggle, patrol + your own in `data/sequences.json`); "TARS, do a little dance" → `perform` skill | `tars/movement/sequences.py` |
| **Gait learning** | Verifiable-reward optimization of the walking parameters: the robot walks, you measure the centimeters, the optimizer learns. `python -m tars.learn` | `tars/learn/` |
| **Continuous conversation** | After answering, TARS keeps listening for ~6 s so you can reply without repeating the wake word (`TARS_FOLLOWUP_WINDOW`) | `tars/voice.py` |
| **Onboard display** | `/display`: movie-style readout (name, humor/honesty bars, power, core temp, clock) for the robot's DSI screen in kiosk mode | `tars/web/static/display.html` |
| **Piper TTS** | Free, local neural text-to-speech: install `piper`, download a voice, set `TARS_PIPER_VOICE` — sits in the fallback chain before espeak | `tars/tts.py` |
| **Volume control** | `set_volume` skill via amixer/pactl | `tars/skills/system.py` |
| **Image generation** | `generate_image` skill (DALL·E 3): saved under `data/images/`, previewed inline in the dashboard chat | `tars/skills/images.py` |
| **Dashboard login** | Optional shared password (`TARS_WEB_PASSWORD`) gating all API routes with session cookies | `tars/web/server.py` |
| **UI themes** | 4 dashboard themes (deep space, amber CRT, terminal green, daylight), persisted per browser | `tars/web/static/` |
| **Knowledge graph** | Structured subject-relation-object facts (`learn_fact`/`query_facts`/`forget_facts`), deduplicated, persisted, auto-injected into the context when relevant, browsable in the dashboard | `tars/knowledge.py` |
| **Speaker identification** *(experimental)* | Band-energy + pitch voice fingerprints; enroll with "learn my voice, I'm Francesco", then TARS knows who's talking and the LLM sees `[Francesco is speaking]` | `tars/speakerid.py`, `tars/skills/speakers.py` |
| **Browser voice mode** | Talk to TARS from any phone/PC on the network: the dashboard records your mic, the robot transcribes, replies and streams the audio back to the browser | `/api/voice/chat` + `/api/tts` |
| **Home Assistant** | `home_assistant` skill: turn on/off/toggle/query any entity via the HA REST API (`HA_URL`/`HA_TOKEN`) | `tars/skills/home_assistant.py` |
| **Music** | `play_music`/`stop_music`: built-in radio stations (lofi, jazz, classical, synthwave), stream URLs or local files via mpv | `tars/skills/music.py` |
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
                                  │ Skill registry (14 plugins)│
                                  │ move · remember · recall  │
                                  │ set_timer · look · persona│
                                  │ system_status · learn_fact│
                                  │ query/forget_facts · music│
                                  │ home_assistant · enroll   │
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

## Choosing your AI stack

| Stack | Brain | Voice | STT | Quality | Running cost | Needs |
|---|---|---|---|---|---|---|
| **Cloud** (default) | OpenAI `gpt-4o-mini` | ElevenLabs | Whisper API | Best, movie-like voice | ~€2–10/month | API keys |
| **Hybrid** ⭐ | OpenAI `gpt-4o-mini` | **Piper** (local) | Whisper API | Excellent, free voice | ~€1–5/month | OpenAI key |
| **Fully local** | Ollama via `TARS_LLM_BASE_URL` | Piper | Vosk | Good, private, offline | **€0** | A PC on the network (or a patient Pi) |

### Piper voice in two minutes

```bash
pip install piper-tts                       # provides the `piper` command
# download a voice from https://github.com/rhasspy/piper/blob/master/VOICES.md
# e.g. en_US-ryan-low (English) or it_IT-riccardo-x_low (Italian)
mkdir -p ~/voices && cd ~/voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/low/en_US-ryan-low.onnx{,.json}
echo "TARS_PIPER_VOICE=$HOME/voices/en_US-ryan-low.onnx" >> .env
```

Piper slots into the fallback chain automatically (before espeak), so cloud engines are used when configured and Piper covers everything else.

### Fully local with Ollama

```bash
# on any PC on your network (or the Pi itself with a small model)
ollama serve && ollama pull llama3.1:8b
# in TARS's .env:
TARS_LLM_BASE_URL=http://<pc-address>:11434/v1
TARS_MODEL=llama3.1:8b
TARS_STT=vosk
```

If the local server doesn't support tool calling, TARS detects it at runtime and degrades to plain conversation instead of failing (skills are temporarily disabled).

## Teaching TARS to walk better (verifiable reward)

The walking gait depends on five timing parameters (torso lift speed, leg
rotation speed, the pivot "bump", the recovery, the return). The factory
values are a compromise; your build — its weight, servos, floor — has its own
optimum. `tars/learn` finds it with a **(1+1) evolution strategy** whose
reward is *physically verifiable*: centimeters actually walked.

```bash
python -m tars.learn --reward measured --iterations 12 --steps 3
```

For each candidate gait the robot walks 3 steps; you read the distance off a
tape measure (or floor tiles) and type it in — negative if it fell. The
optimizer mutates the parameters in log-space with an adaptive step size
(1/5th-success rule: explore wider while improving, narrow when stalling) and
saves the best gait to `data/gait_params.json`, loaded automatically at every
start. Budget ~10 minutes and ~2 m of free floor for a session; you can stop
and resume — training always starts from the current best.

**Hands-free variant** — let the camera be the judge:

```bash
python -m tars.learn --reward camera --iterations 12 --steps 3
```

A frame is grabbed before and after each candidate's steps; phase correlation
between the two recovers the camera translation in pixels — proportional to
the ground covered when the camera watches a textured static scene (pointing
it at the floor works best). Pixels are a relative unit, which is all the
optimizer needs. Supervise the first sessions: a fall produces a garbage
frame, and the tape measure (`--reward measured`) remains the ground truth.

`--reward sim` runs the same machinery against a deterministic surrogate
landscape (used by the test suite to verify the optimizer actually converges)
— useful to dry-run the whole loop off-robot with `--sim`. **Ctrl-C is safe
in every mode**: training stops and keeps the best gait found so far.

## The onboard screen

Point the robot's own browser at the readout for the full movie effect:

```bash
chromium-browser --kiosk --noerrdialogs http://localhost:8000/display
```

Black background, cyan monospace, humor/honesty bars, power and core temp,
CRT scanlines, blinking cursor. The name pulses while TARS is listening.
Localhost is exempt from the dashboard password, so the kiosk works even
with `TARS_WEB_PASSWORD` set.

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
| `/api/knowledge` | GET | — | Knowledge-graph triples |
| `/api/voice/chat` | POST | multipart `audio` file | **Browser voice mode**: audio in → `{heard, reply}` |
| `/api/tts` | POST | `{"text": "..."}` | Synthesized audio file (browser playback) |
| `/api/voice/start\|stop\|ptt` | POST | — | Voice loop control / push-to-talk |
| `/api/characters` | GET/POST | `{"name": "case"}` | List / switch character cards |
| `/api/login` | POST | `{"password": "..."}` | Session login when `TARS_WEB_PASSWORD` is set |
| `/images/<file>` | GET | — | Generated images |

## Configuration reference

All via `.env` (see `.env.example`): `OPENAI_API_KEY`, `TARS_LLM_BASE_URL`, `TARS_MODEL`, `TARS_EMBEDDING_MODEL`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `TARS_PIPER_VOICE`, `TARS_LANGUAGE`, `TARS_WAKE_WORD`, `TARS_TTS`, `TARS_STT`, `TARS_SIM`, `TARS_GAMEPAD`, `TARS_WEB_PORT`, `TARS_WEB_PASSWORD`, `HA_URL`, `HA_TOKEN`, `TARS_MUSIC_DIR`. Personality and PWM calibration persist in `data/settings.json`; long-term memory (with embeddings) in `data/memory.json`.

## Autostart on boot

```bash
sudo cp deploy/tars.service /etc/systemd/system/   # adjust paths inside if needed
sudo systemctl daemon-reload
sudo systemctl enable --now tars
journalctl -u tars -f                               # live logs
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Servos jitter or twitch | Power problem 9 times out of 10: buck converter not at **6.2 V**, undersized battery, or missing **common ground** between PCA9685 V+ rail and the Pi |
| `No PCA9685 found` on the robot | Enable I2C (`sudo raspi-config`), then `i2cdetect -y 1` should show `0x40`; check SDA/SCL wiring |
| Microphone not picked up | `arecord -l` to list devices; set the USB card as default in `~/.asoundrc` |
| No sound | `aplay -l`, test with `speaker-test -t wav`; make sure the USB sound card, not HDMI, is the default sink |
| Wake word never triggers | Vosk downloads its model on first use — needs internet once; or set `TARS_STT=openai` and use push-to-talk |
| Browser mic button does nothing | Browsers only allow microphone on HTTPS or localhost. Easiest workaround: `ssh -L 8000:localhost:8000 pi@tars.local`, then open `http://localhost:8000` |
| Gamepad not detected | It is autodetected now; if it still fails, find it with `python -c "import evdev; print(evdev.list_devices())"` and set `TARS_GAMEPAD` |
| Replies are slow | Use `gpt-4o-mini` (default), keep ElevenLabs (it streams per sentence), or go local with Ollama on a PC and `TARS_LLM_BASE_URL` |

## Design notes — how this compares to the reference community project

The most complete community implementation organizes its code as `character/memory/modules/skills/stt/tts/www` and pioneered ideas we embraced: a skills plugin system, sentence-based streaming TTS, a heartbeat scheduler, INA260 monitoring. This runtime keeps those ideas but rethinks the execution:

- **One process, ~15 small modules** instead of a large multi-app codebase — easier to read end-to-end and to hack on.
- **Skills are a single decorated function** with auto-discovery; no config files or dispatch chains.
- **Vision uses the multimodal LLM** (one API, can answer questions about the scene) instead of a separate local BLIP captioning model.
- **Memory retrieval is semantic** (embeddings + cosine) with a zero-dependency offline fallback, and the LLM can also search it explicitly via `recall`.
- **Everything degrades gracefully** down to a fully offline, zero-cost stack (Vosk + espeak-ng + keyword memory).
- Same Pi 5 hardware, PCA9685 wiring and PWM calibration model, so it runs on a standard V3-style build unchanged.

All of the headline community features now have an original counterpart here: skills, streaming TTS, scheduler, battery monitoring, knowledge graph, speaker ID, Home Assistant, music and browser voice mode — verified by the test suite in `tests/run_tests.py` (`python tests/run_tests.py`, no hardware or API keys needed).
