"""Fuel-gap check: OSM amenity=fuel (Overpass, `around` the day's track) projected onto the track."""
from __future__ import annotations

import json
import math

from .common import DATA, TrackIndex, haversine_km, load_route
from .geocode import overpass_query

CORRIDOR_KM = 1.5
MAX_GAP_KM = 180
PROBE_SPACING_KM = 4.0


def _probe_line(coords) -> list[tuple[float, float]]:
    out = [coords[0]]
    for c in coords[1:]:
        if haversine_km(*out[-1], *c) >= PROBE_SPACING_KM:
            out.append(c)
    out.append(coords[-1])
    return out


CHUNK = 40   # probe points per Overpass query; dense corridors (PL/CZ) time out as one big query


def _stations(coords) -> list[tuple[float, float, str]]:
    probes = _probe_line(coords)

    def query(pts):
        line = ",".join(f"{la:.4f},{lo:.4f}" for la, lo in pts)
        js = overpass_query(f"[out:json][timeout:90];nwr[amenity=fuel](around:{CORRIDOR_KM * 1000:.0f},{line});"
                            f"out center tags;", retry_if_down=True)
        return {(e["type"], e["id"]): e for e in js.get("elements", [])}

    try:
        elements = query(probes)
    except RuntimeError:   # one big query timed out: retry in chunks
        elements = {}
        for i in range(0, len(probes) - 1, CHUNK):
            elements.update(query(probes[i:i + CHUNK + 1]))
    out = []
    for e in elements.values():
        la = e.get("lat", e.get("center", {}).get("lat"))
        lo = e.get("lon", e.get("center", {}).get("lon"))
        if la is not None:
            t = e.get("tags", {})
            out.append((la, lo, t.get("name") or t.get("brand") or "fuel"))
    return out


def day_track(stats_day: dict) -> list[tuple[float, float]]:
    """Land coordinates of the whole day, ferry crossings excluded (concatenated in order)."""
    coords = []
    for part in stats_day["routed"]["parts"]:
        if part["kind"] == "land":
            for leg in part["legs"]:
                coords.extend((c[0], c[1]) for c in leg["coords"])
    return coords


def gaps_for_track(coords) -> dict:
    idx = TrackIndex(coords, cell_deg=0.03)
    hits = []
    for la, lo, name in _stations(coords):
        d, i = idx.nearest(la, lo)
        if d <= CORRIDOR_KM:
            hits.append((idx.cum[i], name))
    hits.sort()
    total = idx.cum[-1]
    marks = [(0.0, "day start")] + hits + [(total, "day end")]
    best = max(zip(marks, marks[1:]), key=lambda ab: ab[1][0] - ab[0][0])
    return {"max_gap_km": best[1][0] - best[0][0], "gap_from": best[0][1], "gap_to": best[1][1],
            "stations": len(hits)}


FUEL_JSON = DATA / "fuel.json"


def run():
    """Compute gaps for every day (base, alternatives, Option B) and store them in data/fuel.json."""
    from .build import day_stats
    route = load_route()
    res = load_gaps()
    for d in route.all_days():
        coords = day_track(day_stats(route, d))
        try:
            res[d.id] = gaps_for_track(coords)
            g = res[d.id]
            flag = "  > limit" if g["max_gap_km"] > MAX_GAP_KM else ""
            print(f"  {d.id:17} max gap {g['max_gap_km']:5.0f} km  ({g['stations']} stations){flag}")
        except RuntimeError as e:
            print(f"  {d.id:17} fuel check failed: {e}")
            res.setdefault(d.id, {"max_gap_km": math.nan, "error": "Overpass unavailable"})
        FUEL_JSON.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


def load_gaps() -> dict:
    if FUEL_JSON.exists():
        return json.loads(FUEL_JSON.read_text(encoding="utf-8"))
    return {}
