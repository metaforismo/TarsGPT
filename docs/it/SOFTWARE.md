# Software TARS — Architettura e Manuale

> Il pacchetto `tars/` di questa repo è un'**implementazione originale e autonoma** di un runtime robot IA completo: wake word, riconoscimento vocale, personalità LLM in streaming con sistema di skill a plugin, sintesi vocale frase-per-frase, memoria semantica a lungo termine, visione multimodale, andature servo, guida col gamepad, scheduler "heartbeat" e dashboard web. 🇬🇧 [English version](../en/SOFTWARE.md)

## Panoramica funzionalità

| Funzionalità | Come funziona | Modulo |
|---|---|---|
| **Sistema di skill a plugin** | Metti un file Python in `tars/skills/`, decora una funzione con `@skill` — si registra da sola come tool LLM all'avvio. 14 skill integrate | `tars/skills/` |
| **Knowledge graph** | Fatti strutturati soggetto-relazione-oggetto (`learn_fact`/`query_facts`/`forget_facts`), deduplicati, persistenti, iniettati automaticamente nel contesto quando rilevanti, visibili nella dashboard | `tars/knowledge.py` |
| **Identificazione speaker** *(sperimentale)* | Impronte vocali a bande di energia + pitch; registrati con "impara la mia voce, sono Francesco" e TARS saprà chi parla: l'LLM vede `[Francesco is speaking]` | `tars/speakerid.py`, `tars/skills/speakers.py` |
| **Voce dal browser** | Parla con TARS da qualsiasi telefono/PC in rete: la dashboard registra il microfono, il robot trascrive, risponde e rimanda l'audio al browser | `/api/voice/chat` + `/api/tts` |
| **Home Assistant** | Skill `home_assistant`: accendi/spegni/interroga qualsiasi entità via API REST di HA (`HA_URL`/`HA_TOKEN`) | `tars/skills/home_assistant.py` |
| **Musica** | `play_music`/`stop_music`: stazioni radio integrate (lofi, jazz, classica, synthwave), URL di stream o file locali via mpv | `tars/skills/music.py` |
| **Pipeline vocale in streaming** | I token dell'LLM arrivano in streaming, vengono tagliati ai confini di frase e pronunciati subito — TARS inizia a rispondere mentre sta ancora "pensando" il resto | `tars/llm.py` + `tars/speech.py` |
| **Wake word** ("TARS") | Offline, modello Vosk small con grammatica ristretta | `tars/voice.py` |
| **Speech-to-text** | API OpenAI Whisper oppure Vosk completamente offline | `tars/stt.py` |
| **Personalità IA** | Umorismo/onestà/sarcasmo 0–100%, regolabili live dalla dashboard o *chiedendolo a TARS* (skill `set_personality`) | `tars/personality.py`, `tars/skills/persona.py` |
| **Memoria semantica a lungo termine** | Le note vengono trasformate in embedding (OpenAI `text-embedding-3-small`) e recuperate per similarità coseno rispetto a ciò che hai appena detto; offline ricade sul matching per parole chiave. Skill esplicite `remember`/`recall` | `tars/memory.py`, `tars/skills/memory_notes.py` |
| **Visione** | Skill `look`: frame dalla camera (rpicam/libcamera/fswebcam/OpenCV) → descrizione con GPT multimodale, può anche rispondere a domande sulla scena | `tars/skills/vision.py` |
| **Movimenti a comando vocale** | L'LLM chiama la skill `move` (passo/svolta/posa) quando gli chiedi di muoversi | `tars/skills/movement.py` → `tars/movement/gaits.py` |
| **Timer e parola proattiva** | "TARS, ricordamelo tra 10 minuti…" → lo scheduler scatta → TARS *parla di sua iniziativa* | `tars/skills/timers.py`, `tars/scheduler.py` |
| **Auto-monitoraggio** | Skill `system_status` (batteria via INA260, temperatura CPU, uptime, disco) + watchdog batteria che annuncia la carica bassa | `tars/skills/system.py` |
| **Text-to-speech** | Catena di fallback: ElevenLabs (la più vicina alla voce del film) → OpenAI TTS → espeak-ng | `tars/tts.py` |
| **Multilingua** | `TARS_LANGUAGE=it` (o en/es/fr/de/pt/ja): risposte, STT e TTS si adeguano | `tars/config.py` |
| **Dashboard web** | Chat in streaming (SSE), pulsantiera movimenti, slider personalità, controllo voce, batteria/CPU, ispezione memoria | `tars/web/` |
| **Guida col gamepad** | 8BitDo Zero 2 via evdev: d-pad = cammina/gira/posa, tasti = braccia | `tars/movement/gamepad.py` |
| **Modalità simulazione** | Niente hardware? Tutto gira con i movimenti servo loggati (`--sim`) | `tars/movement/driver.py` |

## Architettura

```
   microfono ──▶ VoiceLoop ──▶ STT ─┐                        ┌─▶ Speaker ──▶ TTS ──▶ 🔊
                (wake word)         │   ┌───────────────┐    │   (streaming a frasi)
   chat web ──▶ SSE /api/chat/stream┼──▶│ Brain (LLM)   │────┤
                                    │   │ + persona     │    └─▶ testo in streaming alla UI
   le skill parlano proattivamente ─┘   │ + memoria     │
   (timer, watchdog batteria)           └──────┬────────┘
                                               │ tool call
                                 ┌─────────────▼─────────────┐
                                 │ Registro skill (14 plugin)│
                                 │ move · remember · recall  │
                                 │ set_timer · look · persona│
                                 │ system_status · learn_fact│
                                 │ query/forget_facts · music│
                                 │ home_assistant · enroll   │
                                 └──────┬──────────┬─────────┘
                                        ▼          ▼
   gamepad (evdev) ───────────▶ Gaits ▶ PCA9685   Scheduler (heartbeat)
```

Ogni livello degrada con grazia: niente PCA9685 → simulazione; niente Vosk → push-to-talk dalla UI web; niente ElevenLabs → OpenAI TTS → espeak-ng; nessuna chiave API → Vosk + espeak-ng + memoria a parole chiave, tutto offline.

## Installazione e avvio

```bash
git clone https://github.com/metaforismo/TarsGPT
cd TarsGPT
./install.sh                 # dipendenze apt + venv + pip; riconosce il Raspberry Pi
cp .env.example .env         # inserisci la tua OPENAI_API_KEY
source .venv/bin/activate
python -m tars.app           # robot completo  (--sim su un portatile, --no-voice, --no-web)
python servo_tester.py       # prima calibra i servo!
```

Dashboard: `http://<indirizzo-pi>:8000`

### Checklist primo avvio

1. `sudo raspi-config` → abilita **I2C** (e la camera se montata).
2. `python servo_tester.py` → trova min/neutro/max PWM di ogni canale; **mai forzare un servo oltre il fine corsa meccanico**.
3. Inserisci i valori calibrati in `data/settings.json` sotto `"pwm"`.
4. Parti con `--no-voice` e verifica i movimenti dalla dashboard.
5. Aggiungi le chiavi API, attiva la voce, dì "TARS".

## Scrivere una skill (il bello del sistema)

Crea `tars/skills/meteo.py`:

```python
from . import skill

@skill("weather", "Get the current weather for a city",
       {"type": "object", "properties": {"city": {"type": "string"}},
        "required": ["city"]})
def weather(ctx, city):
    # ctx ti dà: settings, memory, gaits, scheduler, speaker (ctx.say(...))
    return f"Sereno a {city}, 22 gradi."   # l'LLM la integra nella risposta
```

Riavvia. Fine — niente file di registrazione, niente catene di dispatch da modificare. Ora l'LLM controlla il meteo quando glielo chiedi.

## API HTTP

| Endpoint | Metodo | Body | Scopo |
|---|---|---|---|
| `/api/chat` | POST | `{"message": "..."}` | Risposta singola |
| `/api/chat/stream` | POST | `{"message": "..."}` | **Stream SSE** dei delta della risposta |
| `/api/move` | POST | `{"action": "step_forward\|turn_left\|turn_right\|pose\|neutral"}` | Comanda il corpo |
| `/api/settings` | GET/POST | `{"humor": 75, ...}` | Leggi/modifica la personalità |
| `/api/status` | GET | — | Stato voce, sim, batteria %, temperatura CPU |
| `/api/memory` | GET | — | Turni recenti + note a lungo termine |
| `/api/knowledge` | GET | — | Triple del knowledge graph |
| `/api/voice/chat` | POST | file `audio` multipart | **Voce dal browser**: audio in ingresso → `{heard, reply}` |
| `/api/tts` | POST | `{"text": "..."}` | File audio sintetizzato (riproduzione nel browser) |
| `/api/voice/start\|stop\|ptt` | POST | — | Controllo loop vocale / push-to-talk |

## Riferimento configurazione

Tutto via `.env` (vedi `.env.example`): `OPENAI_API_KEY`, `TARS_MODEL`, `TARS_EMBEDDING_MODEL`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `TARS_LANGUAGE`, `TARS_WAKE_WORD`, `TARS_TTS`, `TARS_STT`, `TARS_SIM`, `TARS_GAMEPAD`, `TARS_WEB_PORT`. Personalità e calibrazione PWM persistono in `data/settings.json`; la memoria a lungo termine (con embedding) in `data/memory.json`.

## Note di design — confronto col progetto community di riferimento

L'implementazione community più completa organizza il codice in `character/memory/modules/skills/stt/tts/www` e ha introdotto idee che abbiamo abbracciato: skill a plugin, TTS in streaming a frasi, scheduler heartbeat, monitoraggio INA260. Questo runtime ne conserva le idee ma ne ripensa l'esecuzione:

- **Un solo processo, ~15 moduli piccoli** invece di una grande codebase multi-app — più facile da leggere per intero e da modificare.
- **Una skill è una singola funzione decorata** con auto-discovery; niente file di configurazione né catene di dispatch.
- **La visione usa l'LLM multimodale** (un'unica API, può rispondere a domande sulla scena) invece di un modello locale BLIP separato per il captioning.
- **Il recupero della memoria è semantico** (embedding + coseno) con fallback offline a zero dipendenze, e l'LLM può anche interrogarla esplicitamente con `recall`.
- **Tutto degrada con grazia** fino a uno stack completamente offline e a costo zero (Vosk + espeak-ng + memoria a parole chiave).
- Stesso hardware Pi 5, stesso cablaggio PCA9685 e stesso modello di calibrazione PWM: gira invariato su una build stile V3.

Tutte le funzionalità di punta del progetto community hanno ora una controparte originale qui: skill, TTS in streaming, scheduler, monitoraggio batteria, knowledge graph, identificazione speaker, Home Assistant, musica e voce dal browser — verificate dalla suite di test in `tests/run_tests.py` (`python tests/run_tests.py`, senza hardware né chiavi API).
