# TarsGPT — Build Your Own TARS from Interstellar

🇬🇧 English | 🇮🇹 [Italiano più sotto](#tarsgpt--costruisci-il-tuo-tars-di-interstellar)

![TARS](https://github.com/user-attachments/assets/cb7f6acf-b7c4-41ff-ab1a-2640e8610c68)

TarsGPT is a guide and codebase for building a functional, AI-powered replica of TARS, the robot from Christopher Nolan's *Interstellar*. This repository consolidates the best knowledge from the entire TARS builder ecosystem — the original Charles Diaz build, the [TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI) project (the most active and complete), [latishab/tars](https://github.com/latishab/tars) (distributed architecture fork), and [TARS-WIZARD](https://github.com/DhruvGoswami10/TARS-WIZARD) (budget multilingual build) — into one place.

## 📚 Documentation

| English | Italiano |
|---|---|
| [Complete Build Guide](docs/en/BUILD_GUIDE.md) | [Guida completa alla costruzione](docs/it/GUIDA_COSTRUZIONE.md) |
| [Shopping List & 3D Printing Guide](docs/en/SHOPPING_LIST.md) | [Lista acquisti e guida alla stampa 3D](docs/it/LISTA_ACQUISTI.md) |

The shopping list covers **everything you need to buy**: electronics, servos, power, the recommended **Bambu Lab 3D printers**, which **filament** to use, and **how to achieve the movie-accurate brushed-metal finish**.

## 🤖 What's in this repo

| File | Purpose |
|---|---|
| `TARSRunner.py` | Initializes TARS and maps a Bluetooth gamepad (8BitDo Zero 2) to movements |
| `ServoController.py` | Low-level servo movements via the Adafruit PCA9685 driver |
| `ServoAbstractor.py` | High-level gaits (step forward, turn left/right, pose) composed from basic movements |
| `525125.STEP` | CAD reference file |

This code is the classic "legacy" gamepad-driven movement stack. For the full AI experience (voice, LLM personality, vision, web UI) follow the [Build Guide](docs/en/BUILD_GUIDE.md), which walks you through installing the TARS-AI Community software on top of the same hardware.

## 🌐 The TARS ecosystem at a glance

- **[TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI)** — the reference project. V3 hardware (no soldering, modular electronics), full AI stack (LLM + TTS + STT + wake word + web dashboard), 5 releases up to **OS Amelia** (2026). License: **CC BY-NC 4.0** (non-commercial, attribution required). Docs: [docs-tars-ai.vercel.app](https://docs-tars-ai.vercel.app) · [Wiki](https://github.com/TARS-AI-Community/TARS-AI/wiki) · [Discord](https://discord.gg/AmE2Gv9EUt)
- **[latishab/tars](https://github.com/latishab/tars)** — distributed-architecture fork: a hardware daemon on the Pi exposes gRPC/WebRTC APIs so AI apps can run on any machine. `pip install tars-robot[daemon]`.
- **[TARS-WIZARD](https://github.com/DhruvGoswami10/TARS-WIZARD)** ([site](https://tars-wizard.vercel.app)) — budget build (~$200–280), 3 servos, GPT personality, speech in 7 languages **including Italian**. MIT license.

## Credits

Based on the original build by **Charles Diaz** ([Hackster.io guide](https://www.hackster.io/charlesdiaz/how-to-build-your-own-replica-of-tars-from-interstellar-224833)) and on the work of the [TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI) and all the projects linked above. TARS-AI content is used under CC BY-NC 4.0 with attribution; this repository is likewise intended for personal, educational, non-commercial use.

---

# TarsGPT — Costruisci il tuo TARS di Interstellar

TarsGPT è una guida (con codice) per costruire una replica funzionante e dotata di IA di TARS, il robot di *Interstellar*. Questa repository riunisce il meglio dell'intero ecosistema TARS — la build originale di Charles Diaz, il progetto [TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI) (il più attivo e completo), [latishab/tars](https://github.com/latishab/tars) (architettura distribuita) e [TARS-WIZARD](https://github.com/DhruvGoswami10/TARS-WIZARD) (build economica e multilingua) — in un unico posto.

## 📚 Documentazione

- **[Guida completa alla costruzione (IT)](docs/it/GUIDA_COSTRUZIONE.md)** — stampa 3D, assemblaggio, elettronica, software IA
- **[Lista acquisti e guida alla stampa 3D (IT)](docs/it/LISTA_ACQUISTI.md)** — tutto quello che serve comprare: elettronica, servo, alimentazione, **quale stampante Bambu Lab scegliere**, **quale filamento usare** e **come ottenere l'effetto metallo spazzolato** identico al film

## 🤖 Contenuto della repo

- `TARSRunner.py` — avvia TARS e mappa il gamepad Bluetooth (8BitDo Zero 2) ai movimenti
- `ServoController.py` — movimenti base dei servo tramite driver Adafruit PCA9685
- `ServoAbstractor.py` — andature di alto livello (passo avanti, svolta, posa)
- `525125.STEP` — file CAD di riferimento

Questo codice è lo stack "classico" di movimento via gamepad. Per l'esperienza IA completa (voce, personalità LLM, visione, dashboard web) segui la [Guida alla costruzione](docs/it/GUIDA_COSTRUZIONE.md), che spiega come installare il software della TARS-AI Community sullo stesso hardware.

## Crediti

Basato sulla build originale di **Charles Diaz** e sul lavoro della [TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI) (licenza CC BY-NC 4.0, attribuzione obbligatoria, uso non commerciale) e degli altri progetti linkati sopra. Questa repository è destinata a uso personale, educativo e non commerciale.
