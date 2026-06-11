# Lista Acquisti TARS — Tutto Quello che Devi Comprare

> Distinta base (BOM) completa per una build TARS-AI **V3** (il design attualmente raccomandato dalla [TARS-AI Community](https://github.com/TARS-AI-Community/TARS-AI)), più stampante 3D, filamento, materiali per la finitura e un'alternativa economica.
>
> 🇬🇧 English version: [SHOPPING_LIST.md](../en/SHOPPING_LIST.md) · 💶 Prezzi voce per voce e totali per scenario: [STIMA_COSTI.md](STIMA_COSTI.md)

**Panoramica budget**

| Build | Elettronica e minuteria | Stampante 3D (se non la possiedi) | Filamento + finitura | Totale |
|---|---|---|---|---|
| TARS-AI V3 (consigliata) | ~300–400 € | 299–649 € (Bambu Lab) | ~40–80 € | **~350–1.100 €** |
| TARS-WIZARD (economica) | ~200–280 € | uguale | ~40–80 € | **~250–1.000 €** |

---

## 1. Calcolo e alimentazione

| # | Articolo | Q.tà | Note |
|---|---|---|---|
| 1 | **Raspberry Pi 5** — consigliati 8 GB (minimo 4 GB) | 1 | Il cervello. Il Pi 5 è richiesto dallo stack software V3; un Pi 4 4GB+ funziona col fork latishab |
| 2 | **Active Cooler ufficiale per Raspberry Pi 5** | 1 | Senza, il Pi 5 va in throttling |
| 3 | **MicroSD 32–64 GB** (A2, es. SanDisk Extreme) | 1 | Per Raspberry Pi OS 64-bit |
| 4 | **Pacco batteria Li-ion 12V ~3000 mAh + caricabatterie** | 1 | Alimentazione principale |
| 5 | **Convertitore buck regolabile XL4015E DC 5A** | 1 | Abbassa i 12V per i servo — regola l'uscita a **6,2 V** |
| 6 | **Regolatore di tensione USB DC 6A** (12V→5V USB) | 1 | Alimenta il Raspberry Pi |
| 7 | **Micro interruttore a bilanciere** | 1 | Interruttore generale |
| 8 | **Cavo USB-C o breakout board USB-C maschio** | 1 | Ingresso alimentazione del Pi (uno dei due) |

## 2. Movimento (servo e controllo)

| # | Articolo | Q.tà | Note |
|---|---|---|---|
| 9 | **Driver PWM/servo 16 canali PCA9685** | 1 | Controller servo I2C (Adafruit o clone) |
| 10 | **Servo MG996R a ingranaggi metallici** | 4 (6 con le braccia) | Gambe/torso. Comprane 1–2 di scorta: i cloni economici sono altalenanti |
| 11 | **Micro servo MG90S** | 4 | Solo versione con braccia |
| 12 | **Prolunghe servo 30 cm** | 6 | Solo versione con braccia |
| 13 | **Cavi Dupont femmina-femmina 40 cm** | 8 | Cablaggio I2C + alimentazione |
| 14 | **Cavo parallelo 2 conduttori 20 AWG** | ~2 m | Distribuzione alimentazione |

> 💪 **Upgrade:** la build TARS-WIZARD usa 3× **LewanSoul LD-3015MG** (17 kg·cm) ad alta coppia al posto degli MG996R — camminata più forte e fluida, costo leggermente superiore.
>
> 🧭 **Sensore opzionale:** un **IMU MPU-6050** (~3 €, I2C) rileva orientamento/cadute — **supportato**: se installato, il training dell'andatura penalizza le cadute automaticamente (sessioni completamente non supervisionate).

## 3. Display, audio e visione

| # | Articolo | Q.tà | Note |
|---|---|---|---|
| 15 | **Touchscreen DSI 5"** — uno tra: UeeKKoo 1024×600, Hosyond 800×480, Waveshare 800×480 | 1 | DSI, non HDMI — è quello che entra nel telaio V3 |
| 16 | **Cavo flat DSI 200 mm** | 1 | Opzionale ma facilita l'assemblaggio |
| 17 | **Modulo camera OV5647 5 MP** | 1 | Per visione / riconoscimento volti |
| 18 | **Scheda audio USB** | 1 | Il Pi 5 non ha jack audio |
| 19 | **Altoparlante 8 Ω 5 W** | 1 | La voce di TARS |
| 20 | **Microfono USB** (mini) | 1 | Comandi vocali / wake word |

## 4. Minuteria di assemblaggio

| # | Articolo | Q.tà | Note |
|---|---|---|---|
| 21 | **Kit viti M3 assortite** (varie lunghezze, con dadi) | 1–2 kit | Le più usate: M3×16 e M3×20 |
| 22 | **Magneti tondi 10×3 mm** | 4 | Versione con braccia — aggancio magnetico delle mani |
| 23 | **Fascette in velcro 15 cm** | 2 | Fissaggio batteria |
| 24 | **Kit guaina termorestringente** | 1 | Cablaggio pulito |
| 25 | **Connettori faston** | 2 | Collegamenti batteria/interruttore |
| 26 | **Sensore corrente/tensione INA260** | 1 | *Opzionale* — monitoraggio batteria (unico componente che richiede saldatura) |
| 27 | **Gamepad Bluetooth 8BitDo Zero 2** | 1 | *Opzionale* — guida manuale col codice di questa repo |

## 5. La stampante 3D — quale Bambu Lab comprare

Hai sentito bene: **Bambu Lab è il riferimento attuale** — veloce, affidabile, praticamente zero smanettamenti. Gamma attuale (2026):

| Modello | Prezzo | Pro | Per TARS? |
|---|---|---|---|
| **Bambu Lab A1** | ~299 € | La più economica, ottima qualità, facile | ✅ Va benissimo con budget limitato. Frame aperto → perfetta per PLA, discreta per PETG |
| **Bambu Lab A1 Mini** | ~199 € | Piccola ed economica | ⚠️ Piatto da 180 mm — verifica che i pezzi V3 più grandi ci entrino prima di sceglierla |
| **Bambu Lab P1S** ⭐ | ~599 € | **Chiusa**, veloce, il riferimento per affidabilità | ✅ **Il punto di equilibrio consigliato.** La camera chiusa rende il PETG/ABS senza problemi |
| **Bambu Lab X2D** | ~649 $ | Erede della X1C (ormai fuori produzione), camera riscaldata, LiDAR | ✅ Ottima se vuoi il top |
| **Bambu Lab H2D** | ~1.899 €+ | Doppio estrusore indipendente, 350×320×325 mm | Sovradimensionata per TARS |

**In sintesi:** compra la **P1S** se puoi (chiusa = PETG perfetto, che è il materiale consigliato per TARS); la **A1** se sei a budget. L'**AMS/AMS lite** serve solo per stampe multicolore — non necessario per TARS, che tanto si vernicia.

Fonti: [confronto Bambu Lab](https://bambulab.com/en-us/compare), [guida all'acquisto 2026](https://www.adpindustries.com/blog/bambu-lab-x1c-vs-p1s-vs-p2s-buyers-guide/), [guida MatterHackers](https://www.matterhackers.com/articles/comparison-guide-which-bambu-lab-3d-printer-is-right-for-me), [recensione X2D — Tom's Hardware](https://www.tomshardware.com/3d-printing/bambu-lab-x2d-review)

## 6. Filamento — con cosa stampare TARS

Raccomandazione ufficiale TARS-AI V3:

| Filamento | Quantità | Uso |
|---|---|---|
| **PETG** ⭐ | 1 kg (1,5 kg con le braccia) | **Consigliato** — più rigido e resistente per il telaio in movimento |
| **PLA** | 1 kg | Alternativa più economica; va bene per un TARS prevalentemente da esposizione |
| **TPU** | 200 g | *Opzionale* — suole dei piedi antiscivolo, camminata molto migliore sui pavimenti lisci |

**Impostazioni di stampa (ufficiali V3):** layer 0,2 mm · almeno 3 perimetri · riempimento 20% gyroid · 5 layer superiori/inferiori · **niente brim** · **supporti ad albero** automatici con angolo soglia supporti a 10° (evita di bloccare i fori delle viti) · mantieni l'orientamento predefinito dei pezzi · stampa **prima il pezzo di calibrazione** (tolleranze ±0,02 mm).

## 7. L'effetto metallo — come ottenere la finitura del film 🎬

Il TARS del film è acciaio inox spazzolato. Tre strade, dalla più facile alla migliore:

### Opzione A — Filamento metallizzato, senza verniciare (facile)
Stampa i pannelli esterni direttamente in filamento effetto metallo:
- [**Atomic Filament Metallic Silver V2 PLA**](https://atomicfilament.com/products/metallic-silver-pla-filament) — vera lucentezza da alluminio, non abrasivo
- [**Polymaker Panchroma Metallic PLA**](https://shop.polymaker.com/products/panchroma-metallic) (silver) — polvere metallica fine, stampa su qualsiasi macchina
- **Bambu Lab PLA Metal / PLA Silk silver** — comodo se compri una stampante Bambu
- **PLA "silk silver" generico** — l'effetto metallo più economico

💡 Trucco: i filamenti silk/metallizzati nascondono meglio le linee di stampa a layer 0,12–0,16 mm; i filamenti metallo *opachi* sembrano più "acciaio lavorato", quelli silk più cromati.

### Opzione B — Verniciatura (risultato migliore, il metodo dei prop maker)
È così che si fanno le repliche che sembrano *vere*:
1. **Carteggia** i pannelli stampati: grana 240 → 400 → 600
2. **Primer riempitivo** (2 mani, carteggiatura leggera tra una e l'altra) — elimina le linee di stampa
3. **Vernice metallizzata**, le opzioni più apprezzate dai builder:
   - **Vallejo Metal Color** (aerografo) — metallizzati moderni e lisci
   - **Humbrol Metalcote** — smalto lucidabile: vernicia, lascia asciugare e **lucida con un panno morbido** per un vero effetto acciaio (valutato meglio dell'Alclad dai builder di TARS su [TheRPF](https://www.therpf.com/forums/threads/tars-from-interstellar.366564/))
   - **Rub 'n Buff (Silver Leaf)** — cera da strofinare; l'effetto metallo spazzolato più rapido
4. **Effetto spazzolato:** dopo la mano metallizzata, passa lana d'acciaio finissima (#0000) o un panno Scotch-Brite in **un'unica direzione** su ogni pannello
5. **Trasparente satinato** per sigillare (saltalo sulle zone lucidate a Metalcote/Rub 'n Buff)

### Opzione C — Filamento caricato a metallo vero (pesante, costoso)
Il PLA caricato acciaio inox (es. Proto-pasta) contiene vera polvere di metallo e si può lucidare fino a un effetto metallo autentico. Avvertenze: serve un **ugello in acciaio temprato** (è abrasivo), i pezzi sono pesanti (male per la camminata) e costa 3–4 volte un filamento normale. Ha senso solo per un TARS statico da esposizione. Per stampe in metallo vero conto terzi esistono servizi come [Forgelabs](https://forgelabs.ca/).

## 8. Attrezzi (se non li hai già)

- Set cacciaviti Phillips (M3) + pinze piccole
- Tronchesina / spelafili
- Multimetro — **indispensabile** per tarare il buck converter a 6,2 V prima di collegare qualsiasi cosa
- Saldatore — solo se monti il sensore INA260 opzionale
- Tronchesi a filo + limette per pulire i pezzi stampati
- Colla cianoacrilica (Attak)

## 9. Alternativa economica: lista TARS-WIZARD (~200–280 $)

La build minimale di [TARS-WIZARD](https://github.com/DhruvGoswami10/TARS-WIZARD): Raspberry Pi 5, **3× servo LD-3015MG**, PCA9685, convertitore 12V→5V, LiPo 11,1V 1300 mAh + caricabatterie, powerbank per il Pi, LCD, microfono, altoparlante, controller 8BitDo, corpo stampato in 3D. Voce in 7 lingue **incluso l'italiano** (GPT + Google STT + AWS Polly). Lista completa con link: [parts-list](https://github.com/DhruvGoswami10/TARS-WIZARD/blob/main/hardware/parts-list.md).

---

*I prezzi sono indicativi (metà 2026); confronta AliExpress e Amazon — molti articoli costano 2–3 volte meno su AliExpress con spedizioni più lente.*
