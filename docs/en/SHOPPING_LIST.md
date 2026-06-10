# TARS Shopping List — Everything You Need to Buy

> Complete bill of materials for a TARS-AI **V3** build (the current recommended design from the [TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI)), plus the 3D printer, filament, finishing supplies and a budget alternative.
>
> 🇮🇹 Versione italiana: [LISTA_ACQUISTI.md](../it/LISTA_ACQUISTI.md)

**Budget overview**

| Build | Electronics & hardware | 3D printer (if you don't own one) | Filament + finishing | Total |
|---|---|---|---|---|
| TARS-AI V3 (recommended) | ~$300–400 | $299–649 (Bambu Lab) | ~$40–80 | **~$350–1,100** |
| TARS-WIZARD (budget) | ~$200–280 | same | ~$40–80 | **~$250–1,000** |

---

## 1. Computing & power

| # | Item | Qty | Notes |
|---|---|---|---|
| 1 | **Raspberry Pi 5** — 8 GB recommended (4 GB minimum) | 1 | The brain. The Pi 5 is required for the V3 software stack; a Pi 4 4GB+ works with the latishab fork |
| 2 | **Raspberry Pi 5 Active Cooler** (official) | 1 | The Pi 5 throttles without it |
| 3 | **MicroSD card 32–64 GB** (A2, e.g. SanDisk Extreme) | 1 | For Raspberry Pi OS 64-bit |
| 4 | **12V Li-ion rechargeable battery pack ~3000 mAh + charger** | 1 | Main power source |
| 5 | **XL4015E DC 5A adjustable buck converter** | 1 | Steps 12V down for the servos — set output to **6.2V** |
| 6 | **DC 6A USB voltage regulator** (12V→5V USB) | 1 | Powers the Raspberry Pi |
| 7 | **Micro rocker switch** | 1 | Main power switch |
| 8 | **USB-C cable or USB-C male breakout board** | 1 | Pi power input (choose one) |

## 2. Motion (servos & control)

| # | Item | Qty | Notes |
|---|---|---|---|
| 9 | **PCA9685 16-channel PWM/servo driver** | 1 | I2C servo controller (Adafruit or clone) |
| 10 | **MG996R metal-gear servos** | 4 (6 with arms) | Legs/torso. Buy 1–2 spares — cheap clones vary in quality |
| 11 | **MG90S micro servos** | 4 | Arms version only |
| 12 | **12" (30 cm) servo extension cables** | 6 | Arms version only |
| 13 | **Dupont cables female-female, 40 cm** | 8 | I2C + power wiring |
| 14 | **20 AWG 2-conductor parallel wire** | ~2 m | Power distribution |

> 💪 **Upgrade option:** the TARS-WIZARD build uses 3× **LewanSoul LD-3015MG** (17 kg·cm) high-torque servos instead of MG996R — stronger and smoother walking, slightly more expensive.

## 3. Display, audio & vision

| # | Item | Qty | Notes |
|---|---|---|---|
| 15 | **5" DSI touchscreen** — one of: UeeKKoo 1024×600, Hosyond 800×480, Waveshare 800×480 | 1 | DSI, not HDMI — it's what fits the V3 chassis |
| 16 | **200 mm DSI ribbon cable** | 1 | Optional but makes assembly easier |
| 17 | **OV5647 5 MP camera module** | 1 | For vision / face detection |
| 18 | **USB sound card** | 1 | The Pi 5 has no audio jack |
| 19 | **8 Ω 5 W speaker** | 1 | TARS's voice |
| 20 | **USB microphone** (mini) | 1 | For voice commands / wake word |

## 4. Assembly hardware

| # | Item | Qty | Notes |
|---|---|---|---|
| 21 | **M3 screw assortment kit** (various lengths, with nuts) | 1–2 kits | Most used: M3×16 and M3×20 |
| 22 | **10×3 mm round magnets** | 4 | Arms version — magnetic hand attachment |
| 23 | **6" Velcro straps** | 2 | Battery mounting |
| 24 | **Heat-shrink tubing kit** | 1 | Clean wiring |
| 25 | **Spade connectors** | 2 | Battery/switch connections |
| 26 | **INA260 current/voltage sensor** | 1 | *Optional* — battery level monitoring (the only part that requires soldering) |
| 27 | **8BitDo Zero 2 Bluetooth gamepad** | 1 | *Optional* — manual driving with the code in this repo |

## 5. The 3D printer — which Bambu Lab to buy

You heard right: **Bambu Lab is the go-to brand right now** — fast, reliable, basically zero tinkering. Current lineup (2026):

| Model | Price | Pros | For TARS? |
|---|---|---|---|
| **Bambu Lab A1** | ~$299 / ~€299 | Cheapest, excellent quality, easy | ✅ Fine on a budget. Open frame → great for PLA, decent for PETG |
| **Bambu Lab A1 Mini** | ~$199 | Tiny and cheap | ⚠️ 180 mm bed — check the largest V3 parts fit before choosing it |
| **Bambu Lab P1S** ⭐ | ~$549 / ~€599 | **Enclosed**, fast, the reliability benchmark | ✅ **Recommended sweet spot.** The enclosure makes PETG/ABS printing trouble-free |
| **Bambu Lab X2D** | ~$649 | X1C successor (X1C is discontinued), heated chamber, LiDAR | ✅ Great if you want top of the line |
| **Bambu Lab H2D** | ~$1,899+ | Dual independent nozzles, 350×320×325 mm | Overkill for TARS |

**Bottom line:** buy the **P1S** if you can (enclosed = perfect PETG, which is the recommended TARS material); buy the **A1** if budget-limited. Add the **AMS/AMS lite** only if you want multi-color prints — not needed for TARS, which gets painted anyway.

Sources: [Bambu Lab comparison](https://bambulab.com/en-us/compare), [2026 buyer's guide](https://www.adpindustries.com/blog/bambu-lab-x1c-vs-p1s-vs-p2s-buyers-guide/), [MatterHackers guide](https://www.matterhackers.com/articles/comparison-guide-which-bambu-lab-3d-printer-is-right-for-me), [X2D review — Tom's Hardware](https://www.tomshardware.com/3d-printing/bambu-lab-x2d-review)

## 6. Filament — what to print TARS with

Official TARS-AI V3 recommendation:

| Filament | Amount | Use |
|---|---|---|
| **PETG** ⭐ | 1 kg (1.5 kg with arms) | **Recommended** — more rigid and durable for the moving chassis |
| **PLA** | 1 kg | Cheaper alternative; fine for a mostly-display TARS |
| **TPU** | 200 g | *Optional* — grippy foot pads, much better walking on smooth floors |

**Print settings (official V3):** 0.2 mm layer height · 3+ walls · 20% gyroid infill · 5 top/bottom layers · **no brim** · automatic **tree supports** with support threshold angle 10° (avoids blocking screw holes) · keep the parts in their pre-set orientation · print the **calibration guide first** (tolerances are ±0.02 mm).

## 7. The metal look — how to get the movie finish 🎬

TARS in the film is brushed stainless steel. Three ways to get there, easiest → best:

### Option A — Metallic filament, no painting (easy)
Print the outer hull panels directly in a metal-effect filament:
- [**Atomic Filament Metallic Silver V2 PLA**](https://atomicfilament.com/products/metallic-silver-pla-filament) — real aluminum-luster look, not abrasive
- [**Polymaker Panchroma Metallic PLA**](https://shop.polymaker.com/products/panchroma-metallic) (silver) — fine metallic powder shimmer, prints on any printer
- **Bambu Lab PLA Metal / PLA Silk silver** — convenient if you buy a Bambu printer
- Generic **"silk silver" PLA** — cheapest metal-ish effect

💡 Trick: metallic/silk filaments hide layer lines best at 0.12–0.16 mm layers, and matte-metal filaments look more "machined steel" than silk ones, which look chromier.

### Option B — Paint it (best result, what prop makers do)
This is how the replicas that look *real* are made:
1. **Sand** the printed panels: 240 → 400 → 600 grit
2. **Filler primer** (2 coats, sand lightly between) — kills the layer lines
3. **Metallic paint**, the options builders rate best:
   - **Vallejo Metal Color** (airbrush) — smooth modern metallics
   - **Humbrol Metalcote** — buffable enamel: paint, let dry, **buff with a soft cloth** for a genuine polished-steel sheen (rated better than Alclad by TARS prop builders on [TheRPF](https://www.therpf.com/forums/threads/tars-from-interstellar.366564/))
   - **Rub 'n Buff (Silver Leaf)** — wax you literally rub on; fastest brushed-metal effect
4. **Brushed effect:** after the metallic coat, drag very fine steel wool (#0000) or a Scotch-Brite pad in **one direction only** along each panel
5. **Satin clear coat** to seal (skip on Metalcote/Rub 'n Buff areas you buffed)

### Option C — Real metal-filled filament (heavy, expensive)
Stainless-steel-filled PLA (e.g. Proto-pasta) contains actual metal powder and can be polished to true metal. Caveats: needs a **hardened steel nozzle** (it's abrasive), parts are heavy (bad for walking), and it costs 3–4× normal filament. Best for a static display TARS only. For outsourced real-metal prints there are services like [Forgelabs](https://forgelabs.ca/).

## 8. Tools (if you don't have them)

- Phillips screwdriver set (M3) + small pliers
- Side cutters / wire stripper
- Multimeter — **required** to set the buck converter to 6.2 V before connecting anything
- Soldering iron — only if you install the optional INA260 sensor
- Flush cutters + needle files for cleaning printed parts
- CA glue (cyanoacrylate)

## 9. Budget alternative: TARS-WIZARD parts list (~$200–280)

The minimal build from [TARS-WIZARD](https://github.com/DhruvGoswami10/TARS-WIZARD): Raspberry Pi 5, **3× LD-3015MG** servos, PCA9685, 12V→5V converter, 11.1V LiPo 1300 mAh + charger, powerbank for the Pi, LCD, microphone, speaker, 8BitDo controller, 3D-printed body. Voice in 7 languages **including Italian** (GPT + Google STT + AWS Polly). Full list with links: [parts-list](https://github.com/DhruvGoswami10/TARS-WIZARD/blob/main/hardware/parts-list.md).

---

*Prices are mid-2026 ballparks; check AliExpress vs Amazon — many items are 2–3× cheaper on AliExpress with slower shipping.*
