# Software TARS — Architettura e Manuale

> Il pacchetto `tars/` di questa repo è un'**implementazione originale e autonoma** di un runtime robot IA completo: wake word, riconoscimento vocale, personalità LLM in streaming con sistema di skill a plugin, sintesi vocale frase-per-frase, memoria semantica a lungo termine, visione multimodale, andature servo, guida col gamepad, scheduler "heartbeat" e dashboard web. 🇬🇧 [English version](../en/SOFTWARE.md)

## Panoramica funzionalità

| Funzionalità | Come funziona | Modulo |
|---|---|---|
| **Sistema di skill a plugin** | Metti un file Python in `tars/skills/`, decora una funzione con `@skill` — si registra da sola come tool LLM all'avvio. 18 skill integrate | `tars/skills/` |
| **LLM locale o cloud** | Cloud OpenAI, oppure qualsiasi server OpenAI-compatibile — Ollama, LM Studio, llama.cpp, vLLM — via `TARS_LLM_BASE_URL`. Un TARS completamente offline è possibile | `tars/llm.py` |
| **Character card** | Personaggi intercambiabili in `characters/*.json` (inclusi TARS, CASE, KIPP): nome, persona, valori di default. "Diventa CASE" funziona a voce, da dashboard o API | `tars/characters.py` |
| **Sequenze coreografate** | Routine di movimento con nome (greet, wiggle, patrol + le tue in `data/sequences.json`); "TARS, balla" → skill `perform` | `tars/movement/sequences.py` |
| **Apprendimento dell'andatura** | Ottimizzazione dei parametri di camminata con reward verificabile: col metro, o a mani libere con la camera; curva di apprendimento live nella dashboard. `python -m tars.learn` | `tars/learn/` |
| **Rilevamento cadute (IMU)** | MPU-6050 opzionale (~3 €, stesso bus I2C): orientamento in `system_status`, e durante il training una caduta diventa automaticamente una penalità | `tars/sensors.py` |
| **Conversazione continua** | Dopo la risposta TARS resta in ascolto ~6 s: puoi replicare senza ripetere la wake word (`TARS_FOLLOWUP_WINDOW`) | `tars/voice.py` |
| **Schermo di bordo** | `/display`: readout in stile film (nome, barre umorismo/onestà, batteria, temperatura, orologio) per il display DSI del robot in modalità kiosk | `tars/web/static/display.html` |
| **Piper TTS** | Sintesi vocale neurale locale e gratuita: installa `piper`, scarica una voce, imposta `TARS_PIPER_VOICE` — nella catena di fallback prima di espeak | `tars/tts.py` |
| **Controllo volume** | Skill `set_volume` via amixer/pactl | `tars/skills/system.py` |
| **Generazione immagini** | Skill `generate_image` (DALL·E 3): salvate in `data/images/`, anteprima inline nella chat della dashboard | `tars/skills/images.py` |
| **Login dashboard** | Password condivisa opzionale (`TARS_WEB_PASSWORD`) che protegge tutte le API con cookie di sessione | `tars/web/server.py` |
| **Temi UI** | 4 temi (spazio profondo, CRT ambra, verde terminale, diurno), persistiti per browser | `tars/web/static/` |
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

## Scegliere il tuo stack IA

| Stack | Cervello | Voce | STT | Qualità | Costo ricorrente | Richiede |
|---|---|---|---|---|---|---|
| **Cloud** (default) | OpenAI `gpt-4o-mini` | ElevenLabs | Whisper API | Migliore, voce da film | ~2–10 €/mese | Chiavi API |
| **Ibrido** ⭐ | OpenAI `gpt-4o-mini` | **Piper** (locale) | Whisper API | Ottima, voce gratis | ~1–5 €/mese | Chiave OpenAI |
| **Tutto locale** | Ollama via `TARS_LLM_BASE_URL` | Piper | Vosk | Buona, privata, offline | **0 €** | Un PC in rete (o un Pi paziente) |

### Voce Piper in due minuti

```bash
pip install piper-tts                       # fornisce il comando `piper`
# scarica una voce da https://github.com/rhasspy/piper/blob/master/VOICES.md
# es. it_IT-riccardo-x_low (italiano) o en_US-ryan-low (inglese)
mkdir -p ~/voices && cd ~/voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/riccardo/x_low/it_IT-riccardo-x_low.onnx{,.json}
echo "TARS_PIPER_VOICE=$HOME/voices/it_IT-riccardo-x_low.onnx" >> .env
```

Piper si inserisce da solo nella catena di fallback (prima di espeak): i motori cloud vengono usati quando configurati, Piper copre tutto il resto.

### Tutto locale con Ollama

```bash
# su qualsiasi PC della tua rete (o sul Pi stesso con un modello piccolo)
ollama serve && ollama pull llama3.1:8b
# nel .env di TARS:
TARS_LLM_BASE_URL=http://<indirizzo-pc>:11434/v1
TARS_MODEL=llama3.1:8b
TARS_STT=vosk
```

Se il server locale non supporta il tool calling, TARS lo rileva a runtime e degrada a conversazione semplice invece di fallire (le skill vengono temporaneamente disabilitate).

## Insegnare a TARS a camminare meglio (reward verificabile)

L'andatura dipende da cinque parametri di timing (velocità di sollevamento del
torso, rotazione delle gambe, il "bump" del pivot, il recupero, il ritorno).
I valori di fabbrica sono un compromesso; la tua build — peso, servo,
pavimento — ha il suo ottimo. `tars/learn` lo trova con una **(1+1) evolution
strategy** la cui reward è *fisicamente verificabile*: i centimetri davvero
percorsi.

```bash
python -m tars.learn --reward measured --iterations 12 --steps 3
```

Per ogni andatura candidata il robot fa 3 passi; leggi la distanza sul metro
(o sulle piastrelle) e la digiti — negativa se è caduto. L'ottimizzatore muta
i parametri in scala logaritmica con passo adattivo (regola del quinto:
esplora più ampio finché migliora, si restringe quando ristagna) e salva
l'andatura migliore in `data/gait_params.json`, caricata automaticamente a
ogni avvio. Servono ~10 minuti e ~2 m di pavimento libero; puoi interrompere
e riprendere — l'allenamento riparte sempre dal miglior risultato corrente.

**Variante a mani libere** — lascia giudicare la camera:

```bash
python -m tars.learn --reward camera --iterations 12 --steps 3
```

Un frame viene catturato prima e dopo i passi di ogni candidata; la
correlazione di fase tra i due recupera la traslazione della camera in pixel —
proporzionale al terreno percorso quando la camera guarda una scena statica
con texture (puntarla verso il pavimento funziona meglio). I pixel sono
un'unità relativa, che è tutto ciò che serve all'ottimizzatore. Con
`--camera-axis x|-x|y|-y` la reward diventa la componente con segno lungo un
asse dell'immagine: camminare *all'indietro* dà punteggio negativo (trova
l'asse "avanti" della tua build spingendo TARS una volta e guardando il segno).

**Completamente non supervisionato** — aggiungi l'IMU MPU-6050 (~3 €, in
parallelo sullo stesso bus I2C, indirizzo 0x68): se presente viene rilevato
automaticamente e ogni candidata che lascia TARS non in piedi riceve una
penalità fissa al posto del punteggio camera — cadere non conviene mai
(`--no-imu` per disattivare). Una singola cattura o misura fallita salta
quella candidata invece di uccidere la sessione, e ogni valutazione viene
registrata in `data/gait_training.json`: la dashboard disegna la **curva di
apprendimento live** (grigio = reward per candidata, accento = miglior
risultato). Senza IMU supervisiona le prime sessioni; il metro
(`--reward measured`) resta la verità di riferimento.

`--reward sim` esegue la stessa macchina su una superficie surrogata
deterministica (usata dalla suite di test per verificare che l'ottimizzatore
converga davvero) — utile per provare l'intero loop a vuoto con `--sim`.
**Ctrl-C è sicuro in ogni modalità**: l'allenamento si ferma conservando la
miglior andatura trovata fin lì.

## Lo schermo di bordo

Punta il browser del robot sul readout per l'effetto film completo:

```bash
chromium-browser --kiosk --noerrdialogs http://localhost:8000/display
```

Sfondo nero, monospace ciano, barre umorismo/onestà, batteria e temperatura,
scanline CRT, cursore lampeggiante. Il nome pulsa mentre TARS ascolta.
Localhost è esente dalla password della dashboard, quindi il kiosk funziona
anche con `TARS_WEB_PASSWORD` impostata.

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
| `/api/characters` | GET/POST | `{"name": "case"}` | Elenca / cambia character card |
| `/api/login` | POST | `{"password": "..."}` | Login di sessione se `TARS_WEB_PASSWORD` è impostata |
| `/images/<file>` | GET | — | Immagini generate |

## Riferimento configurazione

Tutto via `.env` (vedi `.env.example`): `OPENAI_API_KEY`, `TARS_LLM_BASE_URL`, `TARS_MODEL`, `TARS_EMBEDDING_MODEL`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `TARS_PIPER_VOICE`, `TARS_LANGUAGE`, `TARS_WAKE_WORD`, `TARS_TTS`, `TARS_STT`, `TARS_SIM`, `TARS_GAMEPAD`, `TARS_WEB_PORT`, `TARS_WEB_PASSWORD`, `HA_URL`, `HA_TOKEN`, `TARS_MUSIC_DIR`. Personalità e calibrazione PWM persistono in `data/settings.json`; la memoria a lungo termine (con embedding) in `data/memory.json`.

## Avvio automatico al boot

```bash
sudo cp deploy/tars.service /etc/systemd/system/   # adegua i percorsi all'interno se serve
sudo systemctl daemon-reload
sudo systemctl enable --now tars
journalctl -u tars -f                               # log in diretta
```

## Risoluzione problemi

| Sintomo | Soluzione |
|---|---|
| I servo tremano o scattano | 9 volte su 10 è alimentazione: buck converter non a **6,2 V**, batteria sottodimensionata, o manca la **massa comune** tra rail V+ del PCA9685 e Pi |
| `No PCA9685 found` sul robot | Abilita I2C (`sudo raspi-config`), poi `i2cdetect -y 1` deve mostrare `0x40`; controlla i cavi SDA/SCL |
| Il microfono non viene rilevato | `arecord -l` per elencare i dispositivi; imposta la scheda USB come default in `~/.asoundrc` |
| Nessun suono | `aplay -l`, prova `speaker-test -t wav`; assicurati che il sink di default sia la scheda USB, non l'HDMI |
| La wake word non scatta mai | Vosk scarica il modello al primo uso — serve internet una volta; oppure `TARS_STT=openai` e usa il push-to-talk |
| Il pulsante microfono del browser non fa nulla | I browser permettono il microfono solo su HTTPS o localhost. Soluzione facile: `ssh -L 8000:localhost:8000 pi@tars.local`, poi apri `http://localhost:8000` |
| Gamepad non rilevato | Ora è autorilevato; se fallisce ancora, trovalo con `python -c "import evdev; print(evdev.list_devices())"` e imposta `TARS_GAMEPAD` |
| Risposte lente | Usa `gpt-4o-mini` (default), tieni ElevenLabs (streama frase per frase), o vai in locale con Ollama su un PC e `TARS_LLM_BASE_URL` |

## Note di design — confronto col progetto community di riferimento

L'implementazione community più completa organizza il codice in `character/memory/modules/skills/stt/tts/www` e ha introdotto idee che abbiamo abbracciato: skill a plugin, TTS in streaming a frasi, scheduler heartbeat, monitoraggio INA260. Questo runtime ne conserva le idee ma ne ripensa l'esecuzione:

- **Un solo processo, ~15 moduli piccoli** invece di una grande codebase multi-app — più facile da leggere per intero e da modificare.
- **Una skill è una singola funzione decorata** con auto-discovery; niente file di configurazione né catene di dispatch.
- **La visione usa l'LLM multimodale** (un'unica API, può rispondere a domande sulla scena) invece di un modello locale BLIP separato per il captioning.
- **Il recupero della memoria è semantico** (embedding + coseno) con fallback offline a zero dipendenze, e l'LLM può anche interrogarla esplicitamente con `recall`.
- **Tutto degrada con grazia** fino a uno stack completamente offline e a costo zero (Vosk + espeak-ng + memoria a parole chiave).
- Stesso hardware Pi 5, stesso cablaggio PCA9685 e stesso modello di calibrazione PWM: gira invariato su una build stile V3.

Tutte le funzionalità di punta del progetto community hanno ora una controparte originale qui: skill, TTS in streaming, scheduler, monitoraggio batteria, knowledge graph, identificazione speaker, Home Assistant, musica e voce dal browser — verificate dalla suite di test in `tests/run_tests.py` (`python tests/run_tests.py`, senza hardware né chiavi API).
