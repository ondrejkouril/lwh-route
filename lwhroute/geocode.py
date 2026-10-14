"""Step 2: verify coordinates.

* Named places  -> Nominatim forward search (≤1 req/s, cached in data/geocode_cache.json).
                   FLAG when the best match is > 3 km from the YAML coordinate.
* Road shaping  -> OSRM: snap to the nearest car road and read its ref (route step `ref`).
                   If it is the wrong road, FLAG and suggest a nearby point that is on it.
  (Overpass was too overloaded to use for this; it is kept for the fuel check.)
Nothing is overwritten: fixes go into the point's `override:` field in route.yaml.
"""
from __future__ import annotations

import json
import math
import re
import time

from .common import DATA, JsonCache, Throttled, haversine_km, load_route, unique_points

GEOCODE_CACHE = DATA / "geocode_cache.json"
FLAG_KM = 3.0
ROAD_OK_M = 400


nominatim = Throttled(1.1)
overpass = Throttled(2.0)
OVERPASS_URLS = ["https://overpass.private.coffee/api/interpreter",
                 "https://overpass-api.de/api/interpreter",
                 "https://overpass.kumi.systems/api/interpreter",
]
_ov_cache = JsonCache("overpass")


def _load_cache() -> dict:
    return json.loads(GEOCODE_CACHE.read_text(encoding="utf-8")) if GEOCODE_CACHE.exists() else {}


def nominatim_search(q: str, cache: dict) -> list[dict]:
    if q not in cache:
        r = nominatim.get("https://nominatim.openstreetmap.org/search",
                          params={"q": q, "format": "jsonv2", "limit": 5})
        r.raise_for_status()
        cache[q] = [{"lat": float(x["lat"]), "lon": float(x["lon"]), "name": x.get("display_name", "")}
                    for x in r.json()]
        GEOCODE_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache[q]


_overpass_down = False
OVERPASS_ROUNDS = 3
_preferred = 0


def overpass_query(q: str, retry_if_down: bool = False) -> dict:
    global _overpass_down
    hit = _ov_cache.get(q)
    if hit is not None:
        return hit
    if _overpass_down and not retry_if_down:
        raise RuntimeError("Overpass marked down earlier in this run")
    global _preferred
    for attempt in range(OVERPASS_ROUNDS * len(OVERPASS_URLS)):
        k = (_preferred + attempt) % len(OVERPASS_URLS)   # start with the mirror that last worked
        url = OVERPASS_URLS[k]
        if attempt and attempt % len(OVERPASS_URLS) == 0:
            time.sleep(20 * attempt // len(OVERPASS_URLS))   # all mirrors failed: back off, next round
        try:
            r = overpass.post(url, data={"data": q}, timeout=60)
        except Exception as e:
            print(f"    overpass {url.split('/')[2]} {type(e).__name__}, trying next", flush=True)
            continue
        if r.status_code == 200 and r.text.lstrip().startswith("{"):
            js = r.json()
            if "remark" in js and not js.get("elements") and "error" in js["remark"].lower():
                print(f"    overpass remark: {js['remark'][:80]}", flush=True)
                continue
            _ov_cache.set(q, js)
            _preferred = k
            return js
        print(f"    overpass {url.split('/')[2]} {r.status_code}, trying next", flush=True)
    _overpass_down = True   # circuit breaker: don't stall the rest of the run
    raise RuntimeError("Overpass failed on all mirrors")


def norm_ref(ref: str) -> set[str]:
    """'E 6;Fv450' -> {'E6', '450'}; national/county prefixes are dropped."""
    out = set()
    for part in re.split(r"[;,/]", ref or ""):
        s = re.sub(r"\s+", "", part.upper())
        s = re.sub(r"^(FV|RV|FYLKESVEI|RIKSVEI|LV|RIKSVÄG|VT|KT|ST|SH)", "", s)
        if s:
            out.add(s)
    return out


def ref_matches(osm_ref: str, want: str) -> bool:
    return bool(norm_ref(osm_ref) & norm_ref(want))



OSRM = "https://router.project-osrm.org"
osrm = Throttled(1.0)


def osrm_road_at(lat: float, lon: float, cache: dict) -> dict:
    """Snap to the nearest car-routable road (OSRM) and read that road's name/ref from a zero-length route."""
    key = f"osrm-road:{lat:.5f},{lon:.5f}"
    if key not in cache:
        r = osrm.get(f"{OSRM}/route/v1/driving/{lon:.6f},{lat:.6f};{lon:.6f},{lat:.6f}",
                     params={"steps": "true", "overview": "false"})
        r.raise_for_status()
        js = r.json()
        step = js["routes"][0]["legs"][0]["steps"][0]
        wp = js["waypoints"][0]
        cache[key] = {"ref": step.get("ref", ""), "name": step.get("name", ""),
                      "lat": wp["location"][1], "lon": wp["location"][0], "snap_m": wp["distance"]}
        GEOCODE_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache[key]


def osrm_nearest(lat: float, lon: float, cache: dict, n: int = 10) -> list[tuple[float, float]]:
    key = f"osrm-nearest{n}:{lat:.5f},{lon:.5f}"
    if key not in cache:
        r = osrm.get(f"{OSRM}/nearest/v1/driving/{lon:.6f},{lat:.6f}", params={"number": n})
        r.raise_for_status()
        cache[key] = [(w["location"][1], w["location"][0]) for w in r.json().get("waypoints", [])]
        GEOCODE_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache[key]


def road_matches(road: dict, want: str) -> bool:
    """`want` is 'ref|ref|Name' alternatives: refs compare normalised, names as case-insensitive substrings."""
    for alt in want.split("|"):
        alt = alt.strip()
        if any(c.isdigit() for c in alt):
            if ref_matches(road["ref"], alt):
                return True
        elif alt.lower() in (road["name"] or "").lower():
            return True
    return False


RING_KM = (0.25, 0.6, 1.2, 2.5, 4.0, 6.0)


def ring(lat: float, lon: float, r_km: float, n: int | None = None):
    n = n or (8 if r_km < 2 else 16)
    for k in range(n):
        a = 2 * math.pi * k / n
        yield (lat + r_km / 111.2 * math.cos(a),
               lon + r_km / (111.2 * math.cos(math.radians(lat))) * math.sin(a))


def check_road(lat: float, lon: float, want: str, cache: dict) -> dict:
    """Shaping point must snap onto road `want`. On a miss, probe rings of points around it (OSRM snap + ref)
    and suggest the nearest snapped location that is on that road."""
    here = osrm_road_at(lat, lon, cache)
    if road_matches(here, want) and here["snap_m"] <= ROAD_OK_M:
        return {"status": "OK", "dist_km": here["snap_m"] / 1000, "found": f"on {here['ref'] or here['name']}"}
    seen = f"snaps to {here['name'] or '?'} ref={here['ref'] or '-'} ({here['snap_m']:.0f} m)"
    best = None
    for r_km in RING_KM:
        for la, lo in ring(lat, lon, r_km):
            cand = osrm_road_at(la, lo, cache)
            if road_matches(cand, want):
                d = haversine_km(lat, lon, cand["lat"], cand["lon"])
                if best is None or d < best[0]:
                    best = (d, cand["lat"], cand["lon"])
        if best is not None:
            break
    if best is None:
        return {"status": "FLAG", "dist_km": None, "found": f"{seen}; no {want} within {RING_KM[-1]:.0f} km"}
    return {"status": "FLAG", "dist_km": best[0], "found": f"{seen}; {want} nearby",
            "suggest": (round(best[1], 5), round(best[2], 5))}


def survey(lat: float, lon: float, cache: dict) -> list[str]:
    """Distinct roads (ref / name) around a point – for choosing the right `road:` value."""
    out = {}
    for r_km in (0.0,) + RING_KM:
        for la, lo in ([(lat, lon)] if r_km == 0 else ring(lat, lon, r_km)):
            c = osrm_road_at(la, lo, cache)
            k = (c["ref"], c["name"])
            d = haversine_km(lat, lon, c["lat"], c["lon"])
            if k not in out or d < out[k][0]:
                out[k] = (d, c["lat"], c["lon"])
    return [f"{d:5.2f} km  ref={ref or '-':10} {name or '?':28} ({la:.5f}, {lo:.5f})"
            for (ref, name), (d, la, lo) in sorted(out.items(), key=lambda kv: kv[1][0])]


def run(include_option_b: bool = True) -> list[dict]:
    route = load_route()
    days = route.days + (route.option_b if include_option_b else []) + route.shortcut + route.variant
    cache = _load_cache()
    rows = []
    for day, p in unique_points(days):
        row = {"day": day.id, "name": p.name, "lat": p.lat, "lon": p.lon, "override": bool(p.override)}
        if p.road:
            # Shaping point: what matters is sitting on the named road; a village name is only a label.
            rr = check_road(p.lat, p.lon, p.road, cache)
            row.update(check=f"road {p.road}", **{k: rr[k] for k in ("status", "dist_km", "found")})
            if "suggest" in rr:
                row["suggest"] = rr["suggest"]
        elif p.geocode:
            hits = nominatim_search(p.geocode, cache)
            if not hits:
                row.update(status="FLAG", check="nominatim", found="no result", dist_km=None)
            else:
                best = min(hits, key=lambda h: haversine_km(p.lat, p.lon, h["lat"], h["lon"]))
                d = haversine_km(p.lat, p.lon, best["lat"], best["lon"])
                row.update(check="nominatim", dist_km=d, found=best["name"][:60],
                           suggest=(round(best["lat"], 5), round(best["lon"], 5)),
                           status="OK" if d <= FLAG_KM else "FLAG")
        else:
            row.update(status="UNCHECKED", check="-", found="no geocode/road key", dist_km=None)
        if p.override and row["status"] == "FLAG":
            row["status"] = "OVERRIDE"   # already resolved by hand
        print(f"  {row['status']:9} {day.id:8} {p.name}", flush=True)
        rows.append(row)
    return rows


def apply_snaps(rows: list[dict], path=DATA / "route.yaml") -> int:
    """Write OSRM road-snap suggestions for flagged shaping points into route.yaml as `override:` (with reason).
    Only road checks are applied automatically; place-name flags stay for a human to judge."""
    text = path.read_text(encoding="utf-8")
    n = 0
    for r in rows:
        if r["status"] != "FLAG" or not r["check"].startswith("road") or not r.get("suggest"):
            continue
        la, lo = r["suggest"]
        reason = f"snapped onto {r['check'][5:]} (OSRM), was {r['dist_km']:.2f} km off"
        ov = f'override: {{lat: {la}, lon: {lo}, reason: "{reason}"}}, '
        pat = re.compile(r"(\{name: " + re.escape(r["name"]) + r", lat: [\d.]+, lon: [\d.]+, )(override: \{[^}]*\}, )?")
        text, k = pat.subn(lambda m: m.group(1) + ov, text)
        n += k
        print(f"  snap {r['name']}: {k} occurrence(s) → {la}, {lo}")
    path.write_text(text, encoding="utf-8")
    return n


def print_table(rows: list[dict]) -> int:
    print(f"{'day':8} {'status':9} {'Δkm':>7}  {'point':38} {'check':12} found / suggestion")
    flagged = 0
    for r in rows:
        dk = "" if r.get("dist_km") is None else f"{r['dist_km']:.2f}"
        sug = f"  → {r['suggest']}" if r["status"] == "FLAG" and r.get("suggest") else ""
        if r["status"] == "FLAG":
            flagged += 1
        print(f"{r['day']:8} {r['status']:9} {dk:>7}  {r['name'][:38]:38} {r['check'][:12]:12} {r['found']}{sug}")
    counts = {s: sum(r["status"] == s for r in rows) for s in ("OK", "FLAG", "OVERRIDE", "UNCHECKED")}
    print(f"\n{len(rows)} unique points: {counts}")
    return flagged
