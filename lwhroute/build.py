"""Step 4: GPX outputs and summaries for the chosen option (out/) and the other option (out/option_a|b/).
Map and itinerary pages are written by pages.py."""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

import gpxpy.gpx as G

from . import fuel
from .common import OUT, Day, Point, Route, haversine_km, load_route

from .routing import day_parts, load_routed

HOURS_FACTOR = 1.10          # BRouter car-fast drive time + 10 % for a loaded bike
MAX_RTE_POINTS = 60
DENSIFY_KM = 0.5           # max spacing of <trk> points (long router edges are interpolated)
CREATOR = "lwh-route (BRouter car-fast track; final curvy routing in Kurviger)"

SYM = {"via": "Flag, Blue", "shape": "Pin, Blue", "poi": "Scenic Area", "overnight": "Lodging",
       "ferry_start": "Anchor", "ferry_end": "Anchor"}
SYM_OVERNIGHT = {"wild camp": "Campground", "campsite cabin": "Campground", "hotel": "Lodging", "home": "Residence"}


# ------------------------------------------------------------------ per-day data
def day_stats(route: Route, day: Day) -> dict:
    r = load_routed(day.id)
    land = [p for p in r["parts"] if p["kind"] == "land"]
    km = sum(l["length_km"] for p in land for l in p["legs"])
    secs = sum(l["time_s"] for p in land for l in p["legs"])
    ferries = [p["ferry"] for p in r["parts"] if p["kind"] == "ferry"]
    ferry_h = sum(route.ferries.get(f, {}).get("duration_h", 0) for f in ferries)
    engines = sorted({l["engine"] for p in land for l in p["legs"]})
    gravel_km = sum(l.get("gravel_km", 0) for p in land for l in p["legs"])
    return {"km": km, "drive_h": secs / 3600 * HOURS_FACTOR, "ferries": ferries, "ferry_h": ferry_h,
            "engines": engines, "gravel_km": gravel_km, "routed": r}


def wpt(p: Point, day: Day) -> G.GPXWaypoint:
    w = G.GPXWaypoint(latitude=p.lat, longitude=p.lon, name=p.name)
    tags = []
    if p.lwh:
        tags.append(f"LWH ({p.lwh_conf or 'confirmed'})")
    if p.spur:
        tags.append(f"spur: {p.spur}")
    w.description = " · ".join(filter(None, [day.label, *tags, p.notes]))
    w.type = p.type
    w.symbol = SYM_OVERNIGHT.get(day.overnight_type, "Lodging") if p.type == "overnight" else SYM.get(p.type)
    return w


def day_waypoints(day: Day) -> list[Point]:
    """POIs, ferry terminals, the overnight stop and any unrouted points."""
    keep = []
    for i, p in enumerate(day.points):
        if p.type in ("poi", "ferry_start", "ferry_end", "overnight") or not p.route:
            keep.append(p)
    return keep


def rtes_for_day(day: Day, routed: dict | None = None) -> list[G.GPXRoute]:
    """One <rte> per land part, so Kurviger/Chigee never have to bridge water themselves.
    Legs replaced by TET gravel get shaping points along the gravel so the route app follows it."""
    rtes = []
    land_parts = [p for p in day_parts(day.points) if p["kind"] == "land"]
    routed_land = [p for p in (routed or {}).get("parts", []) if p["kind"] == "land"]
    for n, part in enumerate(land_parts, 1):
        pts = part["points"]
        legs = routed_land[n - 1]["legs"] if n - 1 < len(routed_land) else []
        suffix = f" ({n}/{len(land_parts)})" if len(land_parts) > 1 else ""
        rte = G.GPXRoute(name=f"{day.label} {pts[0].name} → {pts[-1].name}{suffix}")
        rte.description = day.title
        for k, p in enumerate(pts):
            rp = G.GPXRoutePoint(latitude=p.lat, longitude=p.lon, name=p.name)
            rp.type = "shape" if p.type == "shape" else "via"
            rp.symbol = SYM.get(p.type)
            rp.comment = p.type
            rte.points.append(rp)
            leg = legs[k] if k < len(legs) else {}
            for m, (la, lo) in enumerate(leg.get("shaping", []), 1):
                sp = G.GPXRoutePoint(latitude=la, longitude=lo, name=f"TET {m}")
                sp.type, sp.symbol, sp.comment = "shape", SYM["shape"], "shape (TET gravel)"
                rte.points.append(sp)
        if len(rte.points) > MAX_RTE_POINTS:
            raise ValueError(f"{day.id} part {n}: {len(rte.points)} route points > {MAX_RTE_POINTS}")
        rtes.append(rte)
    return rtes


def tracks_for_day(route: Route, day: Day, routed: dict) -> list[G.GPXTrack]:
    """Land parts as tracks (one segment each); every ferry crossing as its own named 2-point track."""
    trks = []
    for part in routed["parts"]:
        if part["kind"] == "ferry":
            label = route.ferries.get(part["ferry"], {}).get("label", part["ferry"])
            t = G.GPXTrack(name=f"FERRY: {label}")
            t.type = "ferry"
            seg = G.GPXTrackSegment()
            for la, lo, _ in part["coords"]:
                seg.points.append(G.GPXTrackPoint(la, lo))
            t.segments.append(seg)
        else:
            t = G.GPXTrack(name=f"{day.label} {part['from']} → {part['to']}")
            gravel = [l["gravel_label"] for l in part["legs"] if l.get("gravel_km")]
            if gravel:
                t.description = "Includes TET gravel: " + "; ".join(gravel)
            t.type = "motorcycle"
            seg = G.GPXTrackSegment()
            last = None
            for leg in part["legs"]:
                for la, lo, ele in leg["coords"]:
                    if last == (la, lo):
                        continue
                    if last is not None:   # densify long straight edges (bridges, tunnels) for devices
                        d = haversine_km(last[0], last[1], la, lo)
                        n = int(d // DENSIFY_KM)
                        for k in range(1, n + 1):
                            f = k / (n + 1)
                            seg.points.append(G.GPXTrackPoint(last[0] + (la - last[0]) * f, last[1] + (lo - last[1]) * f))
                    seg.points.append(G.GPXTrackPoint(la, lo, elevation=ele))
                    last = (la, lo)
            t.segments.append(seg)
        trks.append(t)
    return trks


def new_gpx(name: str, desc: str = "") -> G.GPX:
    g = G.GPX()
    g.creator = CREATOR
    g.name = name
    g.description = desc
    return g


def write_gpx(g: G.GPX, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(g.to_xml(version="1.1"), encoding="utf-8")


def build_day_gpx(route: Route, day: Day, st: dict, out_dir: Path):
    g = new_gpx(f"{day.label} {day.title}", f"{st['km']:.0f} km road, ≈{st['drive_h']:.1f} h riding. {day.notes}".strip())
    g.routes.extend(rtes_for_day(day, st["routed"]))
    g.tracks.extend(tracks_for_day(route, day, st["routed"]))
    g.waypoints.extend(wpt(p, day) for p in day_waypoints(day))
    write_gpx(g, out_dir / day.filename)


def build_masters(route: Route, days: list[Day], stats: dict, out_dir: Path, title: str):
    mr = new_gpx(f"{title} – routes", "All day routes (rte only) for Kurviger / Chigee import.")
    mt = new_gpx(f"{title} – tracks", "BRouter tracks; each ferry crossing is a separate named 2-point track.")
    pois = new_gpx(f"{title} – POIs", "POIs, ferry terminals and overnight stops.")
    seen = set()
    for d in days:
        mr.routes.extend(rtes_for_day(d, stats[d.id]["routed"]))
        mt.tracks.extend(tracks_for_day(route, d, stats[d.id]["routed"]))
        for p in day_waypoints(d):
            if p.key not in seen:
                seen.add(p.key)
                pois.waypoints.append(wpt(p, d))
    write_gpx(mr, out_dir / "lwh_master_routes.gpx")
    write_gpx(mt, out_dir / "lwh_master_track.gpx")
    write_gpx(pois, out_dir / "pois.gpx")


# ------------------------------------------------------------------ summary
def lwh_stops(day: Day) -> list[str]:
    out, seen = [], set()
    for p in day.points:
        if p.lwh and p.name not in seen:
            seen.add(p.name)
            out.append(p.name + ("*" if p.lwh_conf == "likely" else ""))
    return out


def _round_or_none(x):
    return None if x is None or x != x else round(x)


def trip_date(route: Route, d: Day) -> dt.date | None:
    start = route.meta.get("start_date")
    return start + dt.timedelta(days=d.offset) if isinstance(start, dt.date) else None


def summary_rows(route: Route, days: list[Day], stats: dict, fuel_gaps: dict) -> list[dict]:
    rows = []
    for d in days:
        st = stats[d.id]
        date = trip_date(route, d)
        rows.append({
            "day": d.label, "yaml_id": d.id, "date": date.isoformat() if date and not d.is_alt else "",
            "offset": d.offset, "title": d.title,
            "km": round(st["km"]), "target_km": round(d.target_km),
            "riding_h": round(st["drive_h"], 1),
            "ferries": "; ".join(route.ferries.get(f, {}).get("label", f) for f in st["ferries"]),
            "ferry_h": round(st["ferry_h"], 1),
            "tolls": "; ".join(d.tolls),
            "seasonal_roads": "; ".join(route.seasonal_roads.get(s, {}).get("label", s) for s in d.seasonal),
            "overnight": (d.overnight.name if d.overnight else ""),
            "overnight_type": d.overnight_type,
            "lwh_stops": "; ".join(lwh_stops(d)),
            "max_fuel_gap_km": _round_or_none(fuel_gaps.get(d.id, {}).get("max_gap_km")),
            "gravel_km": round(st["gravel_km"]),
            "router": "/".join(st["engines"]),
            "gpx": d.filename,
        })
    return rows


def write_csv(rows: list[dict], path: Path):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


WILD_CAMPING = [
    ("Norway", "Allemannsretten: up to 2 nights in one spot on uncultivated land, ≥150 m from houses/cabins; fire ban 15 Apr–15 Sep near forest."),
    ("Sweden", "Allemansrätten: 1–2 nights, out of sight of houses, not on farmland; respect local fire bans."),
    ("Finland", "Jokamiehenoikeus: short-term camping allowed away from homes; no open fire without landowner permission; NP campsites in Linnansaari."),
    ("Estonia", "Use free RMK campsites/forest huts (rmk.ee); otherwise landowner permission needed."),
    ("Latvia", "Generally tolerated on public land away from houses; campsites recommended near Riga/Gauja NP."),
    ("Lithuania", "Only at designated campsites/rest areas; wild camping in parks is fined."),
    ("Denmark", "No wild camping – use campsites or free shelters (shelter.dk / udinaturen.dk)."),
    ("Germany", "No wild camping – campsites only."),
    ("Poland", "Only on designated forest areas ('Zanocuj w lesie' programme) or campsites."),
]


def open_questions(route: Route, days: list[Day]) -> list[str]:
    q = ["Book the Bodø–Moskenes and Helsinki–Tallinn ferries as soon as the 2027 timetables open "
         "(Bodø–Moskenes is critical in late June / July).",
         "Check the Lysefjord car-ferry summer timetable for the D06 date; ride `D06_alt.gpx` if it is not running.",
         "Hiljainen kansa, Sigulda bobsleigh track, Linnansaari, Palanga and the Raate road are *likely* LWH "
         "locations (region match, not confirmed on screen)."]
    fd = ferry_days(days)
    if "andenes-gryllefjord" in fd:
        q.insert(1, "Book the Andenes–Gryllefjord ferry as soon as the 2027 timetable is out (summer only, 2–3 sailings "
                    "a day; new operating contract from 16 May 2027) – day " + ", ".join(fd["andenes-gryllefjord"]) + ".")
    label = {d.id: d.label for d in days}
    gravel = [g for g in route.gravel if g["day"] in label]
    if gravel:
        q.append("TET gravel: download the TET Finland GPX (`fin.gpx`) from transeurotrail.org into `input/tet/` and "
                 "re-run `route` + `build` – candidate sections: "
                 + "; ".join(f"{label[g['day']]} {g['from']} → {g['to']}" for g in gravel) + ".")
    return q


def write_summary_md(route: Route, days: list[Day], rows: list[dict], fuel_gaps: dict, path: Path,
                     title: str, variant_note: str, alt_rows: list[dict], buffer_days: int):
    total = sum(r["km"] for r in rows)
    hours = sum(r["riding_h"] for r in rows)
    first, last = rows[0]["date"], rows[-1]["date"]
    when = f" · {first} → {last}" if first else ""
    L = [f"# {title}", "", variant_note, "",
         f"**{len(rows)} riding days{when} · {total:,.0f} km road · ≈{hours:.0f} h riding** (excl. ferries)", "",
         "Distances and times come from a BRouter `car-fast` track (OSRM fallback where noted). "
         f"Riding hours = router drive time × {HOURS_FACTOR:.2f}, excluding stops and ferries. "
         "**Final curvy routing happens in Kurviger** – import the `<rte>` (via + shaping points) and let Kurviger "
         "compute the motorcycle route; the BRouter `<trk>` is only for distance/time and a visual check.", "",
         "## ⚠ Season dependency", "",
         "This route is only viable **mid-June to mid-August**. These roads/ferries are seasonal – "
         "**verify opening status on vegvesen.no (and the ferry operators) before departure**:", ""]
    used = {s for d in days for s in d.seasonal}
    for key, sr in route.seasonal_roads.items():
        if key in used:
            on = ", ".join(d.label for d in days if key in d.seasonal)
            L.append(f"- **{sr['label']}** ({on}) – {sr['typical']}; verify on {sr.get('verify', 'vegvesen.no')}")
    L += ["", "If the Lysefjord ferry is not running, ride `D06_alt.gpx` instead.", "",
          "## Day table", "",
          "| Day | Date | Route | km | target | h | Ferries | Tolls | Seasonal | Overnight (type) | LWH stops | Max fuel gap |",
          "|---|---|---|--:|--:|--:|---|---|---|---|---|--:|"]
    for r in rows:
        fg = r["max_fuel_gap_km"]
        fg_s = "n/a" if fg is None else (f"**{fg}**" if fg > fuel.MAX_GAP_KM else str(fg))
        gr = f" (incl. {r['gravel_km']} km TET gravel)" if r["gravel_km"] else ""
        L.append(f"| {r['day']} | {r['date']} | {r['title']}{gr} | {r['km']} | {r['target_km']} | {r['riding_h']} "
                 f"| {r['ferries'] or '–'} | {r['tolls'] or '–'} | {r['seasonal_roads'] or '–'} "
                 f"| {r['overnight']} ({r['overnight_type']}) | {r['lwh_stops'] or '–'} | {fg_s} |")
    L += ["", "`*` = likely LWH location (strong match, not confirmed on screen). "
              "Day numbers are trip days; the `yaml_id` column in summary.csv maps them to `data/route.yaml`."]
    if alt_rows:
        L += ["", "### Alternatives (not in totals)", "",
              "| File | Route | km | h | Ferries |", "|---|---|--:|--:|---|"]
        for r in alt_rows:
            L.append(f"| {r['day']} | {r['title']} | {r['km']} | {r['riding_h']} | {r['ferries'] or '–'} |")
    buffer_text = (f"{buffer_days} unassigned weather/rest day(s). "
                   "Most valuable around D06–D09 (seasonal Norwegian roads), D12 (Bodø–Moskenes ferry) and the "
                   "Helsinki–Tallinn ferry day." if buffer_days else
                   "None – every day of the trip is a riding day. If weather costs a day, the easiest days to give up "
                   "are the Kihnu island day or the Andøya/Senja split (ride Svolvær → Tromsø on the E10/E6 in one day).")
    L += ["", "## Buffer days", "", buffer_text,
          "", "## Ferries", "", "| Ferry | Operator | ≈ h | Book ahead | Day |", "|---|---|--:|---|---|"]
    for key, fd in ferry_days(days).items():
        f = route.ferries[key]
        L.append(f"| {f['label']} | {f['operator']} | {f['duration_h']} | {booking(f)} | {', '.join(fd)} |")
    L += ["", "Operators change – confirm timetables and operator names before booking.", "",
          "## Tolls", ""]
    used_t = {t for d in days for t in d.tolls}
    for key, txt in route.tolls.items():
        if key in used_t or key == "autopass":
            L.append(f"- {txt}")
    L += [f"- {CZ_PL_DE_TOLLS}", "", "## Fuel", "",
          f"Gaps measured along each day's track between OSM `amenity=fuel` stations within {fuel.CORRIDOR_KM} km "
          f"(Overpass), including day start → first station. Days with > {fuel.MAX_GAP_KM} km between stations:", ""]
    flagged = [(d.label, fuel_gaps[d.id]) for d in days if (fuel_gaps[d.id].get("max_gap_km") or 0) > fuel.MAX_GAP_KM]
    if flagged:
        for d, g in flagged:
            L.append(f"- **{d}**: {g['max_gap_km']:.0f} km gap ({g['gap_from']} → {g['gap_to']}) – fill up before.")
    else:
        L.append("- none above the threshold (still fill up at every chance in Lapland, Finnmark and on "
                 "Norwegian mountain roads).")
    missing = [d.label for d in days if fuel_gaps[d.id].get("max_gap_km") is None
               or fuel_gaps[d.id]["max_gap_km"] != fuel_gaps[d.id]["max_gap_km"]]
    if missing:
        L += ["", f"Not checked (Overpass unavailable during the build): {', '.join(missing)} – "
                  "re-run `python -m lwhroute fuel` then `build`."]
    L += ["", "## Wild camping rules", ""]
    L += [f"- **{c}**: {t}" for c, t in WILD_CAMPING]
    L += ["", "## Open items", ""] + [f"{i}. {q}" for i, q in enumerate(open_questions(route, days), 1)] + [""]
    path.write_text("\n".join(L), encoding="utf-8")


CZ_PL_DE_TOLLS = ("Czech motorways: motorcycles are currently vignette-exempt; Germany & Polish A1/S-roads used here "
                  "are toll-free for motorcycles – verify before travel.")


def booking(f: dict) -> str:
    return "**yes – critical in July**" if f.get("critical") else ("yes" if f.get("book") else "walk-up usually fine")


def ferry_days(days: list[Day]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for d in days:
        for p in day_parts(d.points):
            if p["kind"] == "ferry":
                out.setdefault(p["ferry"], []).append(d.label)
    return out


# ------------------------------------------------------------------ main
def build_variant(route: Route, days: list[Day], alt_days: list[Day], out_dir: Path, title: str,
                  variant_note: str, day_files: list[Day], pages_too: bool):
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in (out_dir / "days").glob("*.gpx"):   # labels shift between options: no stale files
        old.unlink()
    stats = {d.id: day_stats(route, d) for d in days + alt_days}
    for d in day_files:
        build_day_gpx(route, d, stats[d.id], out_dir / "days")
    build_masters(route, days, stats, out_dir, title)
    all_gaps = fuel.load_gaps()
    gaps = {d.id: all_gaps.get(d.id, {"max_gap_km": float("nan")}) for d in days}
    rows = summary_rows(route, days, stats, gaps)
    alt_rows = summary_rows(route, alt_days, stats, {}) if alt_days else []
    write_csv(rows + alt_rows, out_dir / "summary.csv")
    buffer_days = int(route.meta.get("trip_days", 30)) - len(days)
    write_summary_md(route, days, rows, gaps, out_dir / "summary.md", title, variant_note, alt_rows, buffer_days)
    if pages_too:
        from . import pages
        pages.write_all(route, days, alt_days, stats, rows, alt_rows, out_dir, title, buffer_days)
    return rows


def run():
    route = load_route()
    chosen = str(route.meta.get("chosen_option", "A")).upper()
    seq_a, seq_b = route.base_days, route.option_b_sequence()
    replaced = set(route.option_b_meta.get("replaces", []))
    variants = {
        "A": dict(days=seq_a, title="Long Way Home – Option A (Swedish Lapland)",
                  note=f"Option A: {len(seq_a)} riding days via Kiruna and Pajala (no Nordkapp).",
                  only=[d for d in seq_a if d.id in replaced]),
        "B": dict(days=seq_b, title="Long Way Home – Nordkapp",
                  note=f"Option B: {len(seq_b)} riding days including Nordkapp.",
                  only=list(route.option_b)),
    }
    other = "A" if chosen == "B" else "B"
    v = variants[chosen]
    rows = build_variant(route, v["days"], route.alt_days, OUT, v["title"],
                         v["note"] + " **Chosen route.**", v["days"] + route.alt_days, pages_too=True)
    o = variants[other]
    rows_o = build_variant(route, o["days"], [], OUT / f"option_{other.lower()}", o["title"],
                           o["note"] + " Not chosen – kept for reference. Day files here cover only the days that "
                           "differ; all other days are in `out/days/`.", o["only"], pages_too=False)
    print(f"Option {chosen} (chosen): {sum(r['km'] for r in rows):,.0f} km in {len(rows)} days → out/")
    if any(r["gravel_km"] for r in rows):
        print("!! out/ contains TET-derived gravel tracks. TET terms forbid redistribution and this repo/site is "
              "public – do not commit or push out/ built like this.")
    print(f"Option {other}: {sum(r['km'] for r in rows_o):,.0f} km in {len(rows_o)} days → out/option_{other.lower()}/")
