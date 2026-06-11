# Cost Estimate — Line by Line

> Indicative mid-2026 prices, VAT included. "Amazon/EU" = fast local purchase; "AliExpress" = savings with 2–4 weeks of shipping. 🇮🇹 [Versione italiana](../it/STIMA_COSTI.md)

## 1. Core electronics (required)

| Component | Qty | Amazon/EU | AliExpress |
|---|---|---:|---:|
| Raspberry Pi 5 8 GB | 1 | €85 | — |
| Official Pi 5 Active Cooler | 1 | €6 | €4 |
| MicroSD 64 GB A2 (SanDisk Extreme) | 1 | €12 | €8 |
| 12 V Li-ion battery 3000 mAh + charger | 1 | €25 | €16 |
| XL4015E 5 A buck converter | 1 | €6 | €2 |
| 12V→5V 6 A USB regulator | 1 | €9 | €4 |
| Micro rocker switch | 1 | €3 | €1 |
| USB-C cable/breakout | 1 | €5 | €2 |
| PCA9685 16-channel (clone) | 1 | €8 | €3 |
| MG996R servos (4 + 2 spares) | 6 | €30 | €18 |
| Dupont F-F 40 cm cable kit | 1 | €6 | €2 |
| 20 AWG 2-conductor wire (2 m) | 1 | €5 | €2 |
| 5" DSI touch display | 1 | €40 | €28 |
| 200 mm DSI ribbon cable | 1 | €6 | €3 |
| OV5647 5 MP camera | 1 | €10 | €5 |
| USB sound card | 1 | €7 | €3 |
| 8 Ω 5 W speaker | 1 | €6 | €2 |
| Mini USB microphone | 1 | €9 | €4 |
| M3 assorted screw kit | 1 | €12 | €7 |
| Velcro, heat-shrink, spade connectors | — | €10 | €5 |
| **Core subtotal** | | **≈ €300** | **≈ €119 + Pi €85 ≈ €205** |

## 2. Optional extras

| Component | Qty | Price | Purpose |
|---|---|---:|---|
| MG90S servos (arms) | 4 | €16 | Articulated arms |
| 30 cm servo extension cables | 6 | €6 | Arms |
| 10×3 mm magnets | 4 | €5 | Magnetic hands |
| Upgrade: 2 extra MG996R | 2 | €10 | 6-servo leg version |
| Upgrade: 3× LD-3015MG instead of MG996R | 3 | +€25 | More torque, better walking |
| INA260 (battery monitoring) | 1 | €10 | Fuel gauge (requires soldering) |
| 8BitDo Zero 2 gamepad | 1 | €20 | Manual driving |
| **"Fully loaded" subtotal** | | **≈ €90** | |

## 3. 3D printer (if you don't own one)

| Model | EU price | Notes |
|---|---:|---|
| Bambu Lab A1 Mini | €199 | Check V3 part sizes first (180 mm bed) |
| Bambu Lab A1 | €299 | Best entry value |
| **Bambu Lab P1S** ⭐ | €599 | Enclosed → flawless PETG. The recommended pick |
| Bambu Lab X2D | ~€700 | Sensible top of the line |

## 4. Filament & finishing

| Material | Qty | Price |
|---|---|---:|
| PETG (structure) | 1.5 kg | €30 |
| TPU (foot pads) | 1 spool (200 g used) | €20 |
| Metallic silver PLA (hull panels) | 1 kg | €25–35 |
| **— or paint route:** filler primer + Rub 'n Buff/Metalcote + satin clear + sandpaper | — | €35–50 |
| **Subtotal** | | **≈ €75–100** |

## 5. Running costs (software/AI)

| Service | Cost | Notes |
|---|---:|---|
| OpenAI API (gpt-4o-mini + Whisper) | €1–5/month | Typical hobby usage; Whisper ≈ $0.006/min |
| ElevenLabs (movie-style voice) | €0–5/month | Free tier 10k chars; Starter $5/month |
| Fully offline alternative (Vosk + espeak-ng) | **€0** | Lower voice quality, free forever |
| Electricity | < €1/month | The Pi 5 draws ~5–10 W |

## 6. Totals per scenario

| Scenario | Electronics | Printer | Filament/finish | **Total** | **If you own a printer** |
|---|---:|---:|---:|---:|---:|
| **Budget** (AliExpress, no arms, A1, offline voice) | €205 | €299 | €75 | **≈ €580** | **≈ €280** |
| **Recommended** (mixed, arms, P1S, OpenAI+ElevenLabs) | €350 | €599 | €90 | **≈ €1,040** | **≈ €440** |
| **Premium** (LD-3015MG, INA260, gamepad, X2D, pro paint) | €420 | €700 | €110 | **≈ €1,230** | **≈ €530** |

💡 **How to save:** order everything except the Pi, display and battery from AliExpress (buy those locally for warranty); start without arms (the design lets you add them later); run the offline voice stack until you decide to pay for APIs.
