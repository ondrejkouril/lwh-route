"""Step 3: route every land leg (days split at ferry_start/ferry_end) with BRouter, OSRM as fallback.

Ferries are never routed: a crossing is a straight 2-point segment between the ferry points.
Each leg = two consecutive routed points; responses are cached per leg in data/cache/<engine>/.
BRouter runs a custom no-ferry variant of car-fast (uploaded per run), so it cannot pick a ferry;
OSRM fallback is checked for ferry steps. BRouter is queried as GeoJSON (same engine as format=gpx) because only that output
carries the per-way tags needed to prove no router-chosen ferry (route=ferry) is used.
"""
from __future__ import annotations

import hashlib
import json
import time

from .common import DATA, ROOT, TET_BUILD, JsonCache, Point, Throttled, load_route
from .tet import GRAVEL_KMH

PROFILE = "car-fast-noferry"   # stock car-fast with route=ferry impassable (profiles/car-fast-noferry.brf)
PROFILE_FILE = ROOT / "profiles" / f"{PROFILE}.brf"
BROUTER = "https://brouter.de/brouter"
OSRM = "https://router.project-osrm.org/route/v1/driving"
ROUTED = DATA / ("routed_tet" if TET_BUILD else "routed")

_brouter = Throttled(1.5)
_profile_id: str | None = None


def profile_tag() -> str:
    """Cache-key tag: profile name + content hash (custom ids on the server are ephemeral)."""
    return f"{PROFILE}-{hashlib.sha1(PROFILE_FILE.read_bytes()).hexdigest()[:8]}"


def brouter_profile_id() -> str:
    """Upload the custom profile once per run; BRouter returns a temporary custom_* id."""
    global _profile_id
    if _profile_id is None:
        r = _brouter.post(f"{BROUTER}/profile", data=PROFILE_FILE.read_bytes(),
                          headers={"Content-Type": "text/plain"})
        r.raise_for_status()
        js = r.json()
        if js.get("error"):
            raise RuntimeError(f"BRouter rejected profile: {js['error']}")
        _profile_id = js["profileid"]
        print(f"  uploaded {PROFILE} as {_profile_id}")
    return _profile_id
_osrm = Throttled(1.0)
_bc = JsonCache("brouter")
_oc = JsonCache("osrm")


def day_parts(points: list[Point]) -> list[dict]:
    """Split routed points into land parts and ferry crossings."""
    parts, cur, pending = [], [], None
    for p in (p for p in points if p.routed):
        if p.type == "ferry_end" and pending is not None:
            parts.append({"kind": "ferry", "ferry": pending.ferry or p.ferry, "a": pending, "b": p})
            pending, cur = None, [p]
            continue
        cur.append(p)
        if p.type == "ferry_start":
            if len(cur) >= 2:
                parts.append({"kind": "land", "points": cur})
            pending, cur = p, []
    if len(cur) >= 2:
        parts.append({"kind": "land", "points": cur})
    return parts


def _lonlat(p: Point) -> str:
    return f"{p.lon:.6f},{p.lat:.6f}"


UNPAVED = {"gravel", "unpaved", "compacted", "fine_gravel", "dirt", "ground", "pebblestone"}
SLOW_KMH = 40   # a cached leg slower than this on average predates the unpaved re-timing below: fetch it again


def _unpaved_retime(hdr: list, rows: list) -> tuple[float, float]:
    """(unpaved km, seconds to subtract). Stock car-fast caps unpaved roads at 2 km/h to keep cars off them; the
    route only uses gravel where shaping points force it (e.g. Fv258), so time those segments at GRAVEL_KMH."""
    try:
        wi, di, ti = hdr.index("WayTags"), hdr.index("Distance"), hdr.index("Time")
    except ValueError:
        return 0.0, 0.0
    km = saved = 0.0
    prev_t = 0.0
    for row in rows:
        t = float(row[ti])
        tags = dict(kv.split("=", 1) for kv in row[wi].split() if "=" in kv)
        if tags.get("surface") in UNPAVED:
            d_km = float(row[di]) / 1000
            km += d_km
            saved += max(0.0, (t - prev_t) - d_km / GRAVEL_KMH * 3600)
        prev_t = t
    return km, saved


def brouter_leg(a: Point, b: Point) -> dict | None:
    key = f"{profile_tag()}|{_lonlat(a)}|{_lonlat(b)}"
    hit = _bc.get(key)
    if hit is not None and ("unpaved_km" in hit or hit["time_s"] <= 0
                            or hit["length_km"] / (hit["time_s"] / 3600) >= SLOW_KMH):
        return hit
    params = {"lonlats": f"{_lonlat(a)}|{_lonlat(b)}", "profile": brouter_profile_id(),
              "alternativeidx": 0, "format": "geojson"}
    for attempt in range(4):
        try:
            r = _brouter.get(BROUTER, params=params, timeout=180)
        except Exception as e:  # network hiccup
            print(f"    brouter error {e}; retry")
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 200 and r.text.lstrip().startswith("{"):
            f = r.json()["features"][0]
            props = f["properties"]
            msgs = props.get("messages") or []
            hdr, rows = (msgs[0], msgs[1:]) if msgs else ([], [])
            wi = hdr.index("WayTags") if "WayTags" in hdr else None
            waytags = [row[wi] for row in rows] if wi is not None else []
            ferry_tags = [t for t in waytags if "route=ferry" in t]
            unpaved_km, saved_s = _unpaved_retime(hdr, rows)
            res = {
                "engine": "brouter", "profile": PROFILE,
                "coords": [[c[1], c[0], c[2] if len(c) > 2 else None] for c in f["geometry"]["coordinates"]],
                "length_km": float(props["track-length"]) / 1000,
                "time_s": float(props["total-time"]) - saved_s,
                "unpaved_km": round(unpaved_km, 2),
                "router_ferry": bool(ferry_tags), "ferry_tags": ferry_tags[:5],
            }
            _bc.set(key, res)
            return res
        print(f"    brouter {r.status_code}: {r.text[:120]!r}")
        if "no track found" in r.text or "island" in r.text or "not mapped" in r.text:
            return None   # deterministic failure: point problem, retrying won't help
        time.sleep(30 if r.status_code == 403 else 5 * (attempt + 1))
    return None


def osrm_leg(a: Point, b: Point) -> dict | None:
    key = f"driving|{_lonlat(a)}|{_lonlat(b)}"
    hit = _oc.get(key)
    if hit is not None:
        return hit
    r = _osrm.get(f"{OSRM}/{_lonlat(a)};{_lonlat(b)}",
                  params={"overview": "full", "geometries": "geojson", "steps": "true"})
    if r.status_code != 200:
        print(f"    osrm {r.status_code}: {r.text[:120]!r}")
        return None
    rt = r.json()["routes"][0]
    ferry = any(s.get("mode") == "ferry" for leg in rt["legs"] for s in leg["steps"])
    res = {"engine": "osrm", "profile": "driving",
           "coords": [[c[1], c[0], None] for c in rt["geometry"]["coordinates"]],
           "length_km": rt["distance"] / 1000, "time_s": rt["duration"],
           "router_ferry": ferry, "ferry_tags": ["osrm step mode=ferry"] if ferry else []}
    _oc.set(key, res)
    return res


def _connect(a: Point, b: Point) -> dict:
    leg = brouter_leg(a, b) or osrm_leg(a, b)
    if leg is None:
        raise LegError(f"no connector route {a.name} → {b.name}")
    return leg


def route_day(day, gravel: list[dict] = ()) -> dict:
    out = {"id": day.id, "parts": []}
    tet_for = {(g["day"], g["from"], g["to"]): g for g in gravel}
    for part in day_parts(day.points):
        if part["kind"] == "ferry":
            a, b = part["a"], part["b"]
            out["parts"].append({"kind": "ferry", "ferry": part["ferry"], "from": a.name, "to": b.name,
                                 "coords": [[a.lat, a.lon, None], [b.lat, b.lon, None]]})
            continue
        legs = []
        pts = part["points"]
        for a, b in zip(pts, pts[1:]):
            leg = brouter_leg(a, b) or osrm_leg(a, b)
            if leg is None:
                raise LegError(f"{day.id}: no route {a.name} → {b.name}")
            g = tet_for.get((day.id, a.name, b.name))
            if g:
                from . import tet
                gl, msg = tet.gravel_leg(g, a, b, leg, _connect)
                print(f"  {day.id} TET gravel '{g['label']}': {msg}")
                leg = gl or leg
            legs.append({"from": a.name, "to": b.name, **leg})
            flag = "  !! ROUTER FERRY" if leg["router_ferry"] else ""
            print(f"  {day.id} {a.name[:28]:28} → {b.name[:28]:28} {leg['length_km']:7.1f} km  [{leg['engine']}]{flag}")
        out["parts"].append({"kind": "land", "from": pts[0].name, "to": pts[-1].name, "legs": legs})
    return out


class LegError(RuntimeError):
    pass


def run():
    ROUTED.mkdir(parents=True, exist_ok=True)
    route = load_route()
    gravel = route.gravel if TET_BUILD else []
    if route.gravel and not TET_BUILD:
        print(f"  {len(route.gravel)} TET gravel section(s) skipped – `route --tet` builds them into data/routed_tet/")
    failed = []
    for day in route.all_days():
        try:
            res = route_day(day, gravel)
        except LegError as e:
            print(f"  !! {e}")
            failed.append(str(e))
            continue
        (ROUTED / f"{day.id}.json").write_text(json.dumps(res), encoding="utf-8")
        km = sum(l["length_km"] for p in res["parts"] if p["kind"] == "land" for l in p["legs"])
        print(f"{day.id}: {km:.0f} km (target {day.target_km:.0f})")
    if failed:
        raise RuntimeError("unroutable legs:\n  " + "\n  ".join(failed))


def load_routed(day_id: str) -> dict:
    return json.loads((ROUTED / f"{day_id}.json").read_text(encoding="utf-8"))
