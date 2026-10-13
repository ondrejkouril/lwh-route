"""Remove town-centre U-turns.

A via point placed in a town centre makes the router drive in and back out along the same road.
For every internal routed point where the track U-turns (and the point is not a declared spur):
  * route prev → next directly; if that route passes within BYPASS_KM of the point, move the point
    onto that through-route (written to route.yaml as `override:` with a reason);
  * otherwise the point is a real destination: a `poi` is marked `spur: short` (expected U-turn),
    anything else is reported for a human decision.
"""
from __future__ import annotations

import re

from .common import DATA, TrackIndex, load_route
from .routing import brouter_leg, day_parts, load_routed, osrm_leg
from .validate import uturn_at

BYPASS_KM = 4.0


def _uturn_points(day) -> list[str]:
    r = load_routed(day.id)
    out = []
    for part in r["parts"]:
        if part["kind"] != "land":
            continue
        seg, joins = [], []
        for leg in part["legs"]:
            seg.extend((c[0], c[1]) for c in leg["coords"])
            joins.append((len(seg) - 1, leg["to"]))
        out += [name for j, name in joins[:-1] if uturn_at(seg, j)]
    return out


def _edit_in_day(text: str, day_id: str, name: str, insert: str) -> tuple[str, int]:
    """Apply `insert` (override / spur) to point `name` inside the YAML block of `day_id` only."""
    m = re.search(rf"^\s*- id: {re.escape(day_id)}\s*$", text, flags=re.M)
    if not m:
        return text, 0
    nxt = re.search(r"^\s*- id: ", text[m.end():], flags=re.M)
    end = m.end() + (nxt.start() if nxt else len(text) - m.end())
    block = text[m.start():end]
    pat = re.compile(r"(\{name: " + re.escape(name) + r", lat: [\d.]+, lon: [\d.]+, )(override: \{[^}]*\}, )?")
    if insert.startswith("override:"):
        repl = lambda mm: mm.group(1) + insert                          # replaces an older override
    else:
        repl = lambda mm: mm.group(1) + (mm.group(2) or "") + insert    # keeps an existing override
    block, k = pat.subn(repl, block, count=1)
    return text[:m.start()] + block + text[end:], k


def run() -> int:
    route = load_route()
    path = DATA / "route.yaml"
    text = path.read_text(encoding="utf-8")
    changes = 0
    for day in route.all_days():
        names = _uturn_points(day)
        if not names:
            continue
        for part in day_parts(day.points):
            if part["kind"] != "land":
                continue
            pts = part["points"]
            for i in range(1, len(pts) - 1):
                p = pts[i]
                if p.name not in names or p.spur:
                    continue
                direct = brouter_leg(pts[i - 1], pts[i + 1]) or osrm_leg(pts[i - 1], pts[i + 1])
                coords = [(c[0], c[1]) for c in direct["coords"]]
                d, j = TrackIndex(coords, cell_deg=0.05).nearest(p.lat, p.lon, rings=2)
                if d <= BYPASS_KM:
                    la, lo = coords[j]
                    ins = (f'override: {{lat: {la:.5f}, lon: {lo:.5f}, reason: "moved {d:.1f} km onto the '
                           f'through-route to avoid a town-centre U-turn"}}, ')
                    text, k = _edit_in_day(text, day.id, p.name, ins)
                    print(f"  {day.id:8} {p.name:34} → through-route ({d:.1f} km)  [{k}]")
                elif p.type == "poi":
                    text, k = _edit_in_day(text, day.id, p.name, "spur: short, ")
                    print(f"  {day.id:8} {p.name:34} → marked spur: short (stop {d:.1f} km off the through-route)  [{k}]")
                else:
                    k = 0
                    print(f"  {day.id:8} {p.name:34} !! U-turn, {d:.1f} km off the through-route – decide by hand")
                changes += k
    path.write_text(text, encoding="utf-8")
    return changes
