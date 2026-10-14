"""Optional TET gravel: splice a section of a Trans Euro Trail track into a day's land leg.

The TET GPX may only be downloaded by the rider (transeurotrail.org terms forbid automated retrieval and
redistribution), so it is never fetched or published: it lives in the private submodule (private/tet/, see common.PRIVATE)
or, without it, in the git-ignored input/tet/; then re-run `route --tet`.

route.yaml `gravel:` entries name a leg (day + from/to point names) and the TET file. For each entry:
  1. find the TET segment passing within SNAP_KM of both leg endpoints (or of `join`/`leave` [lat, lon], where the
     TET meets the road, when it covers only part of the leg),
  2. cut it between the two nearest points,
  3. join it to the endpoints with BRouter connector legs,
  4. keep it only if it is ≤ max_detour × the road leg (default 1.6) – otherwise the road leg stays.
Without the file the entry is simply reported as "not applied".
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import gpxpy

from .common import PRIVATE, ROOT, Point, haversine_km

# the private submodule (private/tet/) when it is checked out, else the git-ignored input/tet/
TET_DIR = Path(os.environ.get("LWH_TET_DIR") or
               (PRIVATE / "tet" if (PRIVATE / "tet").is_dir() else ROOT / "input" / "tet"))
SNAP_KM = 8.0
GRAVEL_KMH = 45          # planning speed on wide hard-packed gravel with a loaded GS
SHAPE_EVERY_KM = 8.0     # rte shaping points along the gravel so Kurviger follows it

_tracks: dict[Path, list[list[tuple[float, float, float | None]]]] = {}


def _segments(path: Path):
    if path not in _tracks:
        g = gpxpy.parse(path.read_text(encoding="utf-8"))
        segs = [[(p.latitude, p.longitude, p.elevation) for p in s.points] for t in g.tracks for s in t.segments]
        segs += [[(p.latitude, p.longitude, p.elevation) for p in r.points] for r in g.routes]
        _tracks[path] = [s for s in segs if len(s) >= 2]
    return _tracks[path]


def _nearest(seg, lat, lon) -> tuple[float, int]:
    best = (float("inf"), -1)
    for i, (la, lo, _) in enumerate(seg):
        if abs(la - lat) < 0.2 and abs(lo - lon) < 0.5:
            d = haversine_km(lat, lon, la, lo)
            if d < best[0]:
                best = (d, i)
    return best


def cut(path: Path, a: Point, b: Point):
    """Closest TET sub-track from near `a` to near `b`, or (None, reason)."""
    best = None
    for seg in _segments(path):
        da, i = _nearest(seg, a.lat, a.lon)
        db, j = _nearest(seg, b.lat, b.lon)
        if da <= SNAP_KM and db <= SNAP_KM and i != j and (best is None or da + db < best[0]):
            sub = seg[i:j + 1] if i < j else seg[j:i + 1][::-1]
            best = (da + db, sub)
    if best is None:
        return None, f"TET does not pass within {SNAP_KM:.0f} km of both {a.name} and {b.name}"
    return best[1], ""


def file_tag(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:8]


def gravel_leg(entry: dict, a: Point, b: Point, road: dict, connect) -> tuple[dict | None, str]:
    """Return (leg, message). `connect(p, q)` routes a paved connector leg (BRouter/OSRM)."""
    path = TET_DIR / entry["file"]
    if not path.exists():
        return None, f"not applied – put {entry['file']} (from transeurotrail.org) into input/tet/"
    # join/leave: where the TET meets the road when it covers only part of the leg (default: the leg's ends)
    ja = Point(name=f"TET join ({entry['label']})", lat=entry["join"][0], lon=entry["join"][1], type="shape") \
        if entry.get("join") else a
    jb = Point(name=f"TET leave ({entry['label']})", lat=entry["leave"][0], lon=entry["leave"][1], type="shape") \
        if entry.get("leave") else b
    sub, why = cut(path, ja, jb)
    if sub is None:
        return None, f"not applied – {why}"
    s = Point(name=f"TET start ({entry['label']})", lat=sub[0][0], lon=sub[0][1], type="shape")
    e = Point(name=f"TET end ({entry['label']})", lat=sub[-1][0], lon=sub[-1][1], type="shape")
    c1 = connect(a, s) if haversine_km(a.lat, a.lon, s.lat, s.lon) > 0.05 else None
    c2 = connect(e, b) if haversine_km(e.lat, e.lon, b.lat, b.lon) > 0.05 else None
    gravel_km = sum(haversine_km(p[0], p[1], q[0], q[1]) for p, q in zip(sub, sub[1:]))
    km = gravel_km + sum(c["length_km"] for c in (c1, c2) if c)
    limit = entry.get("max_detour", 1.6) * road["length_km"]
    if km > limit:
        return None, f"not applied – TET version is {km:.0f} km vs {road['length_km']:.0f} km road (limit {limit:.0f})"
    coords = (c1["coords"] if c1 else []) + [[la, lo, el] for la, lo, el in sub] + (c2["coords"] if c2 else [])
    shaping, run = [], 0.0
    for p, q in zip(sub, sub[1:]):
        run += haversine_km(p[0], p[1], q[0], q[1])
        if run >= SHAPE_EVERY_KM:
            shaping.append([round(q[0], 5), round(q[1], 5)])
            run = 0.0
    leg = {"engine": "tet+" + "/".join(sorted({c["engine"] for c in (c1, c2) if c}) or {"none"}),
           "profile": f"TET {entry['file']}@{file_tag(path)}",
           "coords": coords, "length_km": km,
           "time_s": gravel_km / GRAVEL_KMH * 3600 + sum(c["time_s"] for c in (c1, c2) if c),
           "router_ferry": any(c["router_ferry"] for c in (c1, c2) if c),
           "ferry_tags": [], "gravel_km": gravel_km, "gravel_label": entry["label"], "shaping": shaping,
           "road_km": road["length_km"]}
    return leg, f"applied – {gravel_km:.0f} km gravel, leg {road['length_km']:.0f} → {km:.0f} km"
