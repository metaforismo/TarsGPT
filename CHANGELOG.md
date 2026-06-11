# Changelog

All notable changes to TarsGPT. Dates are merge dates.

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
