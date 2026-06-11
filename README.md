# TarsGPT — A Complete AI Robot Inspired by TARS

🇬🇧 English | 🇮🇹 [Italiano più sotto](#tarsgpt--un-robot-ia-completo-ispirato-a-tars)

![TARS](https://github.com/user-attachments/assets/cb7f6acf-b7c4-41ff-ab1a-2640e8610c68)

TarsGPT is a **complete, self-contained robot project**: an original Python runtime (voice AI, personality, movement, web dashboard) plus full bilingual documentation to design, print, wire, assemble and finish a walking TARS-style robot.

## ✨ Features

- 🗣️ **Hands-free voice AI** — offline wake word ("TARS"), Whisper or Vosk speech recognition, ElevenLabs/OpenAI/espeak text-to-speech with automatic fallback
- 🧠 **Adjustable personality** — humor, honesty and sarcasm from 0 to 100%, changeable from the dashboard or by simply *asking the robot*
- 🦿 **Walking gaits** — step, turns, "monolith" pose; voice-commanded ("TARS, walk forward") via LLM tool-calling
- 💾 **Long-term memory** — the robot decides what to remember and keeps it across restarts
- 🌐 **Web dashboard** — chat, movement pad, personality sliders, voice control at `http://<pi>:8000`
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
  llm.py             # LLM brain, persona, move/remember/personality tools
  voice.py stt.py tts.py audio.py
  movement/          # PCA9685 driver, gaits, gamepad
  web/               # Flask dashboard
servo_tester.py      # interactive servo calibration
legacy/              # the original gamepad-only scripts (kept for reference)
docs/                # bilingual documentation (en/, it/)
```

## Credits & license

Code in this repository: MIT (see [LICENSE](LICENSE)). The 3D-printable chassis files referenced in the build guide are by the TARS-AI Community (CC BY-NC 4.0) — required attribution for the printed parts only. TARS is a character from *Interstellar*; this is a non-commercial fan project.

---

# TarsGPT — Un Robot IA Completo Ispirato a TARS

TarsGPT è un **progetto robot completo e autonomo**: un runtime Python originale (IA vocale, personalità, movimento, dashboard web) più documentazione bilingue completa per progettare, stampare, cablare, assemblare e rifinire un robot stile TARS che cammina.

## ✨ Funzionalità

- 🗣️ **IA vocale a mani libere** — wake word offline ("TARS"), riconoscimento Whisper o Vosk, sintesi ElevenLabs/OpenAI/espeak con fallback automatico
- 🧠 **Personalità regolabile** — umorismo, onestà e sarcasmo da 0 a 100%, modificabili dalla dashboard o semplicemente *chiedendolo al robot*
- 🦿 **Andature** — passo, svolte, posa "monolite"; comandi vocali ("TARS, cammina") via tool-calling LLM
- 💾 **Memoria a lungo termine** — il robot decide cosa ricordare e lo conserva tra i riavvii
- 🌐 **Dashboard web** — chat, pulsantiera movimenti, slider personalità, controllo voce su `http://<pi>:8000`
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

Il codice di questa repository è MIT (vedi [LICENSE](LICENSE)). I file 3D del telaio citati nella guida sono della TARS-AI Community (CC BY-NC 4.0) — attribuzione necessaria solo per le parti stampate. TARS è un personaggio di *Interstellar*; questo è un fan project non commerciale.
