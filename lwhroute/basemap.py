"""Offline basemap: Natural Earth 1:10m countries + lakes (public domain), clipped to the trip area and simplified.

Written once to data/basemap.json so map pages show land, borders and lakes even where tile servers are
blocked (e.g. sandboxed viewers) or offline. Run: python -m lwhroute basemap
"""
from __future__ import annotations

import json
import math

import requests

from .common import DATA, USER_AGENT

NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/"
BBOX = (3.0, 46.5, 34.0, 72.0)     # lon_min, lat_min, lon_max, lat_max
TOL = 0.006                        # Douglas–Peucker tolerance in degrees (~0.3–0.6 km)
MIN_AREA = 0.002                   # drop islands/lakes smaller than this (deg²)
OUT_FILE = DATA / "basemap.json"


def _dp(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1e-12
        best, idx = 0.0, None
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n
            if d > best:
                best, idx = d, i
        if idx is not None and best > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def _area(r):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]))) / 2


def _in_bbox(r):
    xs, ys = [p[0] for p in r], [p[1] for p in r]
    return not (max(xs) < BBOX[0] or min(xs) > BBOX[2] or max(ys) < BBOX[1] or min(ys) > BBOX[3])


def _polys(geom):
    return [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]


def _simplify(feature_geom):
    out = []
    for poly in _polys(feature_geom):
        outer = poly[0]
        if not _in_bbox(outer) or _area(outer) < MIN_AREA:
            continue
        rings = []
        for ring in poly:
            # closed ring: first == last, so split at the farthest vertex before simplifying
            k = max(range(len(ring)), key=lambda i: (ring[i][0] - ring[0][0]) ** 2 + (ring[i][1] - ring[0][1]) ** 2)
            s = _dp(ring[:k + 1], TOL)[:-1] + _dp(ring[k:], TOL)
            if len(s) >= 4 and _area(s) >= MIN_AREA:
                rings.append([[round(x, 3), round(y, 3)] for x, y in s])
        if rings:
            out.append(rings)
    return out


def run():
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    res = {"countries": [], "lakes": []}
    for name, key, props in (("ne_10m_admin_0_countries.geojson", "countries", ("NAME_EN", "ISO_A2_EH")),
                             ("ne_10m_lakes.geojson", "lakes", ("name",)),
                             ("ne_10m_lakes_europe.geojson", "lakes", ("name",))):
        print(f"  downloading {name}")
        r = s.get(NE + name, timeout=300)
        r.raise_for_status()
        for f in r.json()["features"]:
            polys = _simplify(f["geometry"])
            if polys:
                res[key].append({"name": f["properties"].get(props[0]) or "",
                                 "iso": f["properties"].get(props[1], "") if len(props) > 1 else "",
                                 "polys": polys})
    OUT_FILE.write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  {len(res['countries'])} countries, {len(res['lakes'])} lakes → {OUT_FILE} "
          f"({OUT_FILE.stat().st_size / 1e6:.1f} MB)")


def load() -> dict:
    return json.loads(OUT_FILE.read_text(encoding="utf-8")) if OUT_FILE.exists() else {"countries": [], "lakes": []}
