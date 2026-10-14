# Decision log

Every decision that shaped the route and the website, newest last, with the reason and where it lives.
Day numbers are **trip days** (D01–D30 of the chosen Option B) unless marked *YAML id*. The two differ
from day 14 on, because the six Option B days (B14, B14b, B15–B18) replace YAML D14–D16; `out/summary.csv` maps them.
Since the Andøya/Senja day was added (2026-10-13), every trip day from D15 on is one higher than before; the
entries below use the current numbering.

**Resume a working session:** run `claude --resume` in `C:\Git` and pick the session from 2026-10-13
(id `43bbabb6-5bc8-43da-a998-a30629ba1286`), or start fresh in this folder. This file, `README.md` and
`data/route.yaml` hold everything needed to continue.

---

## 1. Your decisions

| Date | Decision | Effect |
|---|---|---|
| 2026-10-13 | Build the plan from `long-way-home-gpx-plan.md` | This repo |
| 2026-10-13 | **Start in the middle of June** | `meta.start_date: 2027-06-15` (year 2027 assumed – the next summer). Home on 13 Jul, 1 spare day |
| 2026-10-13 | **Option B – Nordkapp** | `meta.chosen_option: B`. Option A (Kiruna / Pajala) kept in `out/option_a/` for reference |
| 2026-10-13 | **Light gravel is fine** | TET splice built (`lwhroute/tet.py`, `gravel:` in route.yaml). Not active until you download the TET Finland GPX – see §4 |
| 2026-10-13 | **Skip the Curonian Spit** | Optional day and its Klaipėda ferries and toll removed |
| 2026-10-13 | **Strömma Farmlodge at 57.05708, 12.42522** | `override:` on D03/D04 |
| 2026-10-13 | **Raatteen Portti at 64.84834, 29.32720** | Coordinates on trip days 20/21 (YAML D17/D18) |
| 2026-10-13 | Fix the map | See §3 |
| 2026-10-13 | Nice itinerary web page | `out/index.html`, also a private claude.ai page |
| 2026-10-13 | Commit and push to a new GitHub repo | `ondrejkouril/lwh-route`, created private |
| 2026-10-13 | Deploy as GitHub Pages | Pages isn't available for private repos on the current plan. **You chose to make the repo public** (over a separate site-only repo). Site: <https://ondrejkouril.github.io/lwh-route/> |
| 2026-10-13 | Czech variant of the itinerary only; everything else stays English | `out/cs/index.html`, texts in `data/i18n_cs.yaml` |
| 2026-10-13 | Ferries table must not scroll sideways | Full width on desktop, stacked rows on phones |
| 2026-10-13 | Cross-check passes and curvy roads against other sources; LWH need not be followed 100 % | Review against Norway's 18 National Tourist Routes, Statens vegvesen and rider sources. Applied below |
| 2026-10-13 | **Split the 488 km Raate → Savonlinna day at Koli** | D21 Raatteen Portti → Koli (≈275 km), D22 Koli → Punkaharju ridge road → Olavinlinna → Rantasalmi → Linnansaari (≈285 km). Replaces the 488 km + 56 km pair; the pure Saimaa rest day is gone |
| 2026-10-13 | **Spend the spare day on Andøya and Senja** | D14 Svolvær → Andøya west coast → Andenes, D15 Andenes ⛴ Gryllefjord → Senja → Botnhamn ⛴ Brensholmen → Tromsø (replaces the 432 km E10/E6 day). Trip is now 30 riding days, home 14 Jul, no buffer |
| 2026-10-13 | **Stalheimskleiva is closed to vehicles** | D08 point is now a non-routed *Stalheim viewpoint* POI: closed since a 2020 collapse, upper part under restoration in 2026 (Statens vegvesen) |
| 2026-10-13 | **Shortcut home as a fallback buffer**: skip the Baltics if Scandinavia runs late. Asked for a Helsinki → Poland ferry; Hanko–Gdynia is freight only, and you didn't want to go back via Germany (Travemünde) | `shortcut:` in route.yaml, built to `out/shortcut/`: D24 Helsinki ⛴ Tallinn → Riga, D25 → Kaunas → Augustów, D26 → Warsaw (S8) → Piotrków Trybunalski, D27 → home. ≈1,560 km in 4 days instead of ≈2,040 km in 7: home 11 Jul, 3 days earlier. Chosen over the Sweden routes because it needs no fixed sailing |
| 2026-10-13 | **Add Borgund stave church** (the Wikipedia "Stave church" lead photo) and other sights along the way | Borgund is a routed out-and-back from Lærdal on D08 and `D08_alt` (+56 km; D08 now ≈339 km). 23 more sights are waypoints only (`route: false`, track unchanged), each ≤ 9 km from the route: stave churches Heddal, Røldal, Undredal, Kaupanger, Urnes (Solvorn ferry), Lom, Rødven, Kvernes; Varberg and Fredriksten fortresses, Vemork, Nidaros Cathedral, Nusfjord, Lofotr Viking Museum, Andenes whale safari, Alta rock art, Sápmi Park, Siida, Santa Claus Village, Kerimäki church, Tallinn Old Town, Rundāle Palace (shortcut), Jasna Góra |
| 2026-10-13 | **More Viking, military and maritime museums** (you prefer these to churches) | 26 waypoints (`route: false`, tracks unchanged), notes prefixed *Viking / Military / Maritime*. Viking: Ladby, Trelleborg, Roskilde Viking Ship Museum (D03), Museum of the Viking Age (Oslo, D05 – planned to reopen late 2027, likely still closed). Military: Akershus (Resistance + Armed Forces museums), Army Museum Trondheim, Aviation Museum Bodø, Lofoten War Memorial Museum, Tromsø Defence Museum, Tirpitz Museum, Muisti and Infantry Museum (Mikkeli), Suomenlinna, Latvian War Museum, Karosta, Kaunas War Museum, Warsaw Rising Museum. Maritime: Rostock ship museum, Maritiman, Fram Museum, Petroleum and Maritime museums (Stavanger), Mellemværftet, Fishing Village Museum Å, Polar Museum Tromsø, Seaplane Harbour Tallinn. The churches stay |
| 2026-10-13 | **Map: reset a selected day; itinerary: highlights and day descriptions** | A “Show whole trip” button appears on the map while a day is selected (also Esc, or clicking the selected day again). Each day card lists its waypoints under *Along the way* – click one to zoom the map to it and open its popup. Every day (and the alternatives and shortcut days) has a short `description:` in route.yaml: landscape and what to look out for, with Czech in i18n_cs.yaml. Alternatives are now labelled *Alternative* (not *Fallback if the ferry is not running*) |
| 2026-10-13 | **Tindevegen and Gamle Strynefjellsvegen as options** | `D08_alt` (Tindevegen toll road instead of the Fodnes ferry and Skjolden) and `D09_alt` (gravel Fv258 Grotli → Videseter, then Rv15 back to the Geiranger road) |
| 2026-10-13 | **Incorporate the TET Finland GPX** (your download, version 2026-09-23) | Private build only: `route --tet` / `build --tet` write git-ignored `data/routed_tet/` and `out_tet/`; the public `out/` and `data/routed/` stay road-only (TET forbids redistribution). Three sections, surfaces checked against OSM via BRouter way tags: **D18 Karigasniemi → Inari** (section 7, 116 km for 94 km of road, ≈89 km compacted gravel; D18 becomes 379 km and ≈7.5 h instead of 354 km and ≈5.8 h); **D20 Raate road** (section 8, the last ≈8 km into Raatteen Portti; the TET shares the main road before that; +3 km); **D21 Lentiira border forests** (section 4, 48 km for 34 km of road, ≈26 km unpaved; +16 km). Ivalo → Sodankylä dropped: the TET doesn't run there (section 7 goes Inari → Rovaniemi as one ≈380 km wilderness line). Partial legs use new `join`/`leave` points |
| 2026-10-14 | **A complete alternative in its own tab: home from Nordkapp through Sweden, ferry to Poland, ride home.** Of three options (inland mountains → Ystad ⛴ Świnoujście; coast + Stockholm → Nynäshamn ⛴ Gdańsk; hybrid → Karlskrona ⛴ Gdynia) you picked the first, but **a bit shorter, with Poland and Czechia on motorways**, keeping the **Międzyrzecz bunkers** | `variant:` in route.yaml, built into `out/sweden/` and linked as a second tab (*Home via Sweden*) on both itinerary pages and the map. Days 1–17 are shared (their GPX files stay in `out/days/`); D18–D29 are new: Nordkapp → Karasjok → Kautokeino, Karesuando → Kiruna (E45 Inland Road), Gällivare → Jokkmokk → Arvidsjaur, Silver Road → Arjeplog → Sorsele → Vilhelmina, **Vildmarksvägen** over Stekenjokk → Strömsund, Östersund → **Flatruet** → Funäsdalen, Sveg → Orsa → Mora, Malung → Klarälven → Karlstad (Sysslebäck dropped: the road from Malung meets the valley 33 km further south, so it would be ridden twice), Göta Canal → **Karlsborg Fortress** → Vättern → Jönköping, Växjö → **Ales stenar** → Ystad and the night ferry, Świnoujście → S3 → **Pniewo bunkers (MRU)** → Wrocław, A4/A1/D1 home. **29 riding days + 1 spare, home 13 July; D18–D29 ≈ 4,110 km (Finland & Baltics ending: ≈ 4,020 km in 13 days), whole trip ≈ 9,570 km.** Longest fuel gap 133 km (Vildmarksvägen). The Swedish south (Mora → Ystad) could lose another day if needed |
| 2026-10-14 | **Motorway days may be up to 750 km** | `validate`: 450 km on normal days, 750 km on `transit: true` days (was 550) |
| 2026-10-14 | **Optional TET Sweden, used on Mora → Ystad if that stretch is boring** | It partly is: the Klarälven (D25) and the Vättern shore (D26) are good, but D26 runs on the E18 and through farmland to Töreboda, and D27 is mostly straight Småland forest roads and Skåne farmland. With your TET Sweden GPX (version 2026-08-01, 27 sections, saved as `input/tet/swe.gpx`): the trail runs ≈ 10–20 km beside the towns, so whole-day scanning (an entry without `from`/`to` tries every leg – kept in `routing.py`) matched nothing; the sections were picked by hand from where the TET parallels the road. **Used:** D26 Kristinehamn → Töreboda through the Tiveden forests (S-02, 159 km for 79 km of road, ≈ 121 gravel) and Karlsborg → Hjo (S-02, 54 for 33, ≈ 30 gravel); D27 Hässleholm → Kåseberga over the Skåne ridges (S-23, 149 for 114, ≈ 90 gravel). D26 becomes 363 km and ≈ 7.6 h (from 263 km, 4.5 h), D27 419 km and ≈ 6.9 h (from 384 km, 5.4 h – still in time for the evening ferry). **Not used:** D25 (the Klarälven is good; the TET there is mostly connectors), D26 Karlstad → Kristinehamn (99 km for 43), D27 Jönköping → Växjö (S-01, 206 for 135 – with S-23 the ferry day would be ≈ 490 km and 9 h). Private build only (`out_tet/sweden/`) |
| 2026-10-14 | **More sights in Sweden** (asked whether there were any) | 12 more waypoints (`route: false`), each checked with Nominatim and measured from the track: Kiruna Church (moved in 2025), Dundret, Lappstaden (Arvidsjaur), Fatmomakke, Jamtli (Viking-age Överhogdal tapestries), Vasaloppets Hus, Värmlands museum, Picasso sculpture (Kristinehamn), Bofors Industrimuseum (military, ≈ 22 km off), Forsvik lock (maritime), Utvandrarnas hus, Kronoberg Castle ruin. Already there: Sápmi Park, Icehotel, Ájtte, Silvermuseet, Hällingsåfallet, Zorn Museum, Nusnäs, Karlsborg Fortress, Ales stenar, Glimmingehus |
| 2026-10-14 | **TET gravel downloadable from the page, via a private repo loaded as a submodule** | A private submodule alone can't make it downloadable on the public Pages site without publishing it (TET forbids redistribution). So: private repo [ondrejkouril/lwh-route-tet](https://github.com/ondrejkouril/lwh-route-tet) as submodule `private/` with the TET GPX (`tet/`) and the gravel day files (`days/`, `sweden/days/`, copied there by `build --tet`); the itinerary shows **TET gravel version (private)** next to *Download GPX* on D18, D20, D21 and Sweden D26, D27, linking to the file in the private repo – it downloads only when signed in to GitHub with access, 404 for everyone else. The Pages workflow checks out without submodules |

## 2. Route decisions made while building (not in the original plan)

| Where | Decision | Why |
|---|---|---|
| D09 | **Added the Åfarnes–Sølsnes ferry** (Fjord1, ~20 min); dropped Molde | There's no fixed link: by land Åndalsnes → Atlantic Road is ~190 km and the day would be ~415 km |
| D10 | **Overland via Sunndalsøra (Rv70) and Oppdal (E6)** | Avoids the E39 Halsa–Kanestraum ferry |
| D11 | Shaping point Trofors on the E6 | Keeps the router off the ferry-laden coastal Fv17 |
| D07 | Added **Fv520 Saudafjellet** (Sauda–Røldal, ~960 m) to the seasonal roads | The plan's route crosses it; it closes in winter |
| D03 | Storebælt and Øresund bridges are toll waypoints, not route points | Shaping points on the dual carriageways caused U-turns; they are the only fixed links anyway |
| D03, D04 | Odense and Halden via points moved onto the through-route | Town centres caused drive-in-and-back U-turns |
| several | Other town vias moved slightly onto the through-route (`bypass` step) | Same U-turn problem; every move has an `override:` reason |
| several | Short side trips marked `spur:` (Little Mermaid, Båstad, Smögen, Dalsnibba, Saltstraumen, Henningsvær, Narvik, Koli, Kihnu points, Rusnė, Kaunas, Augustów, Puumala) | Out-and-back stops; exempt from the U-turn and on-track checks |
| D22/D23 | Linnansaari boat from **Rantasalmi (Porosalmi)** instead of Oravi | Closer to the next day's Puumala ridge road |
| D23 | Added Sulkava and Puumala (Rd 62) | Rd 62 Saimaa ridge road on the way to Helsinki |
| D28 | Added Rusnė (Nemunas delta) as an optional spur | Scenic detour on the Nemunas road |
| D29 | Overnight **Nadarzyn** (S8, south-west of Warsaw) instead of Mszczonów | Keeps D29 and D30 both under 550 km and avoids Warsaw traffic |
| D01, D29, D30 | Removed shaping points Prague, Łomża and Piotrków | Caused detours; the motorway is the natural line |
| D14, D15 | New ferries **Andenes–Gryllefjord** (summer only, ≈1 h 40) and **Botnhamn–Brensholmen** (all year, ≈45 min) | Only way to link Andøya, Senja and Tromsø without a ≈555 km day via Finnsnes |
| D09_alt | Four shaping points along Fv258 | BRouter's car profile avoids the unpaved road and otherwise doubles back on Rv15 |
| Sweden D23 | Four shaping points over Flatruet; three on Z 795 / E45 south of Strömsund | BRouter's car profile otherwise detoured ≈ 240 km round Flatruet and ≈ 80 km round a short unpaved link south of Strömsund (OSRM takes both directly) |
| Sweden D27/D28 | The night ferry belongs to D27 (overnight = cabin, marker at Świnoujście); D28 starts at the Świnoujście terminal | Ystad–Świnoujście night sailings leave ≈ 22:00–23:00 and arrive ≈ 06:00–07:00 (Polferries, Unity Line) |
| Sweden D28 | Overnight at Bielany Wrocławskie (A4/A8), not Międzyrzecz | Splits the ≈ 870 km from the ferry home into ≈ 480 + 390 km and leaves time for the 1.5–2.5 h bunker tour; staying at Międzyrzecz would make the last day ≈ 620 km (allowed under the 750 km rule) |
| Sweden | Coordinates fixed from Nominatim: Kiruna (new town centre), Ljungdalen (13.5 km off), Hällingsåfallet, Pniewo museum entrance, Karlsborg fortress museum | `override:` with reasons |
| D22 | Punkaharju ridge road (Harjutie) via shaping points at both ends; Olavinlinna before Savonlinna | Arriving from the east, the castle comes first |
| D03 | Added Mellbystrand shaping point | Coast road along Laholmsbukten |
| Plan coordinates | Hvedholm (4.1 km off), Kiruna (3.4 km), Panemunė Castle (5.4 km) corrected | Only 3 of the plan's points were > 3 km off – under the "> 5 flagged → stop and ask" rule, so fixed via `override:` |
| Norway | Road refs accept old and new numbers (`500\|4224\|Lysevegen`, `243\|5627\|Bjørgavegen`) | 2020 county-road renumbering: OSM uses the new numbers |

### Considered in the 2026-10-13 road review and not added

| Road | Why not |
|---|---|
| Kystriksveien Fv17 (instead of E6 on D11) | ≈430 km with six ferries, at least 2 days; the spare day went to Andøya/Senja |
| Havøysund National Tourist Route (Fv889, D17) | 83 km each way off the E69; D17 would be ≈435 km. Ride it only on a perfect-weather day |
| Rovaniemi → Posio → Kuusamo → Rd 5 (D20) | 354 km vs 333 km; no rider source rates Rd 81, so not worth the change |
| Old road over Røldalsfjellet (D07) | Open roughly July–October in an average year, so likely still closed on 21 June |
| Senja without the Andenes ferry (via Finnsnes) | ≈555 km in one day |
| Shortcut via Sweden: Helsinki ⛴ Stockholm, then Karlskrona ⛴ Gdynia (Stena) or Nynäshamn ⛴ Gdańsk | Same 3 days saved as the Via Baltica shortcut, but two overnight sailings at fixed times with cabins to book |
| Shortcut via Helsinki ⛴ Travemünde (Finnlines, ≈30 h, daily) | 4 days saved, but you didn't want to go back through Germany |
| Hanko ⛴ Gdynia (Finnlines) | Freight ro-ro line, no regular private bookings |

### Accepted warnings (reported, not changed)

- D03 Faaborg → Tvååker **466 km** is over the 450 km daily limit (the 488 km Raate → Savonlinna day was split at Koli).
- D23 Rantasalmi → Helsinki is 21 % over target (401 km, fast roads).
- No fuel gap over 180 km; the longest is D17 Alta → Nordkapp (158 km), then D14 Svolvær → Andenes (110 km).
- Riding hours: BRouter's stock car profile times unpaved roads at 2 km/h; `routing.py` re-times unpaved segments at
  the TET planning speed (45 km/h). This only changes hours (D05, D06, D06_alt, D09_alt), never the route.

## 3. Technical decisions

| Topic | Decision | Why |
|---|---|---|
| Python | `uv` with Python 3.12 (installed via winget) | No Python on the PC |
| Router | BRouter with a custom **car-fast-noferry** profile (`profiles/`), OSRM as fallback | Stock car-fast picked ferries; the plan forbids router-chosen ferries. Every ferry is explicit in route.yaml |
| Ferries | Days split at ferry points; each crossing is its own named 2-point track; `<rte>` split the same way | Kurviger/Chigee never have to bridge water |
| Road checks | OSRM snap + road ref instead of Overpass | Overpass was too overloaded; it's kept only for the fuel check (with mirrors, caching, chunking) |
| Riding hours | Router time × 1.10 | Loaded bike; stops and ferries excluded |
| Day numbering | Output files numbered by trip day (`Day.label`) | Option B shifts days; the rider needs D01…D29 in order |
| Map tiles | OpenStreetMap tiles (inverted in dark mode) over an **offline Natural Earth basemap** (`data/basemap.json`) | CARTO tiles now need an API key; the offline basemap keeps geography visible where tiles are blocked (e.g. claude.ai pages) |
| Midnight sun | Badge only when the sun's centre stays above the horizon at the overnight stop | Conservative: Mo i Rana (south of the Arctic Circle) isn't promised it |
| Website | Static pages in `out/`, deployed by `.github/workflows/pages.yml` | Build locally, push, Pages republishes |
| claude.ai page | Copy of the English itinerary with Leaflet CSS inlined; GPX links open on the Pages site | That viewer only allows Google Fonts stylesheets and blocks downloads |
| Translations | `data/i18n_cs.yaml` maps exact English text → Czech; missing text stays English | Route data stays single-language in route.yaml |

## 4. Open items

1. **Book ferries** as soon as the 2027 timetables open: Bodø–Moskenes (D12, 26 Jun – critical), Andenes–Gryllefjord
   (D15, 29 Jun – summer only, 2–3 sailings a day, new operating contract from 16 May 2027) and Helsinki–Tallinn (D24).
2. **Lysefjord car ferry** (D06, 20 Jun): check the summer timetable; if it isn't running, ride `D06_alt.gpx`.
   **Gamle Strynefjellsvegen** (D09, 23 Jun): ride `D09_alt.gpx` only if Fv258 is already open.
3. **TET gravel** lives in the private submodule `private/` (TET GPX in `private/tet/`). After `route --tet` + `build --tet`,
   commit and push `private/` (its `days/` and `sweden/days/` hold the gravel day files), then commit the submodule pointer
   here and rebuild the public site so the private links appear. On the phone: open the itinerary while signed in to GitHub
   and use *TET gravel version (private)*. The TET GPX is updated often: re-download it shortly before the trip and rebuild.
   Never push or publish `out_tet/`.
4. *Likely* (not confirmed) Long Way Home locations: Hiljainen kansa, Sigulda bobsleigh track, Linnansaari, Palanga, the Raate road, Pajala forest camp (Option A).
5. Re-check seasonal road openings on vegvesen.no shortly before departure.
6. **No buffer day left.** If weather costs a day, drop the Kihnu island day (D25) or ride Svolvær → Tromsø in one day
   (skip the Andøya/Senja split). If it costs more, take the **shortcut home** from Helsinki (`out/shortcut/`, 3 days
   gained) – decide in Helsinki; only the Tallinn ferry (many sailings a day) is needed.
7. **Home via Sweden** (if chosen): book the Ystad–Świnoujście night ferry with a cabin (D27) and check the Pniewo bunker
   tour times (D28); Vildmarksvägen over Stekenjokk (D22) usually opens in early June – check trafikverket.se.
   It has one spare day.

## 5. Publishing notes

- Repo: <https://github.com/ondrejkouril/lwh-route> (public since 2026-10-13). The site shows the home town and the travel dates.
- Site: <https://ondrejkouril.github.io/lwh-route/> · [česky](https://ondrejkouril.github.io/lwh-route/cs/) · [map](https://ondrejkouril.github.io/lwh-route/map.html)
- Private claude.ai copy: <https://claude.ai/artifact/EK2aGnsiYShvWYbgQwfxM8> (rebuilt from `data/cache/artifact_itinerary.html`).
- Pushing from this PC: `env -u GH_TOKEN git push` (the `GH_TOKEN` environment variable holds an invalid token; Git Credential Manager works).
