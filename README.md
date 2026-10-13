# lwh-route

GPX build for a 30-day solo motorcycle trip (BMW R 1300 GS) from Kobylnice (CZ) following *Long Way Home*
(2025) through Denmark, Scandinavia and the Baltics, then home via Poland.

**Chosen route: Option B (Nordkapp, Andøya and Senja)** – departure 15 June 2027, 30 riding days (no spare day), ≈ 9,430 km.
**Website:** <https://ondrejkouril.github.io/lwh-route/> (itinerary) ·
[česky](https://ondrejkouril.github.io/lwh-route/cs/) ·
[full-screen map](https://ondrejkouril.github.io/lwh-route/map.html). GPX files download from the day entries.

The site is `out/`, deployed by `.github/workflows/pages.yml` on every push to `main` that changes `out/`.
Czech texts come from `data/i18n_cs.yaml` (exact English → Czech pairs; anything missing stays English).

`data/route.yaml` is the single source of truth. Everything in `out/` is generated.
Every route and publishing decision, with its reason, is logged in [`DECISIONS.md`](DECISIONS.md).

## Run

```sh
uv run python -m lwhroute geocode    # verify points: Nominatim (places) + OSRM snap/ref (shaping points on named roads)
uv run python -m lwhroute snap       # write road-snap suggestions from the last geocode run as `override:` entries
uv run python -m lwhroute route      # BRouter (no-ferry car-fast) per leg, days split at ferries; OSRM fallback
uv run python -m lwhroute bypass     # move town-centre vias that cause U-turns onto the through-route
uv run python -m lwhroute fuel       # Overpass amenity=fuel along each track -> data/fuel.json
uv run python -m lwhroute basemap    # one-off: Natural Earth land/lakes -> data/basemap.json (offline map background)
uv run python -m lwhroute build      # GPX, summary.md/.csv, index.html + map.html (+ out/option_a/)
uv run python -m lwhroute validate   # §3 gates -> out/validation.md (exit 1 on hard failures)
uv run python -m lwhroute all        # geocode, route, fuel, build, validate; stops if > 5 points flagged (--force)
uv run python -m lwhroute.diag D09   # per-leg km vs straight line, to spot detours
```

Coordinates are never silently changed: fixes go into `override: {lat, lon, reason}` on the point.
Network responses are cached (`data/geocode_cache.json`, `data/cache/`), so re-runs are offline
unless points change.

## How the routing avoids water routing

* Every day is split at `ferry_start`/`ferry_end`; a crossing is a straight 2-point track `FERRY: <route>`.
* The `<rte>` is split the same way (one route per land part), so Kurviger/Chigee never bridge water themselves.
* BRouter runs `profiles/car-fast-noferry.brf` – stock `car-fast` with `route=ferry` impassable – so the
  router *cannot* pick a ferry. The BRouter GeoJSON `WayTags` are still checked for `route=ferry`.
* Shaping points on named roads are verified by snapping with OSRM and reading the road `ref`.
  Note the 2020 Norwegian county-road renumbering: OSM tags Fv500 Lysevegen as **Fv4224** and
  Fv243 Aurlandsfjellet as **Fv5627 (Bjørgavegen)**; `road:` accepts `old|new|name`.

`meta.chosen_option` (A/B) and `meta.start_date` in `route.yaml` decide which trip lands in `out/` and the dates.
Each day's `description:` (landscape, what to look out for) shows on the itinerary page; its POIs (`type: poi`)
are listed there under *Along the way* and open on the map when clicked.
`shortcut:` in `route.yaml` is an alternative ending of the chosen trip: it replaces every day from
`replaces_from` (a YAML id) on; its day offsets count from that day.
Day files are numbered by trip day (D01…D30); `summary.csv` maps each to its `yaml_id`
(e.g. trip day D20 = YAML `D17`, because the six Option B days B14, B14b, B15–B18 replace D14–D16).

## Optional TET gravel

`gravel:` in `route.yaml` lists Trans Euro Trail sections that can replace a road leg (Raate road, Raate → Kuhmo,
Ivalo → Sodankylä). The TET terms forbid automated download and redistribution, so the file is not in this repo:
download the Finland GPX from <https://transeurotrail.org/finland/>, save it as `input/tet/fin.gpx` (git-ignored),
then run `route` and `build`. A section is applied only if the TET passes within 8 km of both ends and is at most
`max_detour` × the road distance; the day's `<rte>` then gets shaping points along the gravel.
**This repo and its website are public: never commit or push `out/` built with TET data** (the build prints a warning when it is).

## Outputs

| File | Use |
|---|---|
| `out/days/DXX_<from>-<to>.gpx` | per day: `<rte>` (via + shaping, split at ferries) for Kurviger/Chigee, BRouter `<trk>`, `<wpt>` POIs/ferries/overnight |
| `out/days/D06_alt.gpx` | Lysefjord-ferry fallback (ride Lysevegen down and back, Fv45 to Stavanger) |
| `out/days/D08_alt.gpx` | D08 via the Tindevegen toll road (Øvre Årdal → Turtagrø) instead of the Fodnes ferry and Skjolden |
| `out/days/D09_alt.gpx` | D09 with the gravel Gamle Strynefjellsvegen (Fv258) – only if it is open |
| `out/lwh_master_routes.gpx` | all day routes (rte only) |
| `out/lwh_master_track.gpx` | all tracks; each ferry crossing is a separate named 2-point track |
| `out/pois.gpx` | waypoints only |
| `out/summary.md`, `out/summary.csv` | per-day km, hours, ferries, tolls, seasonal roads, overnight, LWH stops, fuel gaps |
| `out/index.html`, `out/cs/index.html` | itinerary page (English / Czech): dates, latitude profile, map, day-by-day road book, ferries/tolls/camping |
| `out/map.html` | full-screen map with a day list (offline Natural Earth basemap + OpenStreetMap tiles) |
| `out/validation.md` | validation report |
| `out/option_a/` | the route not taken: Swedish Lapland via Kiruna/Pajala (D14–D16 day files + masters, summary) |
| `out/shortcut/` | alternative ending if Scandinavia runs late: from Helsinki straight home on the Via Baltica (4 day files from D24, masters, full-trip summary); shown on the itinerary page as a callout before D24 |

The BRouter track is for distance/time and a visual check only; **final curvy routing is done in Kurviger**.
`<trk>` points are densified to ≤ 500 m spacing (long straight router edges on bridges/tunnels).

Map data © OpenStreetMap contributors (ODbL); basemap from Natural Earth (public domain).
