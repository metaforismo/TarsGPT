# TARS Complete Build Guide

> From a spool of filament to a talking, walking TARS. Based on the [TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI) **V3** design — the current reference build — with notes on the alternatives.
>
> 🇮🇹 Versione italiana: [GUIDA_COSTRUZIONE.md](../it/GUIDA_COSTRUZIONE.md)
>
> 🛒 Buy everything first: [Shopping List](SHOPPING_LIST.md)

## 1. Know the ecosystem (pick your path)

| Project | Best for | Stack | License |
|---|---|---|---|
| **[TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI)** ⭐ | The full experience | Pi 5, full AI (LLM, TTS, STT, wake word, web UI, skills plugins) | CC BY-NC 4.0 |
| **[latishab/tars](https://github.com/latishab/tars)** | Developers | Hardware daemon on the Pi + gRPC/WebRTC APIs; AI apps run anywhere (`pip install tars-robot[daemon]`); web dashboard at `http://tars.local:8000` | see LEGAL.md |
| **[TARS-WIZARD](https://github.com/DhruvGoswami10/TARS-WIZARD)** | Budget / multilingual | Pi 5, 3 servos, GPT-3.5 personality, voice in EN/ES/FR/DE/**IT**/PT/JA | MIT |
| **This repo (legacy scripts)** | Manual gamepad driving | `TARSRunner.py` + PCA9685, 8BitDo Zero 2 | MIT |

**Why V3 hardware is the one to build:** an extra torso servo for independent leg movement, **no soldering required**, modular electronics, accessible USB/HDMI ports, better cable management, and lower total cost than V1/V2.

### TARS-AI release history (what the software can do)

- **v1.0** — first release: fully local AI with the TARS personality, configurable humor/honesty levels, modular framework.
- **v2.0** — Whisper STT, function calling (Naive Bayes + LLM), voice-controlled movement, DALL·E/Stable Diffusion image generation, Home Assistant integration.
- **v3.0** — ElevenLabs TTS, local Whisper + Vosk, Silero VAD, web chat UI, improved memory/RAG, per-sentence TTS streaming.
- **v4.0** — TARS V2 mechanical redesign, hybrid RAG, Azure/OpenAI TTS options, INA260 battery monitoring, motion-control tab in the web UI.
- **OS Amelia** (2026, current) — skills plugin architecture, streaming LLM with sentence-based TTS, speaker identification, memory/knowledge-graph dashboard, CNN/ONNX wake word ("Atomik"), Pi Zero 2 support, Discord/music/radio/camera skills, browser voice mode, 15 UI themes.

Full changelogs: [GitHub releases](https://github.com/TARS-AI-Community/TARS-AI/releases) · [docs site](https://docs-tars-ai.vercel.app/releases).

## 2. 3D print the parts

1. Get the **V3 STL files** from the [TARS-AI repo](https://github.com/TARS-AI-Community/TARS-AI) (`3D Printer Files`, V3 branch). A static (non-motorized) version also exists if you only want a display piece.
2. **Print the calibration guide first.** The design assumes ±0.02 mm tolerance; if the calibration part doesn't fit, tune your flow/scale before printing 1+ kg of parts.
3. Slicer settings (official): **0.2 mm** layers, **3+ walls**, **20% gyroid** infill, **5** top/bottom layers, **no brim**, **automatic tree supports** with **support threshold angle 10°** so supports don't grow inside screw holes.
4. **Don't rotate the parts** — they are pre-oriented so layer lines look right on the visible faces.
5. Material: **PETG** for anything structural; TPU for the foot pads; metallic PLA or paint for the hull panels — see the [finishing section of the Shopping List](SHOPPING_LIST.md#7-the-metal-look--how-to-get-the-movie-finish-).

## 3. Electronics

⚠️ **Set the XL4015 buck converter to 6.2 V with a multimeter before connecting any servo.** Servos die at 12 V.

1. Power chain: 12 V battery → rocker switch → splits into (a) XL4015 buck @ **6.2 V** → PCA9685 V+ servo rail, and (b) USB regulator @ 5 V → Raspberry Pi USB-C.
2. PCA9685 → Pi via I2C (SDA/SCL/3V3/GND dupont wires). Build a tidy loom with the heat-shrink.
3. Servos plug into PCA9685 channels (V3 docs map the channels; the legacy code in this repo uses 0–2 for drive/lift and 3–8 for arms).
4. DSI display ribbon → Pi DSI port; camera → camera port; USB sound card + mic → USB; speaker → sound card via the 8 Ω 5 W speaker.
5. Optional INA260 (the only soldering in the build) goes in series with the battery for fuel-gauge readings.

## 4. Mechanical assembly

Follow the [V3 wiki](https://github.com/TARS-AI-Community/TARS-AI/wiki/V3) step by step. Order that works:

1. **Electronics tray** — buck converters, Pi, PCA9685 mounted in the chassis.
2. **Torso** — chassis halves, leg mounts with the linear-motion mechanism, main servos (M3×20 screws) with modified horns, hull panels.
3. **Legs** — speaker in the leg, TPU foot pads, lower legs to hull (M3×16 screws).
4. **Arms (optional)** — 10×3 mm magnets for the hands, MG90S servos in forearms/hands, servo extension cables routed through the torso.
5. Battery strapped in with the Velcro; rocker switch in its slot.

## 5. Software

### Path A — TARS-AI V3 (recommended)

```bash
# 1. Flash Raspberry Pi OS 64-bit with Raspberry Pi Imager
#    Enable I2C, SPI, camera in raspi-config; add the DSI overlay to config.txt

# 2. Install
git clone -b V3 https://github.com/TARS-AI-Community/TARS-AI
cd TARS-AI
./Install.sh

# 3. Configure .env with your API keys
#    OPENAI_API_KEY  (required)
#    ELEVENLABS_API_KEY  (recommended for the movie voice)

# 4. Calibrate the servos BEFORE first run
python app-servotester.py

# 5. Launch
./tars-launcher.sh
```

You get: the web dashboard, voice interaction with wake word, the TARS personality (adjustable humor — *"What's your humor setting, TARS?" "That's 100 percent."*), vision, and the skills system.

### Path B — latishab/tars (distributed)

```bash
pip install "tars-robot[daemon]"   # on the Pi
```

The daemon exposes gRPC (`:50051`) and WebRTC (`:8000`) so you can run the AI brain on a PC/server and keep the Pi light. Dashboard at `http://tars.local:8000`. The `tars-conversation-app` adds LLM+STT+TTS voice AI.

### Path C — Legacy gamepad control (this repo)

The original Charles Diaz-style control stack: pair an 8BitDo Zero 2, then:

```bash
pip install evdev adafruit-pca9685
python TARSRunner.py
```

D-pad up = step forward, left/right = turn, down = pose, triggers/face buttons = arms. Check `/dev/input/event*` for your gamepad's device number. This is great for testing the mechanics before installing the AI stack.

## 6. Calibration & first steps

1. With the hull open, run the servo tester and find each servo's neutral/min/max PWM values; the legacy `ServoController.py` shows the kind of values to expect (e.g. neutral height 275, up 205, down 450).
2. Tighten servo horns only after centering.
3. First walk test on carpet (more grip, falls hurt less). The V3 gait lands flush on the torso, which improves walking across surfaces with different friction.
4. Tune the personality in the web UI (humor %, honesty %, voice).

## 7. License & credits

- **TARS-AI** content/design: **CC BY-NC 4.0** — personal/educational builds and modifications are fine, **selling printed parts, kits, or finished robots is not**. Attribution required (see their [ATTRIBUTION.md](https://github.com/TARS-AI-Community/TARS-AI)).
- Original build: **Charles Diaz** — [Hackster.io guide](https://www.hackster.io/charlesdiaz/how-to-build-your-own-replica-of-tars-from-interstellar-224833).
- Community: [TARS-AI Discord](https://discord.gg/AmE2Gv9EUt) · [Wiki](https://github.com/TARS-AI-Community/TARS-AI/wiki) · [docs-tars-ai.vercel.app](https://docs-tars-ai.vercel.app)

*Honesty setting: 90%. Good luck with the build.*
