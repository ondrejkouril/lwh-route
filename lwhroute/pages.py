"""Web pages for the chosen trip, deployed to GitHub Pages from out/:
  out/index.html      itinerary (English)
  out/cs/index.html   itinerary (Czech; texts from data/i18n_cs.yaml, untranslated data stays English)
  out/map.html        full-screen map (English)

All pages embed their data. The map draws an offline Natural Earth basemap (data/basemap.json) and puts
OpenStreetMap tiles on top when they load; if tiles are blocked or offline, it keeps the offline basemap.
"""
from __future__ import annotations

import copy
import datetime as dt
import html
import json
import math
from pathlib import Path

import requests
import yaml

from . import basemap, fuel
from .build import HOURS_FACTOR, WILD_CAMPING, booking, day_waypoints, ferry_days, open_questions, trip_date, \
    CZ_PL_DE_TOLLS
from .common import CACHE, DATA, TET_BUILD, USER_AGENT, Day, Route, haversine_km

ARCTIC_CIRCLE = 66.5634
CHAPTER_COLORS = ["#c2255c", "#e8590c", "#2b8a3e", "#1c7ed6", "#7048e8", "#0b7285", "#5c940d", "#c92a2a", "#862e9c"]


# ------------------------------------------------------------------ data
def _decimate(coords, step_km=0.2):
    out = [coords[0]]
    for c in coords[1:-1]:
        if haversine_km(out[-1][0], out[-1][1], c[0], c[1]) >= step_km:
            out.append(c)
    out.append(coords[-1])
    return [[round(c[0], 5), round(c[1], 5)] for c in out]


def midnight_sun(lat: float, date: dt.date | None) -> bool:
    """Sun's centre stays above a flat horizon at local midnight (no refraction allowance – conservative,
    so towns just south of the Arctic Circle are not promised midnight sun)."""
    if date is None:
        return False
    n = date.timetuple().tm_yday
    decl = 23.44 * math.sin(math.radians(360 / 365 * (284 + n)))
    return lat > 90 - decl


def _fmt_lat(lat: float) -> str:
    d = int(lat)
    return f"{d}°{round((lat - d) * 60):02d}′N"


def trip_data(route: Route, days: list[Day], alt_days: list[Day], stats: dict, rows: list[dict],
              alt_rows: list[dict], title: str, buffer_days: int, shortcut: dict | None = None,
              own: set | None = None, lede: str | None = None) -> dict:
    """`own`: ids of the days whose GPX files live in this site's days/ folder (a variant); the others are
    linked from the chosen trip's days/ folder. None = all of them are here."""
    row_by = {r["yaml_id"]: r for r in rows + alt_rows}
    repo = (route.meta.get("repo_url") or "").rstrip("/")
    chapters, chapter_of, ci = [], {}, -1
    for d in days:
        if d.chapter or ci < 0:
            ci += 1
            chapters.append({"name": d.chapter or "", "color": CHAPTER_COLORS[ci % len(CHAPTER_COLORS)], "days": []})
        chapters[-1]["days"].append(d.label)
        chapter_of[d.id] = ci
    alt_for = {d.alternative_of: d for d in alt_days}

    lines, out_days, profile, cum = [], [], [], 0.0
    for d in days + alt_days:
        st, r = stats[d.id], row_by[d.id]
        color = "#868e96" if d.is_alt else chapters[chapter_of[d.id]]["color"]
        max_lat = -90.0
        for part in st["routed"]["parts"]:
            if part["kind"] == "ferry":
                lines.append({"day": d.label, "kind": "ferry", "alt": d.is_alt,
                              "c": [[round(c[0], 5), round(c[1], 5)] for c in part["coords"]],
                              "label": route.ferries.get(part["ferry"], {}).get("label", part["ferry"])})
                continue
            for leg in part["legs"]:
                cs = leg["coords"]
                max_lat = max(max_lat, max(c[0] for c in cs))
                lines.append({"day": d.label, "kind": "land", "alt": d.is_alt, "color": color,
                              "gravel": bool(leg.get("gravel_km")), "c": _decimate(cs)})
                if not d.is_alt:   # latitude profile, one sample every ~5 km
                    last = None
                    for c in cs:
                        if last is not None:
                            cum += haversine_km(last[0], last[1], c[0], c[1])
                        if not profile or cum - profile[-1][0] >= 5:
                            profile.append([round(cum, 1), round(c[0], 3)])
                        last = c
        if d.is_alt:
            continue
        date = trip_date(route, d)
        on = d.overnight
        alt = alt_for.get(d.id)
        out_days.append({
            "label": d.label, "id": d.id, "num": int(d.label[1:]), "chapter": chapter_of[d.id], "color": color,
            "date": date.isoformat() if date else "", "title": d.title, "from": d.from_, "to": d.to,
            "km": r["km"], "h": r["riding_h"], "end_km": round(cum),
            "ferries": [{"label": route.ferries[f]["label"], "h": route.ferries[f]["duration_h"],
                         "book": bool(route.ferries[f].get("book")), "critical": bool(route.ferries[f].get("critical"))}
                        for f in st["ferries"]],
            "seasonal": [route.seasonal_roads[s]["label"] for s in d.seasonal],
            "tolls": [route.tolls[t].split(" – ")[0].split(" (")[0] for t in d.tolls if t != "autopass"],
            "gravel_km": r["gravel_km"],
            "lwh": [{"name": p.name, "likely": p.lwh_conf == "likely"}
                    for p in {p.name: p for p in d.points if p.lwh}.values()],
            "overnight": on.name if on else "", "overnight_type": d.overnight_type,
            "notes": d.notes, "transit": d.transit, "description": d.description,
            "sights": [{"name": p.name, "notes": p.notes, "lat": round(p.lat, 5), "lon": round(p.lon, 5), "lwh": p.lwh}
                       for p in {p.name: p for p in d.points if p.type == "poi"}.values()],
            "max_lat": round(max_lat, 2),
            "midnight_sun": bool(on and midnight_sun(on.lat, date)),
            "fuel_gap": r["max_fuel_gap_km"],
            "gpx": d.filename, "shared": own is not None and d.id not in own,
            "alt": {"file": alt.filename, "km": row_by[alt.id]["km"], "h": row_by[alt.id]["riding_h"],
                    "title": alt.title, "notes": alt.notes, "description": alt.description} if alt else None,
        })

    sc = None
    if shortcut:   # alternative ending: dashed on the map (alternatives layer), callout in the road book
        sdays, srow = shortcut["days"], {r["yaml_id"]: r for r in shortcut["rows"]}
        for d in sdays:
            for part in stats[d.id]["routed"]["parts"]:
                if part["kind"] == "ferry":
                    continue
                for leg in part["legs"]:
                    lines.append({"day": "Shortcut " + d.label, "kind": "land", "alt": True, "color": "#868e96",
                                  "gravel": False, "c": _decimate(leg["coords"])})
        sc = {"title": shortcut["meta"]["title"], "notes": shortcut["meta"].get("notes", ""),
              "from": sdays[0].label, "saved": shortcut["saved"], "n_replaced": len(shortcut["replaced"]),
              "replaced_km": shortcut["replaced_km"], "km": sum(srow[d.id]["km"] for d in sdays),
              "home": srow[sdays[-1].id]["date"],
              "days": [{"label": d.label, "title": d.title, "km": srow[d.id]["km"], "h": srow[d.id]["riding_h"],
                        "ferries": [route.ferries[f]["label"] for f in stats[d.id]["ferries"]],
                        "file": d.filename, "description": d.description} for d in sdays]}

    points, seen = [], set()
    labels = {d.id: d.label for d in days + alt_days}
    sc_days = shortcut["days"] if shortcut else []
    labels.update({d.id: "Shortcut " + d.label for d in sc_days})
    for d in days + alt_days + sc_days:
        for p in day_waypoints(d) + [p for p in d.points if p.lwh]:
            if p.key in seen or p.type in ("ferry_start", "ferry_end") and not p.lwh:
                continue
            seen.add(p.key)
            points.append({"lat": round(p.lat, 5), "lon": round(p.lon, 5), "name": p.name, "type": p.type,
                           "lwh": p.lwh, "likely": p.lwh_conf == "likely", "day": labels[d.id],
                           "notes": p.notes, "alt": d.is_alt or d in sc_days})

    fd = ferry_days(days)
    ferries = [{"label": route.ferries[k]["label"], "operator": route.ferries[k]["operator"],
                "h": route.ferries[k]["duration_h"], "booking": booking(route.ferries[k]).replace("**", ""),
                "critical": bool(route.ferries[k].get("critical")), "days": v} for k, v in fd.items()]
    used = {s for d in days for s in d.seasonal}
    seasonal = [{"label": sr["label"], "typical": sr["typical"], "verify": sr.get("verify", "vegvesen.no"),
                 "days": [d.label for d in days if k in d.seasonal]}
                for k, sr in route.seasonal_roads.items() if k in used]
    used_t = {t for d in days for t in d.tolls}
    tolls = [txt for k, txt in route.tolls.items() if k in used_t or k == "autopass"] + [CZ_PL_DE_TOLLS]
    gaps = sorted(((r["max_fuel_gap_km"] or 0, r["day"]) for r in rows), reverse=True)[:5]

    start, end = trip_date(route, days[0]), trip_date(route, days[-1])
    top = max(days, key=lambda d: max((p.lat for p in d.points), default=0))
    north = max(top.points, key=lambda p: p.lat)
    return {
        "title": title, "start": start.isoformat() if start else "", "end": end.isoformat() if end else "",
        "bike": route.meta.get("bike", ""), "home": route.meta.get("start", ""),
        "total_km": sum(r["km"] for r in rows), "hours": round(sum(r["riding_h"] for r in rows)),
        "n_days": len(days), "buffer_days": buffer_days, "trip_days": len(days) + buffer_days,
        "n_ferries": sum(len(d["ferries"]) for d in out_days),
        "north": {"name": north.name, "lat": north.lat, "fmt": _fmt_lat(north.lat), "day": top.label},
        "arctic": ARCTIC_CIRCLE, "chapters": chapters, "days": out_days, "lines": lines, "points": points,
        "profile": profile, "ferries": ferries, "seasonal": seasonal, "tolls": tolls,
        "wild": [{"country": c, "text": t} for c, t in WILD_CAMPING],
        "fuel": {"max": fuel.MAX_GAP_KM, "top": [{"day": d, "km": k} for k, d in gaps]},
        "open": open_questions(route, days), "hours_factor": HOURS_FACTOR, "repo": repo, "shortcut": sc,
        "lede": lede or "",
        "generated": dt.date.today().isoformat(),
        "basemap": basemap.load(),
    }


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def page(head: str, body: str, lang: str = "en") -> str:
    return (f'<!doctype html>\n<html lang="{lang}"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            f"{head}</head><body>\n{body}</body></html>\n")


ARTIFACT_FILE = CACHE / "artifact_itinerary.html"


def _tabs(site: dict, up: str, suffix: str, tr=lambda s: s) -> list[dict]:
    """Tab links from a page `up` levels below the site root (e.g. "../") to each variant's page."""
    return [{"label": tr(t["label"]), "href": up + t["dir"] + suffix or "./", "active": t["dir"] == site.get("dir", "")}
            for t in site.get("tabs", [])]


def write_all(route: Route, days, alt_days, stats, rows, alt_rows, out_dir: Path, title: str, buffer_days: int,
              shortcut: dict | None = None, site: dict | None = None):
    """`site`: {"tabs": [{label, dir}], "dir": this variant's folder under out/ ("" = root), "own": day ids with
    GPX files in this folder (None = all), "lede": intro text, "artifact": write the claude.ai copy}."""
    site = site or {}
    data = trip_data(route, days, alt_days, stats, rows, alt_rows, title, buffer_days, shortcut,
                     site.get("own"), site.get("lede"))
    up = "../" * site.get("dir", "").count("/")   # from this variant's folder back to the site root
    tabs_html = "".join(f'<a href="{html.escape(t["href"])}">{html.escape(t["label"])}</a>'
                        for t in _tabs(site, up, "map.html") if not t["active"])
    h = MAP_PAGE[0].replace("__TITLE__", html.escape(title)).replace("__SHARED_CSS__", SHARED_CSS)
    b = (MAP_PAGE[1].replace("__DATA__", _json(data)).replace("__MAP_JS__", MAP_JS)
         .replace("__UI__", _json(UI["en"])).replace("__TABS__", tabs_html))
    (out_dir / "map.html").write_text(page(h, b), encoding="utf-8")
    (out_dir / "index.html").write_text(
        render_itinerary(data, "en", {"gpx": "days/", "shared": up + "days/", "lang": "cs/", "map": "map.html",
                                      "tabs": _tabs(site, up, "")}), encoding="utf-8")
    (out_dir / "cs").mkdir(exist_ok=True)
    tr = load_translations("cs")
    (out_dir / "cs" / "index.html").write_text(
        render_itinerary(translate(data, tr), "cs",
                         {"gpx": "../days/", "shared": "../" + up + "days/", "lang": "../", "map": "../map.html",
                          "tabs": _tabs(site, "../" + up, "cs/", tr)}), encoding="utf-8")
    base = (route.meta.get("site_url") or "").rstrip("/")
    if base and site.get("artifact") and not TET_BUILD:   # claude.ai artifact copy: links go to the Pages site
        ARTIFACT_FILE.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT_FILE.write_text(artifact_body(render_itinerary(
            data, "en", {"gpx": f"{base}/days/", "shared": f"{base}/days/", "lang": f"{base}/cs/",
                         "map": f"{base}/map.html", "tabs": _tabs(site, f"{base}/", ""), "external": True})),
            encoding="utf-8")


LEAFLET_CSS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"


def artifact_body(doc: str) -> str:
    """Itinerary without the document skeleton (the artifact host adds its own) and with Leaflet's CSS inlined
    (the artifact sandbox only loads stylesheets from Google Fonts)."""
    head = doc.split("<head>", 1)[1].split("</head>", 1)[0]
    head = "\n".join(l for l in head.splitlines() if not l.startswith("<meta "))
    body = doc.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    css_file = CACHE / "leaflet-1.9.4.min.css"
    if not css_file.exists():
        r = requests.get(LEAFLET_CSS, headers={"User-Agent": USER_AGENT}, timeout=60)
        r.raise_for_status()
        css_file.write_text(r.text, encoding="utf-8")
    tag = f'<link rel="stylesheet" href="{LEAFLET_CSS}">'
    return (head + body).replace(tag, "<style>/* Leaflet 1.9.4 */\n" + css_file.read_text(encoding="utf-8")
                                 + "\n</style>")


# ------------------------------------------------------------------ shared CSS / JS
LIBS = """<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Barlow:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
"""

SHARED_CSS = """
/* Nordic road atlas: cool birch-grey paper, fjord ink, midnight-sun amber for the Arctic. */
:root{
  --bg:#eef2f4; --surface:#ffffff; --ink:#14212b; --muted:#5a6a75; --line:#d3dce1;
  --fjord:#1d5f7a; --sun:#b86e00; --sun-soft:rgba(232,154,20,.16); --ferry:#2a66c4; --gravel:#8a5a2b;
  --map-land:#e3e7df; --map-sea:#c6dae4; --map-border:#aab6b0; --casing:#ffffff; --shield:#1f7a3a; --shield-ink:#ffffff;
  --display:"Barlow Condensed","Arial Narrow",sans-serif; --body:"Barlow",system-ui,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0d151b; --surface:#15212a; --ink:#e3eaee; --muted:#93a3ae; --line:#27353f;
  --fjord:#6fb3cf; --sun:#f0ae3c; --sun-soft:rgba(240,174,60,.14); --ferry:#86aef2; --gravel:#d29d68;
  --map-land:#1b2730; --map-sea:#0e1c25; --map-border:#3a4a55; --casing:#0d151b; --shield:#2f9a52; --shield-ink:#ffffff;
  color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0d151b; --surface:#15212a; --ink:#e3eaee; --muted:#93a3ae; --line:#27353f;
  --fjord:#6fb3cf; --sun:#f0ae3c; --sun-soft:rgba(240,174,60,.14); --ferry:#86aef2; --gravel:#d29d68;
  --map-land:#1b2730; --map-sea:#0e1c25; --map-border:#3a4a55; --casing:#0d151b; --shield:#2f9a52; --shield-ink:#ffffff;
  color-scheme:dark}
html,body{background:var(--bg);color:var(--ink)}
body{font:16px/1.5 var(--body);margin:0}
.leaflet-container{background:var(--map-sea);font:13px/1.4 var(--body)}
.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:var(--surface);color:var(--ink)}
.leaflet-popup-content b{font-family:var(--display);font-size:16px;font-weight:600}
.leaflet-tooltip{background:var(--surface);color:var(--ink);border-color:var(--line)}
.leaflet-bar a,.leaflet-control-layers{background:var(--surface);color:var(--ink);border-color:var(--line)}
.leaflet-control-attribution{background:color-mix(in srgb,var(--surface) 80%,transparent)!important;color:var(--muted)}
.leaflet-control-attribution a{color:var(--fjord)}
.ov{display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--surface);
  border:2px solid var(--c);color:var(--ink);font:600 11px/1 var(--mono);box-shadow:0 1px 3px rgba(0,0,0,.3);transition:all .15s}
.z-lo .ov{width:9px;height:9px;font-size:0;border-width:2px}
.lwh{color:var(--sun);font-size:17px;line-height:1;text-shadow:0 0 2px var(--casing),0 0 2px var(--casing)}
.z-lo .lwh{font-size:11px}
.tiles-dark{filter:invert(1) hue-rotate(180deg) brightness(.92) contrast(.88) saturate(.6)}
.map-reset[hidden]{display:none}
.map-reset button{appearance:none;border:0;border-radius:2px;cursor:pointer;background:var(--surface);color:var(--fjord);
  padding:6px 10px;font:600 13px var(--body)}
.map-reset button:hover{background:var(--bg)}
.map-note{position:absolute;z-index:500;left:50%;transform:translateX(-50%);bottom:8px;background:var(--surface);
  color:var(--muted);border:1px solid var(--line);border-radius:6px;padding:2px 8px;font-size:12px}
:focus-visible{outline:2px solid var(--fjord);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
"""

MAP_JS = r"""
function tripMap(el, D, opts){
  opts = opts || {};
  const t = opts.t || {}, num = opts.num || (x => x);
  const root = document.documentElement;
  const tok = n => getComputedStyle(root).getPropertyValue(n).trim();
  const isDark = () => root.dataset.theme === 'dark' ||
    (root.dataset.theme !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
  const map = L.map(el, {zoomSnap:.25, zoomDelta:.5, preferCanvas:true, scrollWheelZoom:opts.wheel !== false,
                         attributionControl:true, minZoom:3, maxZoom:18});
  map.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>');
  map.createPane('base').style.zIndex = 150;   // below the tile pane (200): tiles cover it when they load
  const R = L.canvas({padding:.5, pane:'base'});
  const ll = rings => rings.map(r => r.map(p => [p[1], p[0]]));
  const land = D.basemap.countries.flatMap(c => c.polys.map(ll));
  const lakes = D.basemap.lakes.flatMap(c => c.polys.map(ll));
  const base = L.layerGroup().addTo(map);
  function drawBase(){
    base.clearLayers();
    for (const p of land) L.polygon(p, {renderer:R, color:tok('--map-border'), weight:.8, fillColor:tok('--map-land'), fillOpacity:1, interactive:false}).addTo(base);
    for (const p of lakes) L.polygon(p, {renderer:R, stroke:false, fillColor:tok('--map-sea'), fillOpacity:1, interactive:false}).addTo(base);
  }
  drawBase();
  map.attributionControl.addAttribution('Basemap: Natural Earth');
  // Detailed tiles on top when they load; on a blocked/offline host the offline basemap stays.
  let tiles = null, tileOk = 0, tileErr = 0;
  function addTiles(){
    if (tiles) map.removeLayer(tiles);
    tileOk = tileErr = 0;
    tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      {maxZoom:19, className:isDark() ? 'tiles-dark' : '', attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'});
    tiles.on('tileload', () => tileOk++);
    tiles.on('tileerror', () => {
      if (++tileErr >= 4 && tileOk === 0) {
        map.removeLayer(tiles); tiles = null;
        if (!el.querySelector('.map-note')) {
          const n = document.createElement('div'); n.className = 'map-note';
          n.textContent = t.m_no_tiles;
          el.appendChild(n);
        }
      }
    });
    if (opts.tiles !== false) tiles.addTo(map);
  }
  addTiles();

  const groups = {}, lines = [], all = L.featureGroup().addTo(map), altG = L.featureGroup();
  for (const f of D.lines) {
    const g = f.alt ? altG : all;
    let style;
    if (f.kind === 'ferry') style = {color:tok('--ferry'), weight:2.5, dashArray:'5 6', opacity:.95};
    else if (f.gravel) style = {color:tok('--gravel'), weight:4, dashArray:'2 5', opacity:1};
    else style = {color:f.color, weight:f.alt ? 3 : 3.5, opacity:f.alt ? .8 : .95, dashArray:f.alt ? '1 6' : null};
    const casing = f.kind === 'land' && !f.alt ? L.polyline(f.c, {color:tok('--casing'), weight:6.5, opacity:.9, interactive:false}).addTo(g) : null;
    const l = L.polyline(f.c, style).addTo(g);
    const d = D.days.find(x => x.label === f.day);
    l.bindTooltip(f.kind === 'ferry' ? t.m_ferry + ' · ' + f.label
      : d ? `<b>${d.label}</b> ${d.title}<br>${num(d.km)} km · ≈${num(d.h)} h` : `${f.day} (${t.m_fallback_tip})`, {sticky:true});
    if (d) l.on('click', () => focusDay(d.label));
    (groups[f.day] = groups[f.day] || []).push(l);
    lines.push({l, casing, f, style});
  }
  const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const dayOf = Object.fromEntries(D.days.map(d => [d.label, d]));
  const markers = {};   // "lat,lon" -> {m, g}: lets the road book open a waypoint's popup
  for (const p of D.points) {
    const g = p.alt ? altG : all;
    const pop = `<b>${esc(p.name)}</b><br>${p.day}${p.type === 'overnight' ? ' · ' + t.m_overnight : ''}` +
      (p.lwh ? ' · ' + (p.likely ? t.m_lwh_likely : t.m_lwh) : '') + (p.notes ? '<br>' + esc(p.notes) : '');
    let m;
    if (p.type === 'overnight' && !p.alt) {
      const d = dayOf[p.day];
      m = L.marker([p.lat, p.lon], {icon:L.divIcon({className:'', html:`<span class="ov" style="--c:${d ? d.color : '#888'}">${d ? d.num : ''}</span>`, iconSize:[20,20], iconAnchor:[10,10]}),
                                    zIndexOffset:500, title:`${p.day}: ${p.name}`});
    } else if (p.lwh) {
      m = L.marker([p.lat, p.lon], {icon:L.divIcon({className:'', html:`<span class="lwh">${p.likely ? '☆' : '★'}</span>`, iconSize:[18,18], iconAnchor:[9,9]}),
                                    title:p.name});
    } else {
      m = L.circleMarker([p.lat, p.lon], {radius:3.5, color:tok('--casing'), weight:1.5, fillColor:tok('--muted'), fillOpacity:1});
    }
    m.bindPopup(pop).addTo(g);
    markers[p.lat + ',' + p.lon] = {m, g};
  }
  const overlays = {[t.m_trip]:all, [t.m_fallback]:altG};
  const ctl = L.control.layers(null, overlays, {collapsed:true, position:'topleft'}).addTo(map);
  if (tiles) ctl.addOverlay(tiles, t.m_detail);
  const pad = () => ({paddingTopLeft:[24, 24], paddingBottomRight:[(opts.padRight ? opts.padRight() : 0) + 24, 24]});
  const zoomClass = () => el.classList.toggle('z-lo', map.getZoom() < 6);
  map.on('zoomend', zoomClass);
  let current = null;
  // "Whole trip" button: visible whenever a day is selected (clicking the selected day again, or Esc, also resets)
  const Reset = L.Control.extend({options:{position:'topright'}, onAdd(){
    const box = L.DomUtil.create('div', 'leaflet-bar map-reset');
    const b = L.DomUtil.create('button', '', box);
    b.type = 'button'; b.textContent = t.m_reset || 'Whole trip'; box.hidden = true;
    L.DomEvent.disableClickPropagation(box);
    b.onclick = () => focusDay(null);
    return box;
  }});
  const reset = new Reset().addTo(map);
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && current) focusDay(null); });
  function restyle(){
    for (const x of lines) {
      const on = !current || x.f.day === current;
      x.l.setStyle({opacity: on ? (x.style.opacity) : .22, weight: x.style.weight + (current && x.f.day === current ? 2 : 0)});
      if (x.casing) x.casing.setStyle({opacity: on ? .9 : .15, weight: current && x.f.day === current ? 9 : 6.5});
    }
  }
  function select(label){
    current = label || null;
    restyle();
    reset.getContainer().hidden = !current;
    if (opts.onFocus) opts.onFocus(current);
  }
  function focusDay(label){
    if (label && label === current) label = null;   // second click on the selected day shows the whole trip
    select(label);
    if (label && groups[label]) map.flyToBounds(L.featureGroup(groups[label]).getBounds(), {...pad(), maxZoom:10, duration:.6});
    else map.flyToBounds(all.getBounds(), {...pad(), duration:.6});
  }
  function focusPoint(lat, lon, label){
    const x = markers[lat + ',' + lon];
    if (label) select(label);
    if (x && !map.hasLayer(x.g)) map.addLayer(x.g);
    map.flyTo([lat, lon], Math.max(map.getZoom(), 11), {duration:.6});
    if (x) map.once('moveend', () => x.m.openPopup());
  }
  map.fitBounds(all.getBounds(), pad());
  zoomClass();
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { drawBase(); addTiles(); });
  new MutationObserver(() => { drawBase(); addTiles(); }).observe(root, {attributes:true, attributeFilter:['data-theme']});
  return {map, focusDay, focusPoint};
}
"""

# ------------------------------------------------------------------ map.html
MAP_PAGE = (r"""<title>__TITLE__ – map</title>
""" + LIBS + r"""<style>__SHARED_CSS__
html,body{height:100%;overflow:hidden}
#map{position:absolute;inset:0}
#panel{position:absolute;z-index:1000;top:12px;right:12px;bottom:12px;width:320px;display:flex;flex-direction:column;
  background:var(--surface);border:1px solid var(--line);border-radius:10px;box-shadow:0 4px 18px rgba(0,0,0,.18);overflow:hidden}
#panel header{padding:14px 16px 10px;border-bottom:1px solid var(--line)}
#panel h1{font:700 26px/1 var(--display);letter-spacing:.01em;margin:0;text-transform:uppercase}
#panel .sub{color:var(--muted);font-size:13px;margin-top:4px}
#panel .stats{display:flex;flex-wrap:wrap;gap:4px 14px;white-space:nowrap;margin-top:8px;font:500 13px var(--mono);font-variant-numeric:tabular-nums}
#list{overflow:auto;padding:6px 8px 10px;flex:1}
.ch{font:600 13px var(--display);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:12px 8px 4px;display:flex;gap:8px;align-items:center}
.ch i{width:16px;height:4px;border-radius:2px;background:var(--c)}
button.day{all:unset;box-sizing:border-box;display:grid;grid-template-columns:34px 1fr auto;gap:2px 8px;width:100%;padding:5px 8px;border-radius:6px;cursor:pointer}
button.day:hover{background:var(--bg)} button.day[aria-pressed="true"]{background:var(--sun-soft)}
button.day:focus-visible{outline:2px solid var(--fjord)}
.n{font:600 12px/1.6 var(--mono);color:var(--muted)} .t{font-size:14px;min-width:0}
.k{font:500 12px/1.6 var(--mono);color:var(--muted);font-variant-numeric:tabular-nums;text-align:right}
.dt{grid-column:2/4;font-size:12px;color:var(--muted)}
.key{border-top:1px solid var(--line);padding:8px 16px 10px;font-size:12px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 12px}
.key span{display:inline-flex;align-items:center;gap:5px}
.sw{width:18px;height:0;border-top:3px solid var(--c)} .sw.d{border-top-style:dashed}
.acts{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:6px;font-size:13px}
.acts a{color:var(--fjord)}
#all{all:unset;cursor:pointer;color:var(--fjord);font-weight:600}
@media (max-width:700px){
  #panel{top:auto;left:8px;right:8px;bottom:8px;width:auto;max-height:46%}
  #panel header{padding:10px 12px 8px} #panel h1{font-size:21px}
}
</style>""", r"""<div id="map" role="region" aria-label="Trip map"></div>
<aside id="panel">
  <header><h1 id="h"></h1><div class="sub" id="sub"></div><div class="stats" id="stats"></div>
  <div class="acts"><button id="all" type="button">Show the whole trip</button><a href="index.html">Itinerary</a><a href="cs/">Itinerář česky</a>__TABS__</div></header>
  <div id="list"></div>
  <div class="key"><span><i class="sw" style="--c:var(--ink)"></i>day route</span><span><i class="sw d" style="--c:var(--ferry)"></i>ferry</span>
  <span><i class="sw d" style="--c:var(--gravel)"></i>TET gravel</span><span>● overnight (day no.)</span><span style="color:var(--sun)">★ Long Way Home location (☆ likely)</span></div>
</aside>
<script>const D = __DATA__; const U = __UI__;</script>
<script>__MAP_JS__</script>
<script>
const fmtD = s => s ? new Date(s + 'T12:00:00').toLocaleDateString('en-GB', {weekday:'short', day:'numeric', month:'short'}) : '';
document.getElementById('h').textContent = D.title;
document.getElementById('sub').textContent = `${fmtD(D.start)} – ${fmtD(D.end)} ${D.start.slice(0,4)} · ${D.home} and back`;
document.getElementById('stats').innerHTML = `<span>${D.total_km.toLocaleString('en-GB')} km</span><span>${D.n_days} days</span><span>${D.n_ferries} ferries</span><span>${D.north.fmt}</span>`;
const panel = document.getElementById('panel');
const wide = () => matchMedia('(min-width:701px)').matches;
const list = document.getElementById('list');
const btns = {};
const T = tripMap(document.getElementById('map'), D, {t:U, padRight: () => wide() ? panel.offsetWidth + 12 : 0,
  onFocus: label => { for (const [k, b] of Object.entries(btns)) b.setAttribute('aria-pressed', k === label); }});
D.chapters.forEach(ch => {
  const h = document.createElement('div'); h.className = 'ch'; h.style.setProperty('--c', ch.color);
  h.innerHTML = '<i></i>'; h.append(ch.name); list.append(h);
  for (const lab of ch.days) {
    const d = D.days.find(x => x.label === lab);
    const b = document.createElement('button'); b.type = 'button'; b.className = 'day'; b.setAttribute('aria-pressed', 'false');
    b.innerHTML = `<span class="n">${d.num}</span><span class="t"></span><span class="k">${d.km} km</span><span class="dt">${fmtD(d.date)}${d.ferries.length ? ' · ferry' : ''}${d.midnight_sun ? ' · midnight sun' : ''}</span>`;
    b.querySelector('.t').textContent = d.title;
    b.onclick = () => T.focusDay(b.getAttribute('aria-pressed') === 'true' ? null : d.label);
    btns[d.label] = b; list.append(b);
  }
});
document.getElementById('all').onclick = () => T.focusDay(null);
</script>
""")

# ------------------------------------------------------------------ index.html (itinerary), en + cs
UI = {
    "en": {
        "locale": "en-GB",
        "lat_fmt": "{d}°{m}′N",
        "how_far": "How far north",
        "how_far_sub": "Latitude along the route, day by day. Above the dashed line you are inside the Arctic Circle; "
                       "numbers mark where each riding day ends.",
        "route": "The route",
        "route_sub": "Click a line, a day or a place below to zoom in; “Show whole trip” (or Esc) zooms back out. "
                     "Numbered circles are overnight stops.",
        "full_map": "Open the full-screen map",
        "days": "Day by day",
        "days_sub": "Distances and riding times come from a routed track (router time × {f}); stops and ferries are "
                    "extra. Each day has a GPX with the Kurviger route, the track and the waypoints.",
        "prep": "Before you go",
        "ferries": "Ferries", "th": ["Crossing", "Operator", "≈ h", "Book", "Day"],
        "seasonal": "Seasonal roads",
        "seasonal_sub": "Check opening status on vegvesen.no (and the ferry operator) shortly before departure.",
        "tolls": "Tolls", "fuel": "Fuel", "wild": "Wild camping", "open": "Still to do",
        "eyebrow": "Solo · {bike} · {home} → Nordkapp → {home}",
        "f_km": "km on the road", "f_days": "riding days + {n} spare", "f_days0": "riding days, no spare",
        "sc_head": "Running late? Fast way home:",
        "sc_text": "from here straight home in {n} days instead of {m} ({km} km instead of {km0} km), home on {date} – {saved} days earlier.", "f_ferries": "ferry crossings",
        "f_north": "{name}, day {num}", "f_hours": "hours in the saddle",
        "lede": "Through Denmark, the Swedish west coast and the Norwegian fjords, up the coast to Lofoten, Andøya, "
                "Senja and Nordkapp, down through Sámi Lapland and the Finnish lakes, across the Gulf of Finland and "
                "home through the Baltic states and Poland.",
        "arctic": "Arctic Circle", "day_ends": "day ends ▸ {km} km in total",
        "profile_aria": "Latitude along the route, from {a} to {b} at {name}",
        "legend_ferry": "Ferry", "legend_lwh": "★ Long Way Home location (☆ likely)",
        "range_many": "Days {a}–{b}", "range_one": "Day {a}",
        "chip_ferry": "Ferry", "book_early": "book early", "book": "book",
        "chip_seasonal": "Seasonal", "chip_toll": "Toll", "chip_gravel": "Gravel",
        "chip_sun": "Midnight sun", "sun_text": "the sun stays up at the overnight stop",
        "chip_transit": "Transit", "transit_text": "motorway day",
        "likely": "likely", "gpx": "Download GPX",
        "fallback": "Alternative:", "sights": "Along the way",
        "riding": "riding", "on_ferries": "on ferries", "fuel_gap": "longest fuel gap",
        "day_word": "DAY", "show_map": "Show on map",
        "stay": {"wild camp": "Wild camp", "campsite cabin": "Cabin", "hotel": "Hotel", "home": "Home",
                 "ferry cabin": "Night ferry",
                 "_": "Overnight"},
        "fuel_text": "No day has more than {max} km between fuel stations on the route. Longest gaps: {list}. "
                     "Fill up whenever you can in Finnmark and Lapland.",
        "footer": "Routes computed with BRouter (car-fast, ferries blocked) on OpenStreetMap data; final curvy "
                  "routing in Kurviger. Basemap: Natural Earth; map tiles © OpenStreetMap contributors. Built {date}",
        "source": "source code and data", "verify": "check",
        "other_lang": "Česky", "tabs_aria": "Route variants",
        # map
        "m_ferry": "Ferry", "m_overnight": "overnight", "m_lwh": "Long Way Home location",
        "m_lwh_likely": "Long Way Home location (likely)", "m_trip": "Trip",
        "m_fallback": "Alternative routes", "m_fallback_tip": "alternative route", "m_reset": "Show whole trip",
        "m_detail": "Detailed map (OpenStreetMap)",
        "m_no_tiles": "Detailed map tiles unavailable here – showing the offline basemap",
    },
    "cs": {
        "locale": "cs-CZ",
        "lat_fmt": "{d}°{m}′ s. š.",
        "how_far": "Jak daleko na sever",
        "how_far_sub": "Zeměpisná šířka podél trasy den po dni. Nad přerušovanou čarou jste za polárním kruhem; "
                       "čísla ukazují, kde který den končí.",
        "route": "Trasa",
        "route_sub": "Kliknutím na čáru, den nebo místo níže mapu přiblížíte; tlačítko „Celá cesta“ (nebo Esc) ji "
                     "zase oddálí. Očíslovaná kolečka jsou místa noclehů.",
        "full_map": "Otevřít mapu na celou obrazovku (anglicky)",
        "days": "Den po dni",
        "days_sub": "Vzdálenosti a časy jízdy pocházejí z naplánované trasy (čas z plánovače × {f}); zastávky a "
                    "trajekty jsou navíc. Ke každému dni je GPX s trasou pro Kurviger, záznamem trasy a body zájmu.",
        "prep": "Před cestou",
        "ferries": "Trajekty", "th": ["Přejezd", "Dopravce", "≈ h", "Rezervace", "Den"],
        "seasonal": "Sezonní silnice",
        "seasonal_sub": "Krátce před odjezdem ověřte, zda jsou otevřené, na vegvesen.no (a u provozovatele trajektu).",
        "tolls": "Mýto", "fuel": "Palivo", "wild": "Spaní v přírodě", "open": "Zbývá zařídit",
        "eyebrow": "Sólo · {bike} · {home} → Nordkapp → {home}",
        "f_km": "km na silnici", "f_days": "jízdních dnů + {n} rezervní", "f_days0": "jízdních dnů, bez rezervy",
        "sc_head": "Zpoždění? Rychlá cesta domů:",
        "sc_text": "odsud rovnou domů za {n} dny místo {m} ({km} km místo {km0} km), doma {date} – o {saved} dny dřív.", "f_ferries": "plaveb trajektem",
        "f_north": "{name}, den {num}", "f_hours": "hodin v sedle",
        "lede": "Přes Dánsko, západní pobřeží Švédska a norské fjordy, podél pobřeží na Lofoty, Andøyu, Senju a Nordkapp, "
                "dolů sámským Laponskem a kolem finských jezer, přes Finský záliv a domů přes Pobaltí a Polsko.",
        "arctic": "Polární kruh", "day_ends": "konce dnů ▸ celkem {km} km",
        "profile_aria": "Zeměpisná šířka podél trasy, od {a} po {b} u {name}",
        "legend_ferry": "Trajekt", "legend_lwh": "★ místo z Long Way Home (☆ pravděpodobné)",
        "range_many": "Dny {a}–{b}", "range_one": "Den {a}",
        "chip_ferry": "Trajekt", "book_early": "rezervovat včas", "book": "rezervovat",
        "chip_seasonal": "Sezonní", "chip_toll": "Mýto", "chip_gravel": "Šotolina",
        "chip_sun": "Půlnoční slunce", "sun_text": "v místě noclehu slunce nezapadne",
        "chip_transit": "Přesun", "transit_text": "den po dálnici",
        "likely": "pravděpodobně", "gpx": "Stáhnout GPX",
        "fallback": "Alternativa:", "sights": "Cestou",
        "riding": "jízdy", "on_ferries": "na trajektech", "fuel_gap": "nejdelší úsek bez pumpy",
        "day_word": "DEN", "show_map": "Ukázat na mapě",
        "stay": {"wild camp": "Spaní v přírodě", "campsite cabin": "Chatka v kempu", "hotel": "Hotel",
                 "home": "Doma", "ferry cabin": "Noční trajekt", "_": "Nocleh"},
        "fuel_text": "Žádný den nemá na trase mezi pumpami víc než {max} km. Nejdelší úseky: {list}. "
                     "Ve Finnmarku a v Laponsku tankujte, kdykoli to jde.",
        "footer": "Trasy spočítané v BRouteru (profil car-fast bez trajektů) nad daty OpenStreetMap; finální "
                  "zatáčkovou trasu počítá Kurviger. Podkladová mapa: Natural Earth; mapové dlaždice "
                  "© přispěvatelé OpenStreetMap. Vytvořeno {date}",
        "source": "zdrojový kód a data", "verify": "ověřte",
        "other_lang": "English", "tabs_aria": "Varianty trasy",
        # map
        "m_ferry": "Trajekt", "m_overnight": "nocleh", "m_lwh": "místo z Long Way Home",
        "m_lwh_likely": "místo z Long Way Home (pravděpodobné)", "m_trip": "Cesta",
        "m_fallback": "Alternativní trasy", "m_fallback_tip": "alternativní trasa", "m_reset": "Celá cesta",
        "m_detail": "Podrobná mapa (OpenStreetMap)",
        "m_no_tiles": "Podrobné mapové dlaždice tu nejsou dostupné – zobrazuje se offline podkladová mapa",
    },
}

HTML_KEYS = ("how_far", "how_far_sub", "route", "route_sub", "full_map", "days", "prep", "ferries", "seasonal",
             "seasonal_sub", "tolls", "fuel", "wild", "open", "other_lang", "tabs_aria")


def load_translations(lang: str):
    """Return tr(text) for `lang`: exact matches from data/i18n_<lang>.yaml, then prefix rules; else unchanged."""
    path = DATA / f"i18n_{lang}.yaml"
    if lang == "en" or not path.exists():
        return lambda s: s
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    strings, prefixes = raw.get("strings") or {}, raw.get("prefixes") or {}

    def tr(s):
        if not isinstance(s, str) or not s:
            return s
        if s in strings:
            return strings[s]
        for en, xx in prefixes.items():
            if s.startswith(en):
                return xx + s[len(en):]
        return s
    return tr


def translate(data: dict, tr) -> dict:
    d = copy.deepcopy(data)
    d["home"] = tr(d["home"])
    d["lede"] = tr(d["lede"])
    d["north"]["name"] = tr(d["north"]["name"])
    for c in d["chapters"]:
        c["name"] = tr(c["name"])
    for day in d["days"]:
        for k in ("title", "notes", "overnight", "description"):
            day[k] = tr(day[k])
        for x in day["sights"]:
            x["name"], x["notes"] = tr(x["name"]), tr(x["notes"])
        for x in day["lwh"]:
            x["name"] = tr(x["name"])
        for f in day["ferries"]:
            f["label"] = tr(f["label"])
        day["seasonal"] = [tr(s) for s in day["seasonal"]]
        day["tolls"] = [tr(s) for s in day["tolls"]]
        if day["alt"]:
            day["alt"]["title"], day["alt"]["notes"] = tr(day["alt"]["title"]), tr(day["alt"]["notes"])
            day["alt"]["description"] = tr(day["alt"]["description"])
    for f in d["lines"]:
        if "label" in f:
            f["label"] = tr(f["label"])
    for p in d["points"]:
        p["name"], p["notes"] = tr(p["name"]), tr(p["notes"])
    for f in d["ferries"]:
        f["label"], f["operator"], f["booking"] = tr(f["label"]), tr(f["operator"]), tr(f["booking"])
    for s in d["seasonal"]:
        s["label"], s["typical"], s["verify"] = tr(s["label"]), tr(s["typical"]), tr(s["verify"])
    d["tolls"] = [tr(s) for s in d["tolls"]]
    for w in d["wild"]:
        w["country"], w["text"] = tr(w["country"]), tr(w["text"])
    d["open"] = [tr(s) for s in d["open"]]
    if d.get("shortcut"):
        sc = d["shortcut"]
        sc["title"], sc["notes"] = tr(sc["title"]), tr(sc["notes"])
        for x in sc["days"]:
            x["title"], x["ferries"] = tr(x["title"]), [tr(f) for f in x["ferries"]]
            x["description"] = tr(x["description"])
    return d


def render_itinerary(data: dict, lang: str, links: dict) -> str:
    ui = UI[lang]
    head = ITINERARY_PAGE[0].replace("__SHARED_CSS__", SHARED_CSS)
    body = ITINERARY_PAGE[1]
    for k in HTML_KEYS:
        body = body.replace("{{" + k + "}}", html.escape(ui[k]))
    for i, h in enumerate(ui["th"]):
        body = body.replace("{{th%d}}" % i, html.escape(h))
    body = (body.replace("__DATA__", _json(data)).replace("__UI__", _json(ui)).replace("__LINKS__", _json(links))
            .replace("__MAP_JS__", MAP_JS))
    return page(head, body, lang)


ITINERARY_PAGE = (r"""<title>Long Way Home 2027</title>
""" + LIBS + r"""<style>__SHARED_CSS__
/* Layout: atlas page – hero with the trip's numbers, latitude profile, map, then the road book by chapter. */
.wrap{max-width:1080px;margin:0 auto;padding-inline:clamp(16px,4vw,40px)}
.topbar{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:10px 16px;padding-top:14px;font-size:14px}
.toplinks{display:flex;gap:16px;margin-left:auto}
.toplinks a{color:var(--fjord);font-weight:500}
.tabs{display:flex;flex-wrap:wrap;gap:2px 4px;border-bottom:1px solid var(--line)}
.tabs[hidden]{display:none}
.tabs a{padding:6px 12px 5px;font:600 16px/1.2 var(--display);text-transform:uppercase;letter-spacing:.04em;color:var(--muted);
  text-decoration:none;border-bottom:3px solid transparent;margin-bottom:-1px}
.tabs a:hover{color:var(--fjord)}
.tabs a[aria-current="page"]{color:var(--ink);border-bottom-color:var(--sun)}
header.hero{padding-block:clamp(16px,4vw,44px) 20px}
.eyebrow{font:500 13px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font:700 clamp(52px,10vw,112px)/.86 var(--display);text-transform:uppercase;letter-spacing:-.01em;margin:10px 0 0;text-wrap:balance}
h1 span{color:var(--sun)}
.dates{font:600 clamp(20px,3vw,28px)/1.2 var(--display);margin-top:14px;text-transform:uppercase;letter-spacing:.02em}
.facts{display:flex;flex-wrap:wrap;gap:10px 34px;margin-top:22px;padding-top:18px;border-top:2px solid var(--ink)}
.fact b{display:block;font:600 clamp(28px,4vw,40px)/1 var(--display);font-variant-numeric:tabular-nums}
.fact span{font-size:13px;color:var(--muted)}
.lede{max-width:64ch;margin-top:18px;color:var(--muted)}
h2{font:700 clamp(28px,4vw,40px)/1 var(--display);text-transform:uppercase;margin:0 0 6px;text-wrap:balance}
section{padding-block:28px}
.sec-sub{color:var(--muted);margin:0 0 16px;max-width:70ch}
.profile-box{overflow-x:auto}
.profile-box svg{display:block;width:100%;min-width:640px;height:auto}
.mapbox{position:relative;height:min(72vh,680px);min-height:380px;border:1px solid var(--line);border-radius:8px;overflow:hidden}
#map{position:absolute;inset:0}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:10px;font-size:13px;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend a{color:var(--fjord);font-weight:500}
.sw{width:18px;height:0;border-top:3px solid var(--c)} .sw.d{border-top-style:dashed}
.chapter{margin-top:34px}
.chapter-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;border-bottom:3px solid var(--c);padding-bottom:6px}
.chapter-head h3{font:700 clamp(22px,3vw,30px)/1.05 var(--display);text-transform:uppercase;margin:0;text-wrap:balance}
.chapter-head .range{font:500 13px var(--mono);color:var(--muted)}
.day{display:grid;grid-template-columns:104px minmax(0,1fr);gap:4px 22px;padding-block:18px;border-bottom:1px solid var(--line)}
.when{display:flex;flex-direction:column;gap:2px}
.when .num{font:700 34px/1 var(--display);color:var(--c)}
.when .num small{font:600 13px var(--mono);color:var(--muted);margin-left:2px;letter-spacing:.04em}
.when .date{font:500 14px var(--mono);font-variant-numeric:tabular-nums}
.body{min-width:0}
.body h4{font:600 24px/1.1 var(--display);margin:0;text-wrap:balance}
.meta{font:500 14px var(--mono);color:var(--muted);margin-top:4px;font-variant-numeric:tabular-nums}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:13px;line-height:1.2;padding:4px 9px;border-radius:4px;border:1px solid var(--line);background:var(--surface)}
.chip b{font:600 11px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.chip.ferry{border-color:color-mix(in srgb,var(--ferry) 45%,var(--line))} .chip.ferry b{color:var(--ferry)}
.chip.season{border-color:color-mix(in srgb,var(--sun) 55%,var(--line))} .chip.season b{color:var(--sun)}
.chip.sun{background:var(--sun-soft);border-color:transparent} .chip.sun b{color:var(--sun)}
.chip.gravel b{color:var(--gravel)}
.chip.crit{font-weight:600}
.lwh-line{margin-top:10px;font-size:15px}
.lwh-line .star{color:var(--sun)}
.stay{margin-top:6px;font-size:15px} .stay b{font-weight:600}
.notes{margin-top:6px;color:var(--muted);max-width:70ch;font-size:15px}
.desc{margin:8px 0 0;max-width:70ch}
.sights{margin-top:10px}
.sights h5{font:600 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 4px}
.sights ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:4px 22px;font-size:14px}
.sights li{min-width:0}
button.sight{all:unset;cursor:pointer;color:var(--fjord);font-weight:600;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}
button.sight:focus-visible{outline:2px solid var(--fjord)}
.sights .sn{color:var(--muted)}
.shortcut .desc{margin:2px 0 0;font-size:14px}
.alt{margin-top:8px;font-size:14px;padding:8px 10px;border-left:3px solid var(--sun);background:var(--sun-soft);max-width:70ch}
.links{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:10px;font-size:13px;align-items:center}
.shortcut{margin-block:18px 4px;max-width:none}
.shortcut ol{margin:8px 0 0;padding-left:22px} .shortcut li{margin-bottom:6px}
.shortcut li .links{margin-top:2px}
.links code,.alt code{font:400 12px var(--mono);color:var(--muted);overflow-wrap:anywhere}
.links a{color:var(--fjord);font-weight:500}
.btn-map{all:unset;cursor:pointer;color:var(--fjord);font-size:13px;font-weight:600;text-decoration:underline;text-underline-offset:3px}
.btn-map:focus-visible{outline:2px solid var(--fjord)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:28px}
.grid2>div{min-width:0}
.grid2>.wide{grid-column:1/-1}
.tbl{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px}
th{font:600 12px var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--muted);text-align:left;border-bottom:2px solid var(--ink);padding:6px 10px 6px 0}
td{border-bottom:1px solid var(--line);padding:7px 10px 7px 0;vertical-align:top}
td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;text-align:right}
td.crit{font-weight:600;color:var(--sun)}
ul.plain{padding-left:18px;margin:0} ul.plain li{margin-bottom:6px}
h3.small{font:700 20px var(--display);text-transform:uppercase;margin:0 0 8px}
ol.open li{margin-bottom:8px;max-width:75ch}
footer{padding-block:28px 48px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);margin-top:24px}
footer a{color:var(--fjord)}
.shield{display:inline-block;background:var(--shield);color:var(--shield-ink);font:600 12px/1 var(--mono);padding:3px 5px;border-radius:3px;vertical-align:1px}
@media (max-width:640px){
  /* ferries: one stacked row per crossing instead of a 5-column table */
  #ferries thead{display:none}
  #ferries,#ferries tbody{display:block}
  #ferries tr{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 12px;padding-block:8px;border-bottom:1px solid var(--line)}
  #ferries td{border:0;padding:0}
  #ferries td:nth-child(1){font-weight:600}
  #ferries td:nth-child(2){grid-row:2;color:var(--muted)}
  #ferries td:nth-child(3){grid-row:2;grid-column:2}
  #ferries td:nth-child(3)::after{content:" h"}
  #ferries td:nth-child(4){grid-row:3;grid-column:1/-1}
  #ferries td:nth-child(5){grid-row:1;grid-column:2;font-family:var(--mono);text-align:right}
  .day{grid-template-columns:1fr;gap:6px}
  .when{flex-direction:row;align-items:baseline;gap:12px}
  .when .num{font-size:28px}
}
</style>""", r"""<div class="wrap">
<div class="topbar"><nav class="tabs" id="tabs" aria-label="{{tabs_aria}}" hidden></nav>
<nav class="toplinks" aria-label="Language and map"><a id="lang-link" href="#">{{other_lang}}</a><a id="map-link" href="#">{{full_map}}</a></nav></div>
<header class="hero">
  <div class="eyebrow" id="eyebrow"></div>
  <h1>Long Way <span>Home</span></h1>
  <div class="dates" id="dates"></div>
  <div class="facts" id="facts"></div>
  <p class="lede" id="lede"></p>
</header>

<section aria-labelledby="lat-h">
  <h2 id="lat-h">{{how_far}}</h2>
  <p class="sec-sub">{{how_far_sub}}</p>
  <div class="profile-box" id="profile"></div>
</section>

<section aria-labelledby="map-h">
  <h2 id="map-h">{{route}}</h2>
  <p class="sec-sub">{{route_sub}}</p>
  <div class="mapbox"><div id="map" role="region" aria-labelledby="map-h"></div></div>
  <div class="legend" id="legend"></div>
</section>

<section aria-labelledby="days-h">
  <h2 id="days-h">{{days}}</h2>
  <p class="sec-sub" id="days-sub"></p>
  <div id="days"></div>
</section>

<section aria-labelledby="prep-h">
  <h2 id="prep-h">{{prep}}</h2>
  <div class="grid2">
    <div class="wide"><h3 class="small">{{ferries}}</h3><div class="tbl"><table id="ferries"><thead><tr><th>{{th0}}</th><th>{{th1}}</th><th>{{th2}}</th><th>{{th3}}</th><th>{{th4}}</th></tr></thead><tbody></tbody></table></div></div>
    <div><h3 class="small">{{seasonal}}</h3><p class="sec-sub">{{seasonal_sub}}</p><ul class="plain" id="seasonal"></ul></div>
    <div><h3 class="small">{{tolls}}</h3><ul class="plain" id="tolls"></ul></div>
    <div><h3 class="small">{{fuel}}</h3><p class="sec-sub" id="fuel"></p></div>
    <div><h3 class="small">{{wild}}</h3><ul class="plain" id="wild"></ul></div>
    <div><h3 class="small">{{open}}</h3><ol class="open" id="open"></ol></div>
  </div>
</section>

<footer id="foot"></footer>
</div>
<script>const D = __DATA__; const U = __UI__; const LINKS = __LINKS__;</script>
<script>__MAP_JS__</script>
<script>
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fill = (s, o) => s.replace(/\{(\w+)\}/g, (m, k) => k in o ? o[k] : m);
const dt = s => new Date(s + 'T12:00:00');
const fmt = (s, o) => s ? dt(s).toLocaleDateString(U.locale, o) : '';
const n = x => Number(x).toLocaleString(U.locale);
const lat = v => fill(U.lat_fmt, {d: Math.floor(v), m: String(Math.round((v - Math.floor(v)) * 60)).padStart(2, '0')});
const DAY = {weekday:'short', day:'numeric', month: U.locale === 'cs-CZ' ? 'long' : 'short'};
const SHORT = {day:'numeric', month: U.locale === 'cs-CZ' ? 'long' : 'short'};
// Road numbers → small green shields (E6, E10, Rv55, Fv63 …)
const roads = s => esc(s).replace(/\b(E ?\d{1,3}|Rv ?\d{1,3}|Fv ?\d{2,4}|A ?\d{1,2}|S ?\d{1,2}|D ?\d{1,2})\b(?![\d.,])/g,
  m => `<span class="shield">${m.replace(' ', '')}</span>`);

$('lang-link').href = LINKS.lang;
$('map-link').href = LINKS.map;
if (LINKS.tabs && LINKS.tabs.length > 1) {   // route variants (e.g. home via Finland & the Baltics / via Sweden)
  $('tabs').innerHTML = LINKS.tabs.map(t => `<a href="${esc(t.href)}"${t.active ? ' aria-current="page"' : ''}>${esc(t.label)}</a>`).join('');
  $('tabs').hidden = false;
}
if (LINKS.external) for (const a of document.querySelectorAll('.topbar a')) { a.target = '_blank'; a.rel = 'noopener'; }
$('eyebrow').textContent = fill(U.eyebrow, {bike: D.bike, home: D.home});
$('dates').textContent = `${fmt(D.start, {day:'numeric', month:'long'})} – ${fmt(D.end, {day:'numeric', month:'long', year:'numeric'})}`;
$('facts').innerHTML = [
  [n(D.total_km), U.f_km], [D.n_days, D.buffer_days ? fill(U.f_days, {n: D.buffer_days}) : U.f_days0], [D.n_ferries, U.f_ferries],
  [lat(D.north.lat), fill(U.f_north, {name: esc(D.north.name), num: +D.north.day.slice(1)})], ['≈' + D.hours, U.f_hours]]
  .map(([b, s]) => `<div class="fact"><b>${b}</b><span>${s}</span></div>`).join('');
$('lede').textContent = D.lede || U.lede;

// ---- latitude profile
(function(){
  const W = 1000, H = 250, L0 = 46, R0 = 16, T0 = 26, B0 = 40;
  const P = D.profile, maxKm = P[P.length - 1][0];
  const lo = 48, hi = 72;
  const x = k => L0 + (W - L0 - R0) * k / maxKm, y = v => T0 + (H - T0 - B0) * (hi - v) / (hi - lo);
  const line = P.map((p, i) => (i ? 'L' : 'M') + x(p[0]).toFixed(1) + ' ' + y(p[1]).toFixed(1)).join('');
  const area = line + `L${x(maxKm)} ${y(lo)}L${x(0)} ${y(lo)}Z`;
  const ac = y(D.arctic);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(fill(U.profile_aria, {a: lat(P[0][1]), b: lat(D.north.lat), name: D.north.name}))}">`;
  s += `<defs><clipPath id="above"><rect x="0" y="0" width="${W}" height="${ac}"/></clipPath>
    <linearGradient id="lg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--fjord)" stop-opacity=".28"/><stop offset="1" stop-color="var(--fjord)" stop-opacity=".04"/></linearGradient></defs>`;
  for (const v of [50, 55, 60, 65, 70]) s += `<line x1="${L0}" x2="${W - R0}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)" stroke-width="1"/><text x="${L0 - 6}" y="${y(v) + 4}" text-anchor="end" font-size="11" font-family="var(--mono)" fill="var(--muted)">${v}°</text>`;
  s += `<path d="${area}" fill="url(#lg)"/>`;
  s += `<path d="${area}" fill="var(--sun)" fill-opacity=".28" clip-path="url(#above)"/>`;
  s += `<path d="${line}" fill="none" stroke="var(--fjord)" stroke-width="2" stroke-linejoin="round"/>`;
  s += `<path d="${line}" fill="none" stroke="var(--sun)" stroke-width="2.4" stroke-linejoin="round" clip-path="url(#above)"/>`;
  s += `<line x1="${L0}" x2="${W - R0}" y1="${ac}" y2="${ac}" stroke="var(--sun)" stroke-width="1.2" stroke-dasharray="5 4"/>`;
  s += `<text x="${W - R0}" y="${ac - 6}" text-anchor="end" font-size="12" font-family="var(--mono)" fill="var(--sun)">${esc(U.arctic)} ${lat(D.arctic)}</text>`;
  let lastX = -99;
  for (const d of D.days) {
    const xx = x(d.end_km);
    s += `<line x1="${xx}" x2="${xx}" y1="${H - B0}" y2="${H - B0 + 5}" stroke="var(--muted)"/>`;
    if (xx - lastX >= 17) { s += `<text x="${xx}" y="${H - B0 + 18}" text-anchor="middle" font-size="11" font-family="var(--mono)" fill="var(--muted)">${d.num}</text>`; lastX = xx; }
  }
  s += `<line x1="${L0}" x2="${W - R0}" y1="${H - B0}" y2="${H - B0}" stroke="var(--ink)" stroke-width="1.5"/>`;
  s += `<text x="${L0}" y="${H - 6}" font-size="11" font-family="var(--mono)" fill="var(--muted)">${esc(fill(U.day_ends, {km: n(maxKm.toFixed(0))}))}</text>`;
  const top = P.reduce((a, b) => b[1] > a[1] ? b : a);
  s += `<circle cx="${x(top[0])}" cy="${y(top[1])}" r="4" fill="var(--sun)" stroke="var(--casing)" stroke-width="1.5"/>`;
  s += `<text x="${x(top[0]) + 8}" y="${y(top[1]) + 4}" font-size="13" font-weight="600" font-family="var(--body)" fill="var(--ink)">${esc(D.north.name)} ${lat(D.north.lat)}</text>`;
  s += `<text x="${x(0) + 4}" y="${y(P[0][1]) - 8}" font-size="12" font-family="var(--body)" fill="var(--ink)">${esc(D.home.split(',')[0])}</text>`;
  $('profile').innerHTML = s + '</svg>';
})();

// ---- map + legend
const T = tripMap($('map'), D, {t:U, num:n});
$('legend').innerHTML = D.chapters.map(c => `<span><i class="sw" style="--c:${c.color}"></i>${esc(c.name)}</span>`).join('') +
  `<span><i class="sw d" style="--c:var(--ferry)"></i>${esc(U.legend_ferry)}</span><span style="color:var(--sun)">${esc(U.legend_lwh)}</span>`;

// ---- day by day
$('days-sub').textContent = fill(U.days_sub, {f: n(D.hours_factor)});
// on the site the file downloads; inside a sandboxed viewer (artifact) it opens from the site in a new tab
const gpxLink = (f, base = LINKS.gpx) => `<a href="${esc(base + f)}" ${LINKS.external ? 'target="_blank" rel="noopener"' : 'download'}>${esc(U.gpx)}</a> <code>${esc(f)}</code>`;
// alternative ending (e.g. Via Baltica straight home): its GPX files live in shortcut/days/ next to days/
const SC = D.shortcut, scBase = LINKS.gpx.replace(/days\/$/, 'shortcut/days/');
const shortcutBox = () => `<div class="alt shortcut"><b>${esc(U.sc_head)}</b> ${esc(fill(U.sc_text, {n: SC.days.length,
  m: SC.n_replaced, km: n(SC.km), km0: n(SC.replaced_km), date: fmt(SC.home, SHORT), saved: SC.saved}))} ${roads(SC.notes)}
  <ol>${SC.days.map(x => `<li><b>${esc(x.title)}</b> – ${n(x.km)} km, ≈${n(x.h)} h${x.ferries.length ? ' · ' + x.ferries.map(esc).join(', ') : ''}
  ${x.description ? `<p class="desc">${roads(x.description)}</p>` : ''}<div class="links">${gpxLink(x.file, scBase)}</div></li>`).join('')}</ol></div>`;
let out = '';
D.chapters.forEach(ch => {
  const ds = ch.days.map(l => D.days.find(d => d.label === l));
  const a = ds[0], b = ds[ds.length - 1];
  const r = ds.length > 1 ? `${fill(U.range_many, {a: a.num, b: b.num})} · ${fmt(a.date, SHORT)} – ${fmt(b.date, SHORT)}` : fill(U.range_one, {a: a.num});
  out += `<div class="chapter" style="--c:${ch.color}"><div class="chapter-head"><h3>${esc(ch.name)}</h3><span class="range">${r} · ${n(ds.reduce((s, d) => s + d.km, 0))} km</span></div>`;
  for (const d of ds) {
    if (SC && d.label === SC.from) out += shortcutBox();
    const chips = [];
    for (const f of d.ferries) chips.push(`<span class="chip ferry${f.critical ? ' crit' : ''}"><b>${esc(U.chip_ferry)}</b>${esc(f.label)} · ${n(f.h)} h${f.critical ? ' · ' + esc(U.book_early) : f.book ? ' · ' + esc(U.book) : ''}</span>`);
    for (const s of d.seasonal) chips.push(`<span class="chip season"><b>${esc(U.chip_seasonal)}</b>${roads(s)}</span>`);
    for (const t of d.tolls) chips.push(`<span class="chip"><b>${esc(U.chip_toll)}</b>${esc(t)}</span>`);
    if (d.gravel_km) chips.push(`<span class="chip gravel"><b>${esc(U.chip_gravel)}</b>${d.gravel_km} km TET</span>`);
    if (d.midnight_sun) chips.push(`<span class="chip sun"><b>${esc(U.chip_sun)}</b>${esc(U.sun_text)}</span>`);
    if (d.transit) chips.push(`<span class="chip"><b>${esc(U.chip_transit)}</b>${esc(U.transit_text)}</span>`);
    const lwh = d.lwh.length ? `<div class="lwh-line"><span class="star">★</span> Long Way Home: ${d.lwh.map(x => esc(x.name) + (x.likely ? ` <span>(${esc(U.likely)})</span>` : '')).join(' · ')}</div>` : '';
    // a variant's site has only its own days in days/; the shared days link to the chosen trip's days/
    const base = d.shared ? LINKS.shared : LINKS.gpx;
    const alt = d.alt ? `<div class="alt"><b>${esc(U.fallback)}</b> ${esc(d.alt.title)} – ${d.alt.km} km, ≈${n(d.alt.h)} h. ${roads(d.alt.description || d.alt.notes)}<div class="links">${gpxLink(d.alt.file, base)}</div></div>` : '';
    const sights = d.sights.length ? `<div class="sights"><h5>${esc(U.sights)}</h5><ul>${d.sights.map(x =>
      `<li><button class="sight" type="button" data-lat="${x.lat}" data-lon="${x.lon}" data-day="${d.label}">${x.lwh ? '★ ' : ''}${esc(x.name)}</button>${x.notes ? ` <span class="sn">– ${roads(x.notes)}</span>` : ''}</li>`).join('')}</ul></div>` : '';
    const ferryH = d.ferries.reduce((s, f) => s + f.h, 0);
    out += `<article class="day" id="${d.label}" style="--c:${ch.color}"><div class="when"><span class="num">${String(d.num).padStart(2, '0')}<small>${esc(U.day_word)}</small></span>
      <span class="date">${fmt(d.date, DAY)}</span></div>
      <div class="body"><h4>${esc(d.title)}</h4>
      <div class="meta">${n(d.km)} km · ≈${n(d.h)} h ${esc(U.riding)}${ferryH ? ` · + ${n(ferryH)} h ${esc(U.on_ferries)}` : ''}${d.fuel_gap != null ? ` · ${esc(U.fuel_gap)} ${d.fuel_gap} km` : ''}</div>
      ${d.description ? `<p class="desc">${roads(d.description)}</p>` : ''}
      ${chips.length ? `<div class="chips">${chips.join('')}</div>` : ''}${lwh}
      <div class="stay"><b>${esc(U.stay[d.overnight_type] || U.stay._)}:</b> ${esc(d.overnight)}</div>
      ${d.notes ? `<div class="notes">${roads(d.notes)}</div>` : ''}${sights}${alt}
      <div class="links"><button class="btn-map" type="button" data-day="${d.label}">${esc(U.show_map)}</button>${gpxLink(d.gpx, base)}</div></div></article>`;
  }
  out += '</div>';
});
$('days').innerHTML = out;
$('days').addEventListener('click', e => {
  const b = e.target.closest('.btn-map, .sight'); if (!b) return;
  $('map').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block:'center'});
  if (b.classList.contains('sight')) T.focusPoint(+b.dataset.lat, +b.dataset.lon, b.dataset.day);
  else T.focusDay(b.dataset.day);
});

// ---- before you go
const md = s => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*([^*]+)\*/g, '<i>$1</i>');
$('ferries').querySelector('tbody').innerHTML = D.ferries.map(f => `<tr><td>${esc(f.label)}</td><td>${esc(f.operator)}</td><td class="num">${n(f.h)}</td><td${f.critical ? ' class="crit"' : ''}>${esc(f.booking)}</td><td>${f.days.join(', ')}</td></tr>`).join('');
$('seasonal').innerHTML = D.seasonal.map(s => `<li>${roads(s.label)} <span style="color:var(--muted)">(${s.days.join(', ')})</span> – ${esc(s.typical)}; ${esc(U.verify)} ${esc(s.verify)}</li>`).join('');
$('tolls').innerHTML = D.tolls.map(t => `<li>${roads(t)}</li>`).join('');
$('fuel').textContent = fill(U.fuel_text, {max: D.fuel.max, list: D.fuel.top.map(f => `${f.day} ${f.km} km`).join(', ')});
$('wild').innerHTML = D.wild.map(w => `<li><b>${esc(w.country)}:</b> ${esc(w.text)}</li>`).join('');
$('open').innerHTML = D.open.map(q => `<li>${md(q)}</li>`).join('');
$('foot').innerHTML = esc(fill(U.footer, {date: fmt(D.generated, {day:'numeric', month:'long', year:'numeric'})})) +
  (D.repo ? ` · <a href="${esc(D.repo)}" target="_blank" rel="noopener">${esc(U.source)}</a>` : '') + '.';
</script>
""")
