# Stima dei Costi — Voce per Voce

> Prezzi indicativi metà 2026, IVA inclusa. Colonna "Amazon/IT" = acquisto rapido in Italia; colonna "AliExpress" = risparmio con 2–4 settimane di attesa. 🇬🇧 [English version](../en/COST_ESTIMATE.md)

## 1. Elettronica di base (obbligatoria)

| Componente | Q.tà | Amazon/IT | AliExpress |
|---|---|---:|---:|
| Raspberry Pi 5 8 GB | 1 | 85 € | — |
| Active Cooler ufficiale Pi 5 | 1 | 6 € | 4 € |
| MicroSD 64 GB A2 (SanDisk Extreme) | 1 | 12 € | 8 € |
| Batteria Li-ion 12 V 3000 mAh + caricatore | 1 | 25 € | 16 € |
| Buck converter XL4015E 5 A | 1 | 6 € | 2 € |
| Regolatore USB 12V→5V 6 A | 1 | 9 € | 4 € |
| Micro interruttore a bilanciere | 1 | 3 € | 1 € |
| Cavo/breakout USB-C | 1 | 5 € | 2 € |
| PCA9685 16 canali (clone) | 1 | 8 € | 3 € |
| Servo MG996R (4 + 2 scorta) | 6 | 30 € | 18 € |
| Cavi Dupont F-F 40 cm (kit) | 1 | 6 € | 2 € |
| Cavo 20 AWG 2 poli (2 m) | 1 | 5 € | 2 € |
| Display DSI 5" touch | 1 | 40 € | 28 € |
| Cavo flat DSI 200 mm | 1 | 6 € | 3 € |
| Camera OV5647 5 MP | 1 | 10 € | 5 € |
| Scheda audio USB | 1 | 7 € | 3 € |
| Altoparlante 8 Ω 5 W | 1 | 6 € | 2 € |
| Microfono USB mini | 1 | 9 € | 4 € |
| Kit viti M3 assortite | 1 | 12 € | 7 € |
| Velcro, guaina, faston | — | 10 € | 5 € |
| **Subtotale base** | | **≈ 300 €** | **≈ 119 € + Pi 85 € ≈ 205 €** |

## 2. Opzionali

| Componente | Q.tà | Prezzo | Per cosa |
|---|---|---:|---|
| Servo MG90S (braccia) | 4 | 16 € | Braccia articolate |
| Prolunghe servo 30 cm | 6 | 6 € | Braccia |
| Magneti 10×3 mm | 4 | 5 € | Mani magnetiche |
| Upgrade: 2× servo MG996R extra | 2 | 10 € | Versione 6 servo gambe |
| Upgrade: 3× LD-3015MG al posto degli MG996R | 3 | +25 € | Coppia maggiore, camminata migliore |
| INA260 (monitoraggio batteria) | 1 | 10 € | Indicatore carica (richiede saldatura) |
| Gamepad 8BitDo Zero 2 | 1 | 20 € | Guida manuale |
| **Subtotale "tutto incluso"** | | **≈ 90 €** | |

## 3. Stampante 3D (se non la possiedi)

| Modello | Prezzo IT | Note |
|---|---:|---|
| Bambu Lab A1 Mini | 199 € | Verifica dimensioni pezzi V3 (piatto 180 mm) |
| Bambu Lab A1 | 299 € | Il miglior rapporto qualità/prezzo entry |
| **Bambu Lab P1S** ⭐ | 599 € | Chiusa → PETG perfetto. La scelta consigliata |
| Bambu Lab X2D | ~700 € | Top di gamma sensato |

## 4. Filamento e finitura

| Materiale | Q.tà | Prezzo |
|---|---|---:|
| PETG (strutture) | 1,5 kg | 30 € |
| TPU (suole piedi) | 1 bobina (ne usi 200 g) | 20 € |
| PLA metallizzato silver (pannelli) | 1 kg | 25–35 € |
| **— oppure verniciatura:** primer riempitivo + Rub 'n Buff/Metalcote + trasparente satinato + carta abrasiva | — | 35–50 € |
| **Subtotale** | | **≈ 75–100 €** |

## 5. Costi ricorrenti (software/IA)

| Servizio | Costo | Note |
|---|---:|---|
| OpenAI API (gpt-4o-mini + Whisper) | 1–5 €/mese | Uso hobbistico tipico; Whisper ≈ 0,006 $/min |
| ElevenLabs (voce stile film) | 0–5 €/mese | Tier gratuito 10k caratteri; Starter 5 $/mese |
| Alternativa 100% offline (Vosk + espeak-ng) | **0 €** | Qualità voce inferiore ma gratis per sempre |
| Elettricità | < 1 €/mese | Il Pi 5 consuma ~5–10 W |

## 6. Totali per scenario

| Scenario | Elettronica | Stampante | Filamento/finitura | **Totale** | **Se hai già la stampante** |
|---|---:|---:|---:|---:|---:|
| **Budget** (AliExpress, niente braccia, A1, voce offline) | 205 € | 299 € | 75 € | **≈ 580 €** | **≈ 280 €** |
| **Consigliato** (mix, braccia, P1S, OpenAI+ElevenLabs) | 350 € | 599 € | 90 € | **≈ 1.040 €** | **≈ 440 €** |
| **Premium** (LD-3015MG, INA260, gamepad, X2D, verniciatura pro) | 420 € | 700 € | 110 € | **≈ 1.230 €** | **≈ 530 €** |

💡 **Come risparmiare:** ordina su AliExpress tutto tranne Pi, display e batteria (comprali in Italia per la garanzia); parti senza braccia (le aggiungi dopo, è previsto dal design); usa lo stack vocale offline finché non decidi di pagare le API.
