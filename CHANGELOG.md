# Changelog

All notable changes to TarsGPT. Dates are merge dates.

## 1.6.0 — 2026-06

- **MuJoCo physics pre-filter** (`--reward mujoco`): the exact same Gaits
  code drives a simplified physics model of TARS via a duck-typed driver
  whose `sleep()` advances the simulation - ~30 ms per episode, thousands
  of candidates per hour on a PC
- **Domain randomization**: each candidate scored across N common worlds
  (friction, servo strength, mass); reward = mean − 0.5·std for robustness
- **Honesty check** (`--correlate`): Spearman rank correlation between
  logged real sessions and the sim, with explicit trust thresholds;
  training logs now store candidate parameters to enable it
- Sim results are never auto-saved: the sim proposes, the real-robot
  verification (`measured`/`camera`) disposes
- Architecture: gait pacing now flows through `driver.sleep()`, and
  parallel return phases run sequentially on non-thread-safe drivers
- Suite grown to 49 tests (sim locomotion direction and sensitivity,
  determinism with common random numbers, fall detection, Spearman, log
  replay)

## 1.5.0 — 2026-06

- **Stability tax**: during training the gyro is sampled while each
  candidate walks; mean angular rate x `--wobble-weight` (default 0.01) is
  subtracted, so equally-fast but smoother gaits win
- **`tars --benchmark`**: times LLM (first token + full reply), TTS
  synthesis and STT on the configured engines; unconfigured stages skip
- **Onboard display waveform**: animated bars tied to the voice state
  (speaking / listening / thinking / idle)
- Suite grown to 45 tests

## 1.4.0 — 2026-06

- **`tars --doctor`**: 12-point self-test (I2C, PCA9685, IMU, camera, mic,
  audio out, TTS/STT/LLM, ffmpeg, disk) with fix hints per failure -
  the first thing to run after wiring
- **Camera calibration** (`--calibrate-camera`): one manual slide measures
  px-per-cm; camera rewards then score in real centimeters
- **Wake acknowledgment**: TARS answers the wake word ("Yes?" / "Sì?", per
  language, `TARS_ACK` to customize or disable) before opening the mic
- **Conversation persistence**: the short-term dialog now survives restarts
- IMU driver gains `read_gyro()` (deg/s, wobble inspection)
- Suite grown to 42 tests

## 1.3.0 — 2026-06

- **MPU-6050 IMU support** (`tars/sensors.py`): orientation and fall
  detection over I2C, graceful without the sensor; attitude reported by
  `system_status`
- **Unsupervised gait training**: with the IMU present, `FallGuard`
  automatically replaces the reward with a penalty whenever a candidate
  leaves TARS not-upright (`--no-imu` to disable)
- **Signed camera reward** (`--camera-axis x|-x|y|-y`): walking backwards
  now scores negative
- **Resilient sessions**: a failed capture/measurement skips that candidate
  instead of aborting training
- **Live learning curve**: every evaluation logged to
  `data/gait_training.json`, plotted in the dashboard (`/api/training`)
- Suite grown to 38 tests
- Shopping lists updated: MPU-6050 is now supported, not just roadmap

## 1.2.0 — 2026-06

- **Camera reward** for gait training (`--reward camera`): frames before and
  after each candidate's steps are compared with phase correlation; the
  recovered translation in pixels becomes the reward — no tape measure needed
- **Sinusoidal easing** on all servo sweeps: gentle start, fast mid-travel,
  braking before the stop (capped at 4x dwell) — smoother and kinder to
  gearboxes, endpoints still land exactly
- **Ctrl-C-safe training**: interrupting a hardware session keeps and can
  save the best gait found so far
- `docs/README.md`: bilingual reading-order index of all documentation;
  MPU-6050 IMU added to the shopping list as optional sensor
- Suite grown to 33 tests (synthetic-shift recovery, camera-reward flow,
  easing endpoint exactness and bounds, interrupt handling)

## 1.1.0 — 2026-06

- **Gait learning** (`tars/learn/`): (1+1) evolution strategy over the five
  walking-timing parameters with a physically verifiable reward (measured
  centimeters per step); log-space mutations, 1/5th-success adaptive step,
  results persisted to `data/gait_params.json` and loaded at startup.
  `python -m tars.learn --reward measured` (or `--reward sim` dry-run)
- **Continuous conversation**: after answering, TARS keeps listening for
  `TARS_FOLLOWUP_WINDOW` seconds (default 6) so follow-ups need no wake word
- **Onboard display** (`/display`): movie-style kiosk readout for the DSI
  screen — humor/honesty bars, power, core temp, CRT scanlines; localhost is
  exempt from the dashboard password so the kiosk always works
- Gait timing refactored into tunable parameters (`DEFAULT_GAIT_PARAMS`)
- Lint-clean codebase (ruff); suite grown to 29 tests

## 1.0.0 — 2026-06

The complete overhaul: from a README plus three scripts to a full, tested robot project.

### Runtime (original implementation, `tars/`)
- **18 plugin skills**, auto-discovered from `tars/skills/`: `move`, `perform`
  (choreographed sequences), `remember`/`recall`, `learn_fact`/`query_facts`/
  `forget_facts` (knowledge graph), `set_timer`, `look` (camera + multimodal
  GPT), `generate_image` (DALL·E 3 with dashboard previews), `system_status`,
  `set_volume`, `play_music`/`stop_music`, `home_assistant`,
  `set_personality`, `set_character`, `enroll_speaker`
- **Streaming voice pipeline**: offline wake word (Vosk) → STT (Whisper API or
  local Vosk) → streaming LLM with tool calling → sentence-by-sentence TTS
- **LLM providers**: OpenAI cloud or any OpenAI-compatible local server
  (Ollama, LM Studio, llama.cpp, vLLM) via `TARS_LLM_BASE_URL`, with runtime
  fallback when the server rejects tool calling
- **TTS chain**: ElevenLabs → OpenAI → Piper (free local neural) → espeak-ng
- **Semantic long-term memory** (embeddings + offline keyword fallback) and a
  **persistent knowledge graph** with automatic context injection
- **Character cards** (TARS, CASE, KIPP included) switchable by voice,
  dashboard or API; identity restored at boot without clobbering tuned dials
- **Speaker identification** (experimental): band-energy + pitch fingerprints
- **Heartbeat scheduler**: spoken reminders, low-battery watchdog (INA260)
- **Web dashboard**: SSE streaming chat, browser voice mode with audio
  replies, movement pad, personality sliders, character selector, knowledge
  panel, vitals, optional password login, 4 themes
- **Gamepad** (8BitDo Zero 2) with device autodiscovery; full `--sim` mode

### Hardware safety & robustness
- Servo sweeps interpolate proportionally (asymmetric calibrations land
  exactly on target); arm nudges clamped to safe PWM bounds
- Microphone speech threshold auto-calibrates on ambient noise
- PWM calibration files merge with new defaults; TTS temp files cleaned up;
  music player processes reaped; whole-word knowledge matching

### Project
- Bilingual documentation (EN/IT): build guide, shopping list with 3D printer
  and metal-finish guidance, line-by-line cost estimate, software manual with
  AI-stack matrix and troubleshooting
- `pip install .` packaging with a `tars` console command; systemd unit for
  autostart; GitHub Actions CI; 25-test suite runnable with no hardware or
  API keys
- Original gamepad scripts preserved in `legacy/` (imports fixed)
