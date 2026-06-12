# Changelog

All notable changes to TarsGPT. Dates are merge dates.

## 1.2.0 — 2026-06

The "OS" release — everything needed to treat TARS as an appliance:

- **TarsGPT OS image** (experimental): a GitHub Actions workflow builds a
  flashable Raspberry Pi OS image with the runtime, dependencies, I2C and
  autostart preinstalled (Actions -> "TarsGPT OS image")
- **One-command appliance**: `./install.sh --robot` enables I2C and
  installs/enables the systemd service on any stock Pi
- **Discord notifications**: `discord_send` skill + automatic fall and
  low-battery alerts to a webhook (`DISCORD_WEBHOOK`) - no bot token
- **Remote Python client** (`tars.client.TarsClient`): chat, move,
  calibrate and read sensors over HTTP from any machine
- **Pi Zero 2 W lite profile** documented (EN/IT)
- Skipped on purpose: music generation (no keyless API worth shipping)
  and RetroPie launching (out of scope for a no-arms robot)
- 21 built-in skills; suite at 68 tests

## 1.1.0 — 2026-06

Feature parity sweep against the reference community project's skill set —
all original implementations:

- **`web_search` skill**: keyless factual lookups (DuckDuckGo Instant
  Answers with Wikipedia fallback) so TARS can answer beyond its training
- **`calculate` skill**: exact arithmetic via a whitelisted AST evaluator
  (their sandbox-exec idea, reduced to what is provably safe)
- **Network camera** (`TARS_CAMERA_URL`): an RTSP/HTTP camera (or an old
  phone) becomes TARS's eyes for `look` and camera-rewarded gait training,
  with hard timeouts and local-camera fallback
- **Web servo calibration**: Calibration panel in the dashboard — pick a
  channel, nudge the PWM live, save into any named calibration slot
  (`POST /api/calibrate`)
- **Knowledge graph view**: the dashboard now renders facts as a small
  force-directed graph
- 20 built-in skills; suite at 65 tests

## 1.0.0 — 2026-06

**First public release.** A complete, tested, self-maintained TARS project:

- **Runtime**: streaming voice AI (wake word, follow-up conversation,
  Whisper/Vosk STT, ElevenLabs/OpenAI/Piper/espeak TTS), 18 plugin skills,
  semantic memory + knowledge graph, character cards (TARS/CASE/KIPP),
  speaker ID, web dashboard with browser voice mode, onboard movie-style
  display, gamepad, simulation mode, doctor/benchmark self-tests
- **Movement, balance-first (no arms)**: step, turns, lateral strafing,
  choreographed sequences; sinusoidal easing; IMU fall watchdog
- **Gait learning with verifiable rewards**: tape-measure, camera
  (calibrated to cm) or domain-randomized MuJoCo pre-filter with sim
  calibration and Spearman honesty check; live learning curve
- **This release**: optional HTTPS (`TARS_TLS=1`) so the browser microphone
  works from any device on the LAN, and the dashboard now restores the
  recent conversation on load
- **Project**: bilingual docs (EN/IT), cost estimates, CI (lint + 57 tests
  + install on 3.11/3.12), automatic releases, Dependabot, pre-commit

## Development history (pre-1.0)

Internal iteration numbers (formerly 1.0–1.8.2) leading to the first
public release.

### 0.8.2 — 2026-06

- **Automatic releases**: a version bump merged to `main` now creates the
  tag and GitHub Release by itself (CHANGELOG notes, duplicate-safe);
  manual dispatch remains available

### 0.8.1 — 2026-06

Repo hygiene release.

- **One-click releases**: `Release` workflow (Actions tab) creates the tag
  and GitHub Release with notes extracted from this file
- `workflow_dispatch` on CI (manual re-runs from the UI)
- `CONTRIBUTING.md` (project scope, dev setup, PR checklist, release how-to)
- Dependabot (pip + actions, weekly) and pre-commit config (ruff + basics)
- `tars --version`

### 0.8.0 — 2026-06

- **Lateral movement**: `strafe_left`/`strafe_right` composite gaits
  (turn–step–counter-turn; the leg DOF cannot crab-walk directly), exposed
  in the `move` skill, dashboard buttons, gamepad triggers (replacing arm
  nudges, per the no-arms focus) and sequences (new `slalom`)
- Best practices: ruff lint step added to CI, ruff configured in
  pyproject; suite grown to 56 tests
- Merged to `main`

### 0.7.0 — 2026-06

Balance-first release (the project now explicitly targets the no-arms build).

- **Fall watchdog** (runtime): with an MPU-6050, a confirmed fall relaxes
  the leg servos, announces it, and re-arms when set upright
- **Sim accuracy**: servo slew-rate limiting with a gravity-assisted
  asymmetric lift (raise servo-limited at 0.4 m/s, drop at 2.0 m/s) -
  verified to preserve a live, realistic parameter landscape
- **Sim calibration** (`--fit-sim`): random search over friction/strength/
  speed constants maximizing Spearman correlation with your logged real
  sessions; persisted and used to recenter domain randomization
- **Efficiency**: physics compiled once per world and reused via cached
  settled-state reset; fail-fast on falls - ~190 ms per candidate
  (6 worlds x 3 steps), ~18,500 candidates/hour on a laptop
- New gait parameter `bump_pause` (pre-bump settle), searchable and active
  on the real robot too; `--robustness` knob and stability-first preset
- Suite grown to 55 tests

### 0.6.0 — 2026-06

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

### 0.5.0 — 2026-06

- **Stability tax**: during training the gyro is sampled while each
  candidate walks; mean angular rate x `--wobble-weight` (default 0.01) is
  subtracted, so equally-fast but smoother gaits win
- **`tars --benchmark`**: times LLM (first token + full reply), TTS
  synthesis and STT on the configured engines; unconfigured stages skip
- **Onboard display waveform**: animated bars tied to the voice state
  (speaking / listening / thinking / idle)
- Suite grown to 45 tests

### 0.4.0 — 2026-06

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

### 0.3.0 — 2026-06

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

### 0.2.0 — 2026-06

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

### 0.1.0 — 2026-06

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

### 0.0.0 — 2026-06

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
