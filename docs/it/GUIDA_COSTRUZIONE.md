# Guida Completa alla Costruzione di TARS

> Da una bobina di filamento a un TARS che parla e cammina. Basata sul design **V3** della [TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI) — la build di riferimento attuale — con note sulle alternative.
>
> 🇬🇧 English version: [BUILD_GUIDE.md](../en/BUILD_GUIDE.md)
>
> 🛒 Prima compra tutto: [Lista Acquisti](LISTA_ACQUISTI.md)

## 1. Conosci l'ecosistema (scegli la tua strada)

| Progetto | Ideale per | Stack | Licenza |
|---|---|---|---|
| **[TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI)** ⭐ | L'esperienza completa | Pi 5, IA completa (LLM, TTS, STT, wake word, UI web, plugin "skills") | CC BY-NC 4.0 |
| **[latishab/tars](https://github.com/latishab/tars)** | Sviluppatori | Daemon hardware sul Pi + API gRPC/WebRTC; le app IA girano ovunque (`pip install tars-robot[daemon]`); dashboard su `http://tars.local:8000` | vedi LEGAL.md |
| **[TARS-WIZARD](https://github.com/DhruvGoswami10/TARS-WIZARD)** | Budget / multilingua | Pi 5, 3 servo, personalità GPT-3.5, voce in EN/ES/FR/DE/**IT**/PT/JA | MIT |
| **Questa repo (script legacy)** | Guida manuale col gamepad | `TARSRunner.py` + PCA9685, 8BitDo Zero 2 | MIT |

**Perché costruire l'hardware V3:** un servo extra nel torso per il movimento indipendente delle gambe, **nessuna saldatura richiesta**, elettronica modulare, porte USB/HDMI accessibili, cablaggio più ordinato e costo totale inferiore rispetto a V1/V2.

### Storico release di TARS-AI (cosa sa fare il software)

- **v1.0** — prima release: IA completamente locale con la personalità di TARS, livelli di umorismo/onestà configurabili, framework modulare.
- **v2.0** — STT Whisper, function calling (Naive Bayes + LLM), movimenti comandati a voce, generazione immagini DALL·E/Stable Diffusion, integrazione Home Assistant.
- **v3.0** — TTS ElevenLabs, Whisper locale + Vosk, Silero VAD, chat web, memoria/RAG migliorati, streaming TTS frase per frase.
- **v4.0** — redesign meccanico TARS V2, RAG ibrido, TTS Azure/OpenAI, monitoraggio batteria INA260, tab di controllo movimento nella UI web.
- **OS Amelia** (2026, attuale) — architettura a plugin "skills", LLM in streaming con TTS a frasi, identificazione dello speaker, dashboard con grafo di memoria/conoscenza, wake word CNN/ONNX ("Atomik"), supporto Pi Zero 2, skill Discord/musica/radio/camera, modalità voce nel browser, 15 temi UI.

Changelog completi: [release GitHub](https://github.com/TARS-AI-Community/TARS-AI/releases) · [sito docs](https://docs-tars-ai.vercel.app/releases).

## 2. Stampa 3D dei pezzi

1. Scarica gli **STL V3** dalla [repo TARS-AI](https://github.com/TARS-AI-Community/TARS-AI) (cartella `3D Printer Files`, branch V3). Esiste anche una versione statica (non motorizzata) se vuoi solo un pezzo da esposizione.
2. **Stampa prima il pezzo di calibrazione.** Il design assume tolleranze di ±0,02 mm; se la calibrazione non combacia, regola flusso/scala prima di stampare oltre 1 kg di pezzi.
3. Impostazioni slicer (ufficiali): layer **0,2 mm**, **almeno 3 perimetri**, riempimento **20% gyroid**, **5** layer sopra/sotto, **niente brim**, **supporti ad albero automatici** con **angolo soglia 10°** così i supporti non crescono dentro i fori delle viti.
4. **Non ruotare i pezzi** — sono già orientati perché le linee di stampa risultino belle sulle facce a vista.
5. Materiali: **PETG** per tutto ciò che è strutturale; TPU per le suole; PLA metallizzato o verniciatura per i pannelli esterni — vedi la [sezione finitura della Lista Acquisti](LISTA_ACQUISTI.md#7-leffetto-metallo--come-ottenere-la-finitura-del-film-).

## 3. Elettronica

⚠️ **Regola il buck converter XL4015 a 6,2 V col multimetro prima di collegare qualsiasi servo.** A 12 V i servo muoiono.

1. Catena di alimentazione: batteria 12 V → interruttore → si divide in (a) buck XL4015 a **6,2 V** → rail servo V+ del PCA9685, e (b) regolatore USB a 5 V → USB-C del Raspberry Pi.
2. PCA9685 → Pi via I2C (cavi dupont SDA/SCL/3V3/GND). Fai un fascio ordinato con la guaina termorestringente.
3. I servo si collegano ai canali del PCA9685 (la documentazione V3 mappa i canali; il codice legacy in questa repo usa 0–2 per gambe/sollevamento e 3–8 per le braccia).
4. Flat DSI del display → porta DSI del Pi; camera → porta camera; scheda audio USB + microfono → USB; altoparlante 8 Ω 5 W → scheda audio.
5. L'INA260 opzionale (unica saldatura della build) va in serie alla batteria per leggere lo stato di carica.

## 4. Assemblaggio meccanico

Segui passo passo la [wiki V3](https://github.com/TARS-AI-Community/TARS-AI/wiki/V3). Ordine che funziona:

1. **Vano elettronica** — buck converter, Pi e PCA9685 montati nel telaio.
2. **Torso** — metà del telaio, supporti gambe con il meccanismo di scorrimento lineare, servo principali (viti M3×20) con squadrette modificate, pannelli esterni.
3. **Gambe** — altoparlante nella gamba, suole in TPU, gambe inferiori al guscio (viti M3×16).
4. **Braccia (opzionali)** — magneti 10×3 mm per le mani, servo MG90S in avambracci/mani, prolunghe servo instradate nel torso.
5. Batteria fissata col velcro; interruttore nella sua sede.

## 5. Software

### Strada A — TARS-AI V3 (consigliata)

```bash
# 1. Flasha Raspberry Pi OS 64-bit con Raspberry Pi Imager
#    Abilita I2C, SPI e camera in raspi-config; aggiungi l'overlay DSI a config.txt

# 2. Installa
git clone -b V3 https://github.com/TARS-AI-Community/TARS-AI
cd TARS-AI
./Install.sh

# 3. Configura .env con le tue chiavi API
#    OPENAI_API_KEY  (obbligatoria)
#    ELEVENLABS_API_KEY  (consigliata per la voce del film)

# 4. Calibra i servo PRIMA del primo avvio
python app-servotester.py

# 5. Avvia
./tars-launcher.sh
```

Ottieni: dashboard web, interazione vocale con wake word, la personalità di TARS (umorismo regolabile — *"Qual è il tuo livello di umorismo, TARS?" "Al 100 percento."*), visione e il sistema di skill.

### Strada B — latishab/tars (distribuito)

```bash
pip install "tars-robot[daemon]"   # sul Pi
```

Il daemon espone gRPC (`:50051`) e WebRTC (`:8000`): il "cervello" IA può girare su un PC/server lasciando leggero il Pi. Dashboard su `http://tars.local:8000`. L'app `tars-conversation-app` aggiunge la voce IA (LLM+STT+TTS).

### Strada C — Controllo gamepad legacy (questa repo)

Lo stack di controllo originale stile Charles Diaz: accoppia un 8BitDo Zero 2, poi:

```bash
pip install evdev adafruit-pca9685
python TARSRunner.py
```

D-pad su = passo avanti, sinistra/destra = svolta, giù = posa, grilletti/tasti = braccia. Controlla `/dev/input/event*` per il numero del tuo gamepad. Perfetto per testare la meccanica prima di installare lo stack IA.

## 6. Calibrazione e primi passi

1. Col guscio aperto, lancia il servo tester e trova i valori PWM di neutro/min/max di ogni servo; il `ServoController.py` legacy mostra il tipo di valori attesi (es. altezza neutra 275, su 205, giù 450).
2. Stringi le squadrette dei servo solo dopo averli centrati.
3. Primo test di camminata sulla moquette/tappeto (più grip, le cadute fanno meno danni). L'andatura V3 atterra col torso a filo del pavimento, migliorando la camminata su superfici con attrito diverso.
4. Regola la personalità dalla UI web (umorismo %, onestà %, voce).

## 7. Licenza e crediti

- Contenuti/design **TARS-AI**: **CC BY-NC 4.0** — build personali/educative e modifiche sono permesse, **vendere pezzi stampati, kit o robot finiti no**. Attribuzione obbligatoria (vedi il loro [ATTRIBUTION.md](https://github.com/TARS-AI-Community/TARS-AI)).
- Build originale: **Charles Diaz** — [guida su Hackster.io](https://www.hackster.io/charlesdiaz/how-to-build-your-own-replica-of-tars-from-interstellar-224833).
- Community: [Discord TARS-AI](https://discord.gg/AmE2Gv9EUt) · [Wiki](https://github.com/TARS-AI-Community/TARS-AI/wiki) · [docs-tars-ai.vercel.app](https://docs-tars-ai.vercel.app)

*Livello di onestà: 90%. Buona costruzione.*
