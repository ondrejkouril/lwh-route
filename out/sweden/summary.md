# Long Way Home – home via Sweden

Variant of the chosen route: from D18 From Nordkapp home through Sweden: Vildmarksvägen, Flatruet, Karlsborg and the Göta Canal, a night ferry Ystad → Świnoujście, then motorways via the Międzyrzecz bunkers. One day shorter than the Finland and Baltics route. 12 days instead of 13. Day files here cover only the variant days; all other days are in `out/days/`.

**29 riding days · 2027-06-15 → 2027-07-13 · 9,570 km road · ≈149 h riding** (excl. ferries)

Distances and times come from a BRouter `car-fast` track (OSRM fallback where noted). Riding hours = router drive time × 1.10, excluding stops and ferries. **Final curvy routing happens in Kurviger** – import the `<rte>` (via + shaping points) and let Kurviger compute the motorcycle route; the BRouter `<trk>` is only for distance/time and a visual check.

## ⚠ Season dependency

This route is only viable **mid-June to mid-August**. These roads/ferries are seasonal – **verify opening status on vegvesen.no (and the ferry operators) before departure**:

- **Fv450 Suleskarvegen** (D06) – usually opens around June; verify on vegvesen.no
- **Fv500 Lysevegen** (D06) – usually opens late May / June; verify on vegvesen.no
- **Fv243 Aurlandsfjellet (Snøvegen)** (D08) – usually opens late May / June; verify on vegvesen.no
- **Rv55 Sognefjellet** (D08) – usually opens May; verify on vegvesen.no
- **Fv63 Trollstigen** (D09) – usually opens late May; verify on vegvesen.no
- **Fv63 Geiranger–Langvatn** (D09) – usually opens May; verify on vegvesen.no
- **Nibbevegen (Dalsnibba summit road)** (D09) – usually opens late May / June; verify on vegvesen.no
- **Lysefjord car ferry Lysebotn–Stavanger** (D06) – summer timetable only; verify on the ferry operator (Kolumbus)
- **Fv520 Saudafjellet (Sauda–Røldal, ~960 m)** (D07) – usually opens late May / June; verify on vegvesen.no
- **Andenes–Gryllefjord ferry (Andøya–Senja)** (D15) – summer only (2026 season: 13 May – 27 Sep); verify on the ferry operator (svipper.no / entur.no)
- **Vildmarksvägen over Stekenjokk (≈ 870 m)** (D22) – closed mid-October to early June; verify on trafikverket.se

If the Lysefjord ferry is not running, ride `D06_alt.gpx` instead.

## Day table

| Day | Date | Route | km | target | h | Ferries | Tolls | Seasonal | Overnight (type) | LWH stops | Max fuel gap |
|---|---|---|--:|--:|--:|---|---|---|---|---|--:|
| D01 | 2027-06-15 | Kobylnice → Spreewald | 525 | 500 | 5.3 | – | – | – | Lübbenau/Spreewald (campsite cabin) | – | 36 |
| D02 | 2027-06-16 | Spreewald → Faaborg | 490 | 440 | 5.6 | Rostock–Gedser; Tårs–Spodsbjerg | – | – | Hvedholm Slotshotel (hotel) | Hvedholm Slotshotel | 82 |
| D03 | 2027-06-17 | Faaborg → Tvååker | 466 | 450 | 6.1 | – | storebaelt; oresund | – | Strömma Farmlodge (hotel) | Hvedholm Slotshotel; Malmö; Strömma Farmlodge | 25 |
| D04 | 2027-06-18 | Tvååker → Oslo | 439 | 420 | 6.1 | – | – | – | Oslo (hotel) | Strömma Farmlodge | 46 |
| D05 | 2027-06-19 | Oslo → Haukeli | 303 | 330 | 5.8 | – | – | – | Haukeliseter (wild camp) | – | 46 |
| D06 | 2027-06-20 | Haukeli → Lysebotn → Stavanger | 199 | 230 | 4.2 | Lysebotn–Stavanger (Lysefjord, seasonal) | – | Fv450 Suleskarvegen; Fv500 Lysevegen; Lysefjord car ferry Lysebotn–Stavanger | Stavanger (hotel) | Øygardstøl; Lysebotn ferry quay | 86 |
| D07 | 2027-06-21 | Stavanger → Voss | 313 | 330 | 6.9 | Hjelmeland–Nesvik | ryfast; autopass | Fv520 Saudafjellet (Sauda–Røldal, ~960 m) | Voss (campsite cabin) | – | 77 |
| D08 | 2027-06-22 | Voss → Lom | 338 | 340 | 7.1 | Fodnes–Mannheller | – | Fv243 Aurlandsfjellet (Snøvegen); Rv55 Sognefjellet | Lom (wild camp) | Gudvangen – Viking Valley | 77 |
| D09 | 2027-06-23 | Lom → Kristiansund | 321 | 300 | 6.7 | Eidsdal–Linge; Åfarnes–Sølsnes | dalsnibba | Nibbevegen (Dalsnibba summit road); Fv63 Geiranger–Langvatn; Fv63 Trollstigen | Kristiansund (hotel) | – | 79 |
| D10 | 2027-06-24 | Kristiansund → Steinkjer | 409 | 380 | 7.4 | – | – | – | Steinkjer (campsite cabin) | – | 35 |
| D11 | 2027-06-25 | Steinkjer → Mo i Rana | 353 | 400 | 5.9 | – | – | – | Mo i Rana (wild camp) | – | 73 |
| D12 | 2027-06-26 | Mo i Rana → Reine (Lofoten) | 255 | 230 | 4.9 | Bodø–Moskenes | – | – | Reine (campsite cabin) | Polarsirkelsenteret (Arctic Circle Centre) | 94 |
| D13 | 2027-06-27 | Reine → Svolvær (Lofoten) | 142 | 150 | 3.0 | – | – | – | Svolvær (campsite cabin) | – | 55 |
| D14 | 2027-06-28 | Svolvær → Andøya → Andenes | 221 | 220 | 4.0 | – | – | – | Andenes (campsite cabin) | – | 110 |
| D15 | 2027-06-29 | Andenes → Senja → Tromsø | 135 | 140 | 3.0 | Andenes–Gryllefjord (Andøya–Senja, seasonal); Botnhamn–Brensholmen | – | Andenes–Gryllefjord ferry (Andøya–Senja) | Tromsø (hotel) | Tromsø | 52 |
| D16 | 2027-06-30 | Tromsø → Lyngen → Alta | 284 | 270 | 5.0 | Breivikeidet–Svensby; Lyngseidet–Olderdalen | – | – | Alta (wild camp) | Tromsø | 70 |
| D17 | 2027-07-01 | Alta → Nordkapp → Honningsvåg | 270 | 230 | 5.1 | – | – | – | Honningsvåg (campsite cabin) | – | 158 |
| D18 | 2027-07-02 | Nordkapp → Karasjok → Kautokeino | 365 | 370 | 6.3 | – | – | – | Kautokeino (campsite cabin) | – | 127 |
| D19 | 2027-07-03 | Kautokeino → Karesuando → Kiruna | 320 | 320 | 4.3 | – | – | – | Kiruna (hotel) | – | 89 |
| D20 | 2027-07-04 | Kiruna → Gällivare → Jokkmokk → Arvidsjaur | 366 | 370 | 4.9 | – | – | – | Arvidsjaur (campsite cabin) | – | 58 |
| D21 | 2027-07-05 | Arvidsjaur → Arjeplog → Sorsele → Vilhelmina | 316 | 320 | 4.4 | – | – | – | Vilhelmina (campsite cabin) | – | 90 |
| D22 | 2027-07-06 | Vildmarksvägen – Vilhelmina → Stekenjokk → Strömsund | 364 | 380 | 5.5 | – | – | Vildmarksvägen over Stekenjokk (≈ 870 m) | Strömsund (campsite cabin) | – | 133 |
| D23 | 2027-07-07 | Strömsund → Östersund → Flatruet → Funäsdalen | 337 | 330 | 5.7 | – | – | – | Funäsdalen (campsite cabin) | – | 91 |
| D24 | 2027-07-08 | Funäsdalen → Sveg → Orsa → Mora | 277 | 280 | 4.0 | – | – | – | Mora (hotel) | – | 75 |
| D25 | 2027-07-09 | Mora → Malung → Klarälven valley → Karlstad | 246 | 250 | 3.9 | – | – | – | Karlstad (hotel) | – | 50 |
| D26 | 2027-07-10 | Karlstad → Göta Canal → Karlsborg → Jönköping | 263 | 270 | 4.5 | – | – | – | Jönköping (hotel) | – | 42 |
| D27 | 2027-07-11 | Jönköping → Växjö → Ales stenar → Ystad ⛴ | 384 | 380 | 5.4 | Ystad–Świnoujście (night ferry) | – | – | Cabin on board, arriving ≈ 06:00–07:00 (ferry cabin) | – | 41 |
| D28 | 2027-07-12 | Świnoujście → Międzyrzecz bunkers → Wrocław | 482 | 480 | 5.0 | – | – | – | Wrocław (hotel) | – | 36 |
| D29 | 2027-07-13 | Wrocław → Gliwice → Ostrava → Kobylnice | 387 | 400 | 3.3 | – | – | – | Kobylnice (home) | – | 27 |

`*` = likely LWH location (strong match, not confirmed on screen). Day numbers are trip days; the `yaml_id` column in summary.csv maps them to `data/route.yaml`.

### Alternatives (not in totals)

| File | Route | km | h | Ferries |
|---|---|--:|--:|---|
| D06_alt | Haukeli → Lysebotn → Stavanger (no ferry fallback) | 344 | 7.5 | – |
| D08_alt | Voss → Tindevegen → Lom | 318 | 6.9 | – |
| D09_alt | Lom → Gamle Strynefjellsvegen → Kristiansund | 350 | 7.5 | Eidsdal–Linge; Åfarnes–Sølsnes |

## Buffer days

1 unassigned weather/rest day(s). Most valuable around D06–D09 (seasonal Norwegian roads), D12 (Bodø–Moskenes ferry) and the night ferry day.

## Ferries

| Ferry | Operator | ≈ h | Book ahead | Day |
|---|---|--:|---|---|
| Rostock–Gedser | Scandlines | 2.0 | yes | D02 |
| Tårs–Spodsbjerg | Molslinjen / Langelandsfærgen | 0.75 | walk-up usually fine | D02 |
| Lysebotn–Stavanger (Lysefjord, seasonal) | Kolumbus / Norled seasonal car ferry | 3.5 | yes | D06 |
| Hjelmeland–Nesvik | Norled | 0.25 | walk-up usually fine | D07 |
| Fodnes–Mannheller | Fjord1 | 0.25 | walk-up usually fine | D08 |
| Eidsdal–Linge | Fjord1 | 0.25 | walk-up usually fine | D09 |
| Åfarnes–Sølsnes | Fjord1 | 0.3 | walk-up usually fine | D09 |
| Bodø–Moskenes | Torghatten Nord | 3.5 | **yes – critical in July** | D12 |
| Andenes–Gryllefjord (Andøya–Senja, seasonal) | Svipper (Troms county ferries) | 1.7 | yes | D15 |
| Botnhamn–Brensholmen | Svipper (Troms county ferries) | 0.75 | walk-up usually fine | D15 |
| Breivikeidet–Svensby | Boreal Sjø | 0.3 | walk-up usually fine | D16 |
| Lyngseidet–Olderdalen | Boreal Sjø | 0.7 | walk-up usually fine | D16 |
| Ystad–Świnoujście (night ferry) | Polferries / Unity Line | 7.5 | yes | D27 |

Operators change – confirm timetables and operator names before booking.

## Tolls

- Storebælt Bridge (DK) – pay at toll plaza / BroBizz
- Øresund Bridge (DK–SE) – pay at toll plaza / BroBizz
- Ryfast tunnels (NO) – AutoPASS
- Norway: register bike + card with AutoPASS for ferries & tolls (Ferjepass / EPC); motorcycles are exempt from many road tolls – verify current rules
- Nibbevegen to Dalsnibba summit – private toll road
- Czech motorways: motorcycles are currently vignette-exempt; Germany & Polish A1/S-roads used here are toll-free for motorcycles – verify before travel.

## Fuel

Gaps measured along each day's track between OSM `amenity=fuel` stations within 1.5 km (Overpass), including day start → first station. Days with > 180 km between stations:

- none above the threshold (still fill up at every chance in Lapland, Finnmark and on Norwegian mountain roads).

## Wild camping rules

- **Norway**: Allemannsretten: up to 2 nights in one spot on uncultivated land, ≥150 m from houses/cabins; fire ban 15 Apr–15 Sep near forest.
- **Sweden**: Allemansrätten: 1–2 nights, out of sight of houses, not on farmland; respect local fire bans.
- **Finland**: Jokamiehenoikeus: short-term camping allowed away from homes; no open fire without landowner permission; NP campsites in Linnansaari.
- **Estonia**: Use free RMK campsites/forest huts (rmk.ee); otherwise landowner permission needed.
- **Latvia**: Generally tolerated on public land away from houses; campsites recommended near Riga/Gauja NP.
- **Lithuania**: Only at designated campsites/rest areas; wild camping in parks is fined.
- **Denmark**: No wild camping – use campsites or free shelters (shelter.dk / udinaturen.dk).
- **Germany**: No wild camping – campsites only.
- **Poland**: Only on designated forest areas ('Zanocuj w lesie' programme) or campsites.

## Open items

1. Book the Bodø–Moskenes ferry as soon as the 2027 timetable opens (critical in late June / July).
2. Book the Andenes–Gryllefjord ferry as soon as the 2027 timetable is out (summer only, 2–3 sailings a day; new operating contract from 16 May 2027) – day D15.
3. Book the Ystad–Świnoujście night ferry with a cabin (Polferries or Unity Line) – day D27.
4. Check the Lysefjord car-ferry summer timetable for the D06 date; ride `D06_alt.gpx` if it is not running.
5. Check the opening times of the Międzyrzecz bunker tours in Pniewo and book a guided tour – day D28.
6. TET gravel: put the TET GPX from transeurotrail.org into `input/tet/` and run `route --tet` + `build --tet` for a private build in `out_tet/` – sections: D26 Kristinehamn → Töreboda (`swe.gpx`); D26 Karlsborg → Hjo (`swe.gpx`); D27 Hässleholm → Kåseberga (`swe.gpx`).
