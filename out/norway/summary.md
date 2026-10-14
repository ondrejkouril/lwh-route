# Long Way Home – fast through Norway

Variant: The whole length of Norway, from Lindesnes to Nordkapp (day 11), riding rather than sailing, then home through Finland and the Baltics. 19 riding days. Not the chosen route.

**19 riding days · 2027-06-15 → 2027-07-03 · 7,640 km road · ≈114 h riding** (excl. ferries)

Distances and times come from a BRouter `car-fast` track (OSRM fallback where noted). Riding hours = router drive time × 1.10, excluding stops and ferries. **Final curvy routing happens in Kurviger** – import the `<rte>` (via + shaping points) and let Kurviger compute the motorcycle route; the BRouter `<trk>` is only for distance/time and a visual check.

## ⚠ Season dependency

This route is only viable **mid-June to mid-August**. These roads/ferries are seasonal – **verify opening status on vegvesen.no (and the ferry operators) before departure**:

- **Fv63 Trollstigen** (D06) – usually opens late May; verify on vegvesen.no
- **Fv63 Geiranger–Langvatn** (D05) – usually opens May; verify on vegvesen.no
- **Nibbevegen (Dalsnibba summit road)** (D05) – usually opens late May / June; verify on vegvesen.no
- **Fv520 Saudafjellet (Sauda–Røldal, ~960 m)** (D04) – usually opens late May / June; verify on vegvesen.no

## Day table

| Day | Date | Route | km | target | h | Ferries | Tolls | Seasonal | Overnight (type) | LWH stops | Max fuel gap |
|---|---|---|--:|--:|--:|---|---|---|---|---|--:|
| D01 | 2027-06-15 | Kobylnice → Wittstock | 746 | 745 | 7.0 | – | – | – | Wittstock/Dosse (hotel) | – | n/a |
| D02 | 2027-06-16 | Wittstock → Hamburg → Hirtshals | 684 | 680 | 6.1 | – | – | – | Hirtshals (hotel) | – | n/a |
| D03 | 2027-06-17 | Hirtshals ⛴ Kristiansand → Lindesnes → Stavanger | 294 | 300 | 6.6 | Hirtshals–Kristiansand | – | – | Stavanger (hotel) | – | n/a |
| D04 | 2027-06-18 | Stavanger → Voss | 313 | 315 | 6.9 | Hjelmeland–Nesvik | ryfast; autopass | Fv520 Saudafjellet (Sauda–Røldal, ~960 m) | Voss (campsite cabin) | – | 77 |
| D05 | 2027-06-19 | Voss → Gaularfjellet → Stryn → Geiranger | 356 | 360 | 7.5 | Vangsnes–Dragsvik | dalsnibba | Fv63 Geiranger–Langvatn; Nibbevegen (Dalsnibba summit road) | Geiranger (campsite cabin) | – | n/a |
| D06 | 2027-06-20 | Geiranger → Trollstigen → Dovrefjell → Trondheim | 388 | 390 | 7.0 | Eidsdal–Linge | – | Fv63 Trollstigen | Trondheim (hotel) | – | n/a |
| D07 | 2027-06-21 | Trondheim → Stiklestad → Mosjøen | 388 | 385 | 6.7 | – | – | – | Mosjøen (campsite cabin) | – | n/a |
| D08 | 2027-06-22 | Mosjøen → Arctic Circle → Bodø ⛴ Reine | 340 | 345 | 6.5 | Bodø–Moskenes | – | – | Reine (campsite cabin) | Polarsirkelsenteret (Arctic Circle Centre) | n/a |
| D09 | 2027-06-23 | Reine → Lofoten → Lofast → Setermoen | 387 | 395 | 7.1 | – | – | – | Setermoen (campsite cabin) | – | n/a |
| D10 | 2027-06-24 | Setermoen → Lyngen fjords → Alta | 397 | 395 | 6.6 | – | – | – | Alta (campsite cabin) | – | n/a |
| D11 | 2027-06-25 | Alta → Nordkapp → Honningsvåg | 270 | 270 | 5.1 | – | – | – | Honningsvåg (campsite cabin) | – | 158 |
| D12 | 2027-06-26 | Nordkapp → Karasjok → Inari | 354 | 355 | 5.8 | – | – | – | Inari (campsite cabin) | – | 99 |
| D13 | 2027-06-27 | Inari → Rovaniemi | 328 | 330 | 4.3 | – | – | – | Rovaniemi (hotel) | – | n/a |
| D14 | 2027-06-28 | Rovaniemi → Oulu → Pyhäsalmi | 385 | 390 | 4.9 | – | – | – | Pyhäsalmi (hotel) | – | n/a |
| D15 | 2027-06-29 | Pyhäsalmi → Jyväskylä → Helsinki | 455 | 455 | 5.7 | – | – | – | Helsinki (hotel) | Helsinki | n/a |
| D16 | 2027-06-30 | Helsinki → Tallinn → Riga | 328 | 320 | 5.5 | Helsinki–Tallinn | – | – | Riga (hotel) | Helsinki; Helsinki West Harbour; Tallinn Old City Harbour; Riga | 80 |
| D17 | 2027-07-01 | Riga → Kaunas → Augustów | 427 | 430 | 5.9 | – | – | – | Augustów (hotel) | Riga | 30 |
| D18 | 2027-07-02 | Augustów → Warsaw → Piotrków Trybunalski | 403 | 410 | 4.6 | – | – | – | Piotrków Trybunalski (hotel) | – | 27 |
| D19 | 2027-07-03 | Piotrków Trybunalski → Kobylnice | 397 | 400 | 4.0 | – | – | – | Kobylnice (home) | – | 25 |

`*` = likely LWH location (strong match, not confirmed on screen). Day numbers are trip days; the `yaml_id` column in summary.csv maps them to `data/route.yaml`.

## Buffer days

None – this is the fast version and every day is a riding day. If weather costs a day the trip simply ends a day later: after Bodø–Moskenes nothing is booked except the Helsinki–Tallinn ferry, which sails many times a day.

## Ferries

| Ferry | Operator | ≈ h | Book ahead | Day |
|---|---|--:|---|---|
| Hirtshals–Kristiansand | Fjord Line / Color Line | 2.75 | yes | D03 |
| Hjelmeland–Nesvik | Norled | 0.25 | walk-up usually fine | D04 |
| Vangsnes–Dragsvik | Fjord1 | 0.5 | walk-up usually fine | D05 |
| Eidsdal–Linge | Fjord1 | 0.25 | walk-up usually fine | D06 |
| Bodø–Moskenes | Torghatten Nord | 3.5 | **yes – critical in July** | D08 |
| Helsinki–Tallinn | Tallink Silja / Viking Line / Eckerö Line | 2.0 | yes | D16 |

Operators change – confirm timetables and operator names before booking.

## Tolls

- Ryfast tunnels (NO) – AutoPASS
- Norway: register bike + card with AutoPASS for ferries & tolls (Ferjepass / EPC); motorcycles are exempt from many road tolls – verify current rules
- Nibbevegen to Dalsnibba summit – private toll road
- Czech motorways: motorcycles are currently vignette-exempt; Germany & Polish A1/S-roads used here are toll-free for motorcycles – verify before travel.

## Fuel

Gaps measured along each day's track between OSM `amenity=fuel` stations within 1.5 km (Overpass), including day start → first station. Days with > 180 km between stations:

- none above the threshold (still fill up at every chance in Lapland, Finnmark and on Norwegian mountain roads).

Not checked (Overpass unavailable during the build): D01, D02, D03, D05, D06, D07, D08, D09, D10, D13, D14, D15 – re-run `python -m lwhroute fuel` then `build`.

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

1. Book the Bodø–Moskenes and Helsinki–Tallinn ferries as soon as the 2027 timetables open (Bodø–Moskenes is critical in late June / July).
2. Book a morning Hirtshals–Kristiansand ferry (Fjord Line ≈ 2¼ h or Color Line ≈ 3¼ h) once the 2027 timetable is out – day D03.
