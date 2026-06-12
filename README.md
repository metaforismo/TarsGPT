# TarsGPT — A Complete AI Robot Inspired by TARS

[![CI](https://github.com/metaforismo/TarsGPT/actions/workflows/ci.yml/badge.svg)](https://github.com/metaforismo/TarsGPT/actions/workflows/ci.yml)

🇬🇧 English | 🇮🇹 [Italiano più sotto](#tarsgpt--un-robot-ia-completo-ispirato-a-tars)

![TARS](https://github.com/user-attachments/assets/cb7f6acf-b7c4-41ff-ab1a-2640e8610c68)

TarsGPT is a **complete, self-contained robot project**: an original Python runtime (voice AI, personality, movement, web dashboard) plus full bilingual documentation to design, print, wire, assemble and finish a walking TARS-style robot. Based on [**Charlie Diaz's original TARS replica**](https://www.hackster.io/charlesdiaz/how-to-build-your-own-replica-of-tars-from-interstellar-224833) — the idea that started it all — rebuilt as an original codebase and extended with everything below.

🌐 **Website**: [tarsgpt.vercel.app](https://tarsgpt.vercel.app) — with an interactive 3D exploded view of the robot (source in [`site/`](site/), one-click deploy on Vercel)

## ✨ Features

- 🧩 **Skills plugin system** — drop a decorated Python function in `tars/skills/` and it becomes an LLM tool automatically; 21 built-in skills
- 🖥️ **Local or cloud LLM** — OpenAI, or fully local via Ollama/LM Studio (`TARS_LLM_BASE_URL`); free local neural voice with Piper TTS
- 🎭 **Character cards** — switch between TARS, CASE and KIPP (or your own) by voice or dashboard
- 🕺 **Choreographed sequences** — greet, wiggle, patrol or your own routines ("TARS, do a little dance")
- 🧬 **Gait learning** — verifiable-reward optimization: the robot walks, you measure, it learns your floor (`python -m tars.learn`)
- 🪐 **Physics pre-filter** — the same gait code runs in a domain-randomized MuJoCo sim: thousands of candidates per hour, honesty-checked against your real sessions (`--reward mujoco`, `--correlate`)
- 💬 **Continuous conversation** — after answering, TARS keeps listening so you can reply without the wake word
- 📟 **Onboard display** — movie-style `/display` readout for the robot's DSI screen (kiosk mode)
- 🕸️ **Knowledge graph** — structured facts ("Francesco owns a P1S") learned, deduplicated, persisted and injected when relevant
- 🪪 **Speaker identification** *(experimental)* — enroll your voice and TARS knows who's talking
- 📱 **Browser voice mode** — talk to TARS from any phone/PC on the network, replies stream back as audio
- 🏠 **Home Assistant, music, images, volume** — smart-home control, radio/local music, DALL·E previews in chat, mixer control
- 🔐 **Dashboard login & themes** — optional password gate, 4 UI themes; autostart via systemd (`deploy/tars.service`)
- ⚡ **Streaming voice pipeline** — the reply is spoken sentence by sentence *while the LLM is still generating*; the web chat streams too (SSE)
- 🗣️ **Hands-free voice AI** — offline wake word ("TARS"), Whisper or Vosk speech recognition, ElevenLabs/OpenAI/espeak text-to-speech with automatic fallback
- 🧠 **Adjustable personality** — humor, honesty and sarcasm from 0 to 100%, changeable from the dashboard or by simply *asking the robot*
- 💾 **Semantic long-term memory** — notes retrieved by embedding similarity (offline keyword fallback), plus explicit `remember`/`recall` skills
- 👁️ **Vision** — the `look` skill captures a camera frame and describes the scene via multimodal GPT
- ⏰ **Timers & proactive speech** — heartbeat scheduler: reminders and low-battery warnings spoken unprompted
- 🦿 **Walking gaits** — step, turns, lateral strafing, "monolith" pose; voice-commanded ("TARS, sidestep right") via LLM tool-calling
- 🌐 **Web dashboard** — streaming chat, movement pad, personality sliders, voice control, battery/CPU vitals at `http://<pi>:8000`
- 🎮 **Gamepad driving** — 8BitDo Zero 2 support
- 🌍 **Multilingual** — English, Italian, Spanish, French, German, Portuguese, Japanese
- 💻 **Simulation mode** — develop everything on a laptop, no hardware needed (`--sim`)

## 🚀 Quick start

```bash
git clone https://github.com/metaforismo/TarsGPT
cd TarsGPT
./install.sh
cp .env.example .env        # add your OPENAI_API_KEY
source .venv/bin/activate
python -m tars.app --sim    # try it now, robot optional
```

## 📚 Documentation

Reading-order index: [docs/README.md](docs/README.md)

| English | Italiano |
|---|---|
| [Software architecture & manual](docs/en/SOFTWARE.md) | [Architettura software e manuale](docs/it/SOFTWARE.md) |
| [Complete build guide](docs/en/BUILD_GUIDE.md) | [Guida completa alla costruzione](docs/it/GUIDA_COSTRUZIONE.md) |
| [Shopping list, printers, metal finish](docs/en/SHOPPING_LIST.md) | [Lista acquisti, stampanti, effetto metallo](docs/it/LISTA_ACQUISTI.md) |
| [Cost estimate, line by line](docs/en/COST_ESTIMATE.md) | [Stima dei costi, voce per voce](docs/it/STIMA_COSTI.md) |

## 🔩 Hardware at a glance

Raspberry Pi 5 (8 GB) · PCA9685 servo driver · 4–6 MG996R + 4 MG90S servos · 5" DSI touchscreen · camera · 12 V battery with dual buck converters · ~1.5 kg PETG. Full details and totals (from **≈ €280** if you own a printer) in the [cost estimate](docs/en/COST_ESTIMATE.md).

## 📁 Repository layout

```
tars/                # the robot runtime (original implementation)
  app.py             # entrypoint: python -m tars.app
  llm.py             # streaming LLM brain with skill tool-calling
  skills/            # plugin skills: move, recall, look, timers, music, HA…
  learn/             # gait optimizer (verifiable-reward evolution strategy)
  speech.py          # sentence-streaming TTS pipeline
  scheduler.py       # heartbeat scheduler (timers, battery watchdog)
  memory.py          # semantic long-term memory (embeddings + offline fallback)
  knowledge.py       # persistent knowledge graph (s-r-o triples)
  speakerid.py       # experimental voice fingerprinting
  voice.py stt.py tts.py audio.py
  movement/          # PCA9685 driver, gaits, gamepad
  web/               # Flask dashboard (SSE chat, browser voice mode)
characters/          # persona cards: tars, case, kipp (add your own)
deploy/tars.service  # systemd unit for autostart on boot
tests/run_tests.py   # full test suite (no hardware/keys needed)
servo_tester.py      # interactive servo calibration
legacy/              # the original gamepad-only scripts (kept for reference)
docs/                # bilingual documentation (en/, it/)
```

## Credits & license

- **The idea**: [Charlie Diaz's original TARS replica](https://www.hackster.io/charlesdiaz/how-to-build-your-own-replica-of-tars-from-interstellar-224833) — this project started from his concept and grew into the full AI runtime, gait learning, balance-first design and documentation you see here.
- **The printable chassis**: referenced from the [TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI) (CC BY-NC 4.0 — attribution required for the printed parts). The full STL set is downloaded from their repo; this repo ships one STEP reference file (`525125.STEP`).
- **The code in this repository**: original implementation, MIT (see [LICENSE](LICENSE)).
- TARS is a character from Christopher Nolan's *Interstellar*; this is a non-commercial fan project.

---

# TarsGPT — Un Robot IA Completo Ispirato a TARS

TarsGPT è un **progetto robot completo e autonomo**: un runtime Python originale (IA vocale, personalità, movimento, dashboard web) più documentazione bilingue completa per progettare, stampare, cablare, assemblare e rifinire un robot stile TARS che cammina. Basato sulla [**replica TARS originale di Charlie Diaz**](https://www.hackster.io/charlesdiaz/how-to-build-your-own-replica-of-tars-from-interstellar-224833) — l'idea da cui tutto è partito — ricostruita come codebase originale ed estesa con tutto ciò che segue.

🌐 **Sito web**: [tarsgpt.vercel.app](https://tarsgpt.vercel.app) — con vista 3D interattiva esplodibile del robot (sorgente in [`site/`](site/))

## ✨ Funzionalità

- 🧩 **Sistema di skill a plugin** — metti una funzione Python decorata in `tars/skills/` e diventa automaticamente un tool dell'LLM; 21 skill integrate
- 🖥️ **LLM locale o cloud** — OpenAI, oppure tutto in locale via Ollama/LM Studio (`TARS_LLM_BASE_URL`); voce neurale locale gratuita con Piper TTS
- 🎭 **Character card** — passa da TARS a CASE a KIPP (o ai tuoi) a voce o da dashboard
- 🕺 **Sequenze coreografate** — greet, wiggle, patrol o le tue routine ("TARS, balla")
- 🧬 **Apprendimento dell'andatura** — ottimizzazione con reward verificabile: il robot cammina, tu misuri, lui impara il tuo pavimento (`python -m tars.learn`)
- 🪐 **Pre-filtro fisico** — lo stesso codice d'andatura gira in un sim MuJoCo con domain randomization: migliaia di candidate l'ora, con controllo di onestà sulle tue sessioni reali (`--reward mujoco`, `--correlate`)
- 💬 **Conversazione continua** — dopo la risposta TARS resta in ascolto: replichi senza ripetere la wake word
- 📟 **Schermo di bordo** — readout `/display` in stile film per il display DSI del robot (modalità kiosk)
- 🕸️ **Knowledge graph** — fatti strutturati ("Francesco possiede una P1S") appresi, deduplicati, persistenti e iniettati quando rilevanti
- 🪪 **Identificazione speaker** *(sperimentale)* — registra la tua voce e TARS sa chi sta parlando
- 📱 **Voce dal browser** — parla con TARS da qualsiasi telefono/PC in rete, le risposte tornano come audio
- 🏠 **Home Assistant, musica, immagini, volume** — domotica, radio/musica locale, anteprime DALL·E in chat, controllo mixer
- 🔐 **Login e temi dashboard** — protezione con password opzionale, 4 temi UI; avvio automatico via systemd (`deploy/tars.service`)
- ⚡ **Pipeline vocale in streaming** — la risposta viene pronunciata frase per frase *mentre l'LLM sta ancora generando*; anche la chat web è in streaming (SSE)
- 🗣️ **IA vocale a mani libere** — wake word offline ("TARS"), riconoscimento Whisper o Vosk, sintesi ElevenLabs/OpenAI/espeak con fallback automatico
- 🧠 **Personalità regolabile** — umorismo, onestà e sarcasmo da 0 a 100%, modificabili dalla dashboard o semplicemente *chiedendolo al robot*
- 💾 **Memoria semantica a lungo termine** — note recuperate per similarità di embedding (fallback offline a parole chiave), più skill esplicite `remember`/`recall`
- 👁️ **Visione** — la skill `look` cattura un frame dalla camera e descrive la scena con GPT multimodale
- ⏰ **Timer e parola proattiva** — scheduler heartbeat: promemoria e avvisi di batteria scarica pronunciati di sua iniziativa
- 🦿 **Andature** — passo, svolte, spostamento laterale, posa "monolite"; comandi vocali ("TARS, spostati a destra") via tool-calling LLM
- 🌐 **Dashboard web** — chat in streaming, pulsantiera movimenti, slider personalità, controllo voce, batteria/CPU su `http://<pi>:8000`
- 🎮 **Guida col gamepad** — supporto 8BitDo Zero 2
- 🌍 **Multilingua** — italiano, inglese, spagnolo, francese, tedesco, portoghese, giapponese
- 💻 **Modalità simulazione** — sviluppa tutto su un portatile, senza hardware (`--sim`)

## 🚀 Avvio rapido

```bash
git clone https://github.com/metaforismo/TarsGPT
cd TarsGPT
./install.sh
cp .env.example .env        # inserisci la tua OPENAI_API_KEY
source .venv/bin/activate
python -m tars.app --sim    # provalo subito, robot opzionale
```

## 📚 Documentazione

- [Architettura software e manuale](docs/it/SOFTWARE.md)
- [Guida completa alla costruzione](docs/it/GUIDA_COSTRUZIONE.md)
- [Lista acquisti, stampanti Bambu Lab, effetto metallo](docs/it/LISTA_ACQUISTI.md)
- [Stima dei costi, voce per voce](docs/it/STIMA_COSTI.md)

## 🔩 Hardware in sintesi

Raspberry Pi 5 (8 GB) · driver servo PCA9685 · 4–6 servo MG996R + 4 MG90S · touchscreen DSI 5" · camera · batteria 12 V con doppio buck converter · ~1,5 kg di PETG. Dettagli completi e totali (da **≈ 280 €** se hai già la stampante) nella [stima dei costi](docs/it/STIMA_COSTI.md).

## Crediti e licenza

- **L'idea**: la [replica TARS originale di Charlie Diaz](https://www.hackster.io/charlesdiaz/how-to-build-your-own-replica-of-tars-from-interstellar-224833) — questo progetto è partito dal suo concept ed è cresciuto nel runtime IA completo, nell'apprendimento dell'andatura, nel design balance-first e nella documentazione che vedi qui.
- **Il telaio stampabile**: riferito dalla [TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI) (CC BY-NC 4.0 — attribuzione necessaria per le parti stampate). Gli STL completi si scaricano dal loro repo; questa repo include un file STEP di riferimento (`525125.STEP`).
- **Il codice di questa repository**: implementazione originale, MIT (vedi [LICENSE](LICENSE)).
- TARS è un personaggio di *Interstellar* di Christopher Nolan; questo è un fan project non commerciale.
