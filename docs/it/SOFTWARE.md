# Software TARS — Architettura e Manuale

> Il pacchetto `tars/` di questa repo è un'**implementazione originale e autonoma** di un runtime robot IA completo: wake word, riconoscimento vocale, personalità LLM con tool-calling, sintesi vocale, andature servo, guida col gamepad e dashboard web. 🇬🇧 [English version](../en/SOFTWARE.md)

## Panoramica funzionalità

| Funzionalità | Come funziona | Modulo |
|---|---|---|
| **Wake word** ("TARS") | Offline, modello Vosk small con grammatica ristretta | `tars/voice.py` |
| **Speech-to-text** | API OpenAI Whisper oppure Vosk completamente offline | `tars/stt.py` |
| **Personalità IA** | Chat OpenAI con la persona di TARS; umorismo/onestà/sarcasmo 0–100%, regolabili in tempo reale (anche *chiedendolo a TARS*: ha un tool `set_personality`) | `tars/llm.py`, `tars/personality.py` |
| **Movimenti a comando vocale** | L'LLM chiama un tool `move` (passo/svolta/posa) quando gli chiedi di muoversi | `tars/llm.py` → `tars/movement/gaits.py` |
| **Memoria a lungo termine** | L'LLM salva fatti con un tool `remember`; persistiti in `data/memory.json` e iniettati in ogni conversazione | `tars/memory.py` |
| **Text-to-speech** | Catena di fallback: ElevenLabs (la più vicina alla voce del film) → OpenAI TTS → espeak-ng | `tars/tts.py` |
| **Multilingua** | Imposta `TARS_LANGUAGE=it` (o en/es/fr/de/pt/ja): risposte, STT e TTS si adeguano | `tars/config.py` |
| **Dashboard web** | Chat, pulsantiera movimenti, controllo voce, slider personalità, stato live | `tars/web/` |
| **Guida col gamepad** | 8BitDo Zero 2 via evdev: d-pad = cammina/gira/posa, tasti = braccia | `tars/movement/gamepad.py` |
| **Andature** | Sollevamento → rotazione gambe → "bump" del torso → ritorno in parallelo; svolte e posa "monolite" | `tars/movement/gaits.py` |
| **Modalità simulazione** | Niente hardware? Tutto gira con i movimenti servo loggati (`--sim`) | `tars/movement/driver.py` |
| **Calibrazione servo** | Tester PWM interattivo con limiti di sicurezza | `servo_tester.py` |

## Architettura

```
                ┌─────────────────────────────────────────┐
   microfono ──▶│ VoiceLoop: wake word ▶ registra ▶ STT   │
                └──────────────┬──────────────────────────┘
                               ▼
  chat web ───▶ ┌─────────────────────────────────────────┐      ┌──────────────────┐
  (UI Flask)    │ Brain (LLM + persona + memoria)         │─────▶│ TTS ▶ altoparlante│
                │   tool: move / remember / personality   │      └──────────────────┘
                └──────────────┬──────────────────────────┘
                               ▼
  gamepad ────▶ ┌─────────────────────────────────────────┐
  (evdev)       │ Gaits ▶ ServoDriver ▶ PCA9685 ▶ servo   │
                └─────────────────────────────────────────┘
```

Ogni livello degrada con grazia: niente PCA9685 → simulazione; niente Vosk → push-to-talk dalla UI web; niente ElevenLabs → OpenAI TTS; nessuna chiave API → Vosk + espeak-ng offline.

## Installazione

```bash
git clone https://github.com/metaforismo/TarsGPT
cd TarsGPT
./install.sh                 # dipendenze apt + venv + pip; riconosce il Raspberry Pi
cp .env.example .env         # poi inserisci la tua OPENAI_API_KEY
```

## Avvio

```bash
source .venv/bin/activate
python -m tars.app                  # robot completo
python -m tars.app --sim            # su un portatile, senza hardware
python -m tars.app --no-voice       # solo testo/web
python servo_tester.py              # prima calibra i servo!
```

Dashboard: `http://<indirizzo-pi>:8000`

### Checklist primo avvio

1. `sudo raspi-config` → abilita **I2C** (e la camera se montata).
2. `python servo_tester.py` → trova min/neutro/max PWM di ogni canale; **mai forzare un servo oltre il fine corsa meccanico**.
3. Inserisci i valori calibrati in `data/settings.json` sotto `"pwm"`.
4. Parti con `--no-voice` e verifica i movimenti dalla dashboard.
5. Aggiungi le chiavi API, attiva la voce, dì "TARS".

## API HTTP

| Endpoint | Metodo | Body | Scopo |
|---|---|---|---|
| `/api/chat` | POST | `{"message": "..."}` | Parla con TARS, restituisce `{"reply": ...}` |
| `/api/move` | POST | `{"action": "step_forward\|turn_left\|turn_right\|pose\|neutral"}` | Comanda il corpo |
| `/api/settings` | GET/POST | `{"humor": 75, ...}` | Leggi/modifica la personalità |
| `/api/status` | GET | — | Stato voce, modalità sim |
| `/api/voice/start\|stop\|ptt` | POST | — | Controllo loop vocale / push-to-talk |

## Riferimento configurazione

Tutto via `.env` (vedi `.env.example`): `OPENAI_API_KEY`, `TARS_MODEL`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `TARS_LANGUAGE`, `TARS_WAKE_WORD`, `TARS_TTS`, `TARS_STT`, `TARS_SIM`, `TARS_GAMEPAD`, `TARS_WEB_PORT`. Personalità e calibrazione PWM persistono in `data/settings.json`; la memoria a lungo termine in `data/memory.json`.

## Estendere TARS

- **Nuovi tool LLM** (≈ skill): aggiungi uno schema a `TOOLS` e un ramo in `Brain._run_tool` (`tars/llm.py`). Idee: meteo, timer, Home Assistant, scatto dalla camera.
- **Nuove andature**: componi le primitive di `Gaits` (sweep dei servo di sollevamento/trazione).
- **La voce del film**: crea una voce custom su ElevenLabs (profonda, asciutta, leggermente metallica) e imposta `ELEVENLABS_VOICE_ID`.
- **Visione**: la camera OV5647 + face detection con `opencv-python` si integra naturalmente come tool `look`.
