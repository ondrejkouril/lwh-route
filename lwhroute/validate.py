"""Step 5: validation gates (§3) → console + out/validation.md. Exit code 1 on hard failures."""
from __future__ import annotations

from .build import day_stats
from .common import OUT, TrackIndex, haversine_km, load_route

KM_TOL = 0.20
GAP_KM = 2.0
LWH_M = 500
EXPECT_A, EXPECT_B = 8500, 9200
DAY_LIMIT_KM = 450
TRANSIT_LIMIT_KM = 750   # motorway days (`transit: true`); rider's rule since 2026-10-14


def _walk(seg, j, step, dist_km):
    d, i = 0.0, j
    while 0 <= i + step < len(seg) and d < dist_km:
        d += haversine_km(*seg[i], *seg[i + step])
        i += step
    return seg[i]


def uturn_at(seg, j, probe_km=0.4, tol_km=0.08) -> bool:
    """True if the track arrives at and leaves point j along the same path (back-tracking)."""
    a, b = _walk(seg, j, -1, probe_km), _walk(seg, j, +1, probe_km)
    return haversine_km(*a, *b) < tol_km and haversine_km(*a, *seg[j]) > tol_km


def check_day(route, day) -> dict:
    st = day_stats(route, day)
    res = {"day": day.id, "km": st["km"], "target": day.target_km, "issues": [], "warnings": [], "info": []}
    dev = (st["km"] - day.target_km) / day.target_km
    res["dev"] = dev
    if abs(dev) > KM_TOL:
        res["warnings"].append(f"km {st['km']:.0f} vs target {day.target_km:.0f} ({dev:+.0%})")
    limit = TRANSIT_LIMIT_KM if day.transit else DAY_LIMIT_KM
    if st["km"] > limit:
        res["warnings"].append(f"{st['km']:.0f} km exceeds daily limit {limit}")

    coords_all = []
    for part in st["routed"]["parts"]:
        if part["kind"] == "ferry":
            continue
        for leg in part["legs"]:
            if leg["router_ferry"]:
                res["issues"].append(f"router-chosen ferry {leg['from']} → {leg['to']}: {leg['ferry_tags'][:2]}")
        # gaps inside the segment (legs are concatenated into one trkseg)
        seg, joins = [], []
        for leg in part["legs"]:
            if seg:   # true gap = discontinuity where two separately routed legs meet
                g = haversine_km(*seg[-1], leg["coords"][0][0], leg["coords"][0][1])
                if g > GAP_KM:
                    res["issues"].append(f"gap {g:.1f} km at '{leg['from']}' between routed legs")
            seg.extend((c[0], c[1]) for c in leg["coords"])
            joins.append((len(seg) - 1, leg["to"]))
        long_edges = sum(haversine_km(*a, *b) > GAP_KM for a, b in zip(seg, seg[1:]))
        if long_edges:
            res["info"].append(f"{long_edges} straight router edge(s) > {GAP_KM:.0f} km in {part['from']} → "
                               f"{part['to']} (bridge/tunnel/straight road; densified in the GPX)")
        for j, name in joins[:-1]:
            if uturn_at(seg, j):
                spur = next((p.spur for p in day.points if p.name == name and p.spur), None)
                if spur:
                    res["warnings"].append(f"U-turn at '{name}' – expected ({spur} spur)")
                else:
                    res["issues"].append(f"U-turn at '{name}' (via/shaping point off the through-road – run `bypass`)")
        coords_all.extend(seg)

    idx = TrackIndex(coords_all, cell_deg=0.02)
    for p in day.points:
        if not p.lwh:
            continue
        d, _ = idx.nearest(p.lat, p.lon, rings=2)
        if d * 1000 > LWH_M:
            if p.spur:
                res["warnings"].append(f"LWH '{p.name}' {d*1000:.0f} m off track – OK, marked spur ({p.spur})")
            elif p.type in ("ferry_start", "ferry_end") and d * 1000 <= 2000:
                pass  # ferry terminals are segment endpoints; harbour access roads can end short of the quay
            else:
                res["issues"].append(f"LWH '{p.name}' {'∞' if d == float('inf') else f'{d*1000:.0f}'} m from track")
    return res


def run() -> int:
    route = load_route()
    report = ["# Validation report", ""]
    hard = 0
    for label, days, expect in (("Option A (base)", route.base_days, EXPECT_A),
                                ("Alternatives", route.alt_days, None),
                                ("Option B (full trip)", route.option_b_sequence(), EXPECT_B),
                                ("Shortcut home (alternative ending)", route.shortcut_days(), None),
                                *((f"Variant: {v['meta'].get('tab', '')}", route.variant_days(v), None)
                                  for v in route.variants)):
        if not days:
            continue
        results = [check_day(route, d) for d in days]
        total = sum(r["km"] for r in results)
        head = f"## {label}: {total:,.0f} km" + (f" (expected ≈ {expect:,})" if expect else "")
        print("\n" + head[3:])
        report += [head, "", "| Day | km | target | Δ | status |", "|---|--:|--:|--:|---|"]
        for r in results:
            st = "FAIL" if r["issues"] else ("warn" if r["warnings"] else "ok")
            hard += bool(r["issues"]) and label != "Option B (full trip)"  # B repeats base days; shortcut counts
            report.append(f"| {r['day']} | {r['km']:.0f} | {r['target']:.0f} | {r['dev']:+.0%} | {st} |")
            line = f"  {r['day']:16} {r['km']:6.0f} km  target {r['target']:4.0f}  {r['dev']:+5.0%}  {st}"
            print(line)
            for m in r["issues"]:
                print(f"      ✗ {m}")
            for m in r["warnings"]:
                print(f"      ! {m}")
            for m in r["info"]:
                print(f"      i {m}")
        notes = [f"- **{r['day']}** ✗ {m}" for r in results for m in r["issues"]] + \
                [f"- {r['day']} ! {m}" for r in results for m in r["warnings"]] + \
                [f"- {r['day']} · {m}" for r in results for m in r["info"]]
        report += [""] + (notes or ["All checks passed."]) + [""]
        if label == "Option B (full trip)":
            hard += sum(bool(r["issues"]) for r in results if r["day"].startswith("B"))
    report += [f"Daily limits: {DAY_LIMIT_KM} km, {TRANSIT_LIMIT_KM} km on motorway (transit) days.", "",
               "Checks: km within ±20 % of target · no router-chosen ferry (BRouter WayTags `route=ferry`) · "
               "no gap > 2 km between routed legs (long straight router edges are reported and densified) · every LWH point ≤ 500 m from track or marked as spur.", ""]
    (OUT / "validation.md").write_text("\n".join(report), encoding="utf-8")
    print(f"\nHard failures: {hard}  → {OUT.name}/validation.md")
    return 1 if hard else 0
