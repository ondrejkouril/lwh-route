"""Shared helpers: paths, YAML model, geometry, throttled + cached HTTP."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
# `--tet` (LWH_TET=1): private build with the TET gravel spliced in. TET terms forbid redistribution and the repo
# is public, so it routes into data/routed_tet/ and builds into out_tet/, both git-ignored; out/ stays road-only.
TET_BUILD = os.environ.get("LWH_TET") == "1"
OUT = ROOT / ("out_tet" if TET_BUILD else "out")
CACHE = DATA / "cache"
USER_AGENT = "lwh-route-gpx-builder/0.1 (personal motorcycle trip planning)"

ROUTABLE = {"via", "shape", "poi", "overnight", "ferry_start", "ferry_end"}


# ------------------------------------------------------------------ model
@dataclass
class Point:
    name: str
    lat: float
    lon: float
    type: str
    lwh: bool = False
    notes: str = ""
    geocode: str | None = None
    road: str | None = None
    lwh_conf: str | None = None
    spur: str | None = None
    route: bool = True
    ferry: str | None = None
    override: dict | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "Point":
        known = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        known["lat"], known["lon"] = float(d["lat"]), float(d["lon"])
        known["notes"] = d.get("notes") or ""
        p = cls(**known)
        if p.override:
            p.lat, p.lon = float(p.override["lat"]), float(p.override["lon"])
        return p

    @property
    def routed(self) -> bool:
        return self.route and self.type in ROUTABLE

    @property
    def key(self) -> str:
        return f"{self.name}|{self.lat:.5f}|{self.lon:.5f}"


@dataclass
class Day:
    id: str
    offset: int
    title: str
    from_: str
    to: str
    target_km: float
    points: list[Point]
    overnight_type: str = ""
    country: str = ""
    transit: bool = False
    tolls: list[str] = field(default_factory=list)
    seasonal: list[str] = field(default_factory=list)
    notes: str = ""
    alternative_of: str | None = None
    optional_extra_day: bool = False
    option: str | None = None
    chapter: str | None = None   # starts a new section on the itinerary page
    description: str = ""       # landscape and what to look out for (itinerary page)

    @classmethod
    def from_dict(cls, d: dict) -> "Day":
        return cls(
            id=d["id"], offset=int(d["offset"]), title=d["title"], from_=d["from"], to=d["to"],
            target_km=float(d["target_km"]), points=[Point.from_dict(p) for p in d["points"]],
            overnight_type=d.get("overnight_type", ""), country=d.get("country", ""),
            transit=bool(d.get("transit", False)), tolls=d.get("tolls") or [],
            seasonal=d.get("seasonal") or [], notes=d.get("notes") or "",
            alternative_of=d.get("alternative_of"), optional_extra_day=bool(d.get("optional_extra_day")),
            option=d.get("option"), chapter=d.get("chapter"), description=d.get("description") or "",
        )

    @property
    def is_alt(self) -> bool:
        return self.alternative_of is not None

    @property
    def label(self) -> str:
        """Trip day number as the rider sees it (D01…); YAML ids of Option B / shifted days differ."""
        return self.id if self.is_alt else f"D{self.offset + 1:02d}"

    @property
    def filename(self) -> str:
        if self.is_alt:
            return f"{self.id}.gpx"
        return f"{self.label}_{slug(self.from_)}-{slug(self.to)}.gpx"

    @property
    def overnight(self) -> Point | None:
        for p in reversed(self.points):
            if p.type == "overnight":
                return p
        return None


@dataclass
class Route:
    meta: dict
    ferries: dict
    seasonal_roads: dict
    tolls: dict
    days: list[Day]          # base days incl. alternatives
    option_b: list[Day]
    option_b_meta: dict
    gravel: list = field(default_factory=list)   # optional TET sections (see tet.py)
    shortcut: list[Day] = field(default_factory=list)   # alternative ending: fast way home (offsets relative)
    shortcut_meta: dict = field(default_factory=dict)
    variant: list[Day] = field(default_factory=list)   # complete alternative ending with its own tab (offsets relative)
    variant_meta: dict = field(default_factory=dict)

    @property
    def base_days(self) -> list[Day]:
        return [d for d in self.days if not d.is_alt]

    @property
    def alt_days(self) -> list[Day]:
        return [d for d in self.days if d.is_alt]

    def option_b_sequence(self) -> list[Day]:
        """Full Option B trip: base days with D14–D16 replaced by B14–B18, later days shifted."""
        replaces = set(self.option_b_meta.get("replaces", []))
        shift = len(self.option_b) - len(replaces)
        seq: list[Day] = []
        inserted = False
        for d in self.base_days:
            if d.id in replaces:
                if not inserted:
                    seq.extend(self.option_b)
                    inserted = True
                continue
            if inserted:
                d = Day(**{**d.__dict__, "offset": d.offset + shift})
            seq.append(d)
        return seq

    def chosen_sequence(self) -> list[Day]:
        return self.option_b_sequence() if str(self.meta.get("chosen_option", "A")).upper() == "B" else self.base_days

    def _ending_sequence(self, meta: dict, ending: list[Day]) -> list[Day]:
        """Chosen trip up to the day before `replaces_from`, then the ending's days (offsets made absolute)."""
        seq = self.chosen_sequence()
        cut = next(i for i, d in enumerate(seq) if d.id == meta["replaces_from"])
        base = seq[cut].offset
        return seq[:cut] + [Day(**{**d.__dict__, "offset": base + d.offset}) for d in ending]

    def shortcut_sequence(self) -> list[Day]:
        return self._ending_sequence(self.shortcut_meta, self.shortcut)

    def shortcut_days(self) -> list[Day]:
        return self.shortcut_sequence()[-len(self.shortcut):] if self.shortcut else []

    def variant_sequence(self) -> list[Day]:
        return self._ending_sequence(self.variant_meta, self.variant)

    def variant_days(self) -> list[Day]:
        return self.variant_sequence()[-len(self.variant):] if self.variant else []

    def all_days(self) -> list[Day]:
        return self.days + self.option_b + self.shortcut + self.variant


def load_route(path: Path = DATA / "route.yaml") -> Route:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    ob = raw.get("option_b") or {}
    return Route(
        meta=raw.get("meta", {}), ferries=raw.get("ferries", {}),
        seasonal_roads=raw.get("seasonal_roads", {}), tolls=raw.get("tolls", {}),
        days=[Day.from_dict(d) for d in raw["days"]],
        option_b=[Day.from_dict(d) for d in ob.get("days", [])],
        option_b_meta={k: v for k, v in ob.items() if k != "days"},
        gravel=raw.get("gravel") or [],
        shortcut=[Day.from_dict(d) for d in (raw.get("shortcut") or {}).get("days", [])],
        shortcut_meta={k: v for k, v in (raw.get("shortcut") or {}).items() if k != "days"},
        variant=[Day.from_dict(d) for d in (raw.get("variant") or {}).get("days", [])],
        variant_meta={k: v for k, v in (raw.get("variant") or {}).items() if k != "days"},
    )


# ------------------------------------------------------------------ geometry
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def line_km(coords: list[tuple[float, float]]) -> float:
    """coords as (lat, lon)."""
    return sum(haversine_km(*a, *b) for a, b in zip(coords, coords[1:]))


class TrackIndex:
    """Grid index over track points for fast nearest-point / along-track lookups."""

    def __init__(self, coords: list[tuple[float, float]], cell_deg: float = 0.05):
        self.coords = coords
        self.cell = cell_deg
        self.cum = [0.0]
        for a, b in zip(coords, coords[1:]):
            self.cum.append(self.cum[-1] + haversine_km(*a, *b))
        self.grid: dict[tuple[int, int], list[int]] = {}
        for i, (la, lo) in enumerate(coords):
            self.grid.setdefault((int(la // cell_deg), int(lo // cell_deg)), []).append(i)

    def nearest(self, lat: float, lon: float, rings: int = 1) -> tuple[float, int]:
        """(distance_km, index) of nearest track point within `rings` grid cells, else (inf, -1)."""
        ci, cj = int(lat // self.cell), int(lon // self.cell)
        best = (math.inf, -1)
        for di in range(-rings, rings + 1):
            for dj in range(-rings, rings + 1):
                for i in self.grid.get((ci + di, cj + dj), ()):
                    d = haversine_km(lat, lon, *self.coords[i])
                    if d < best[0]:
                        best = (d, i)
        return best


# ------------------------------------------------------------------ text
_TRANSLIT = str.maketrans({"ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "ß": "ss", "ł": "l", "Ł": "L", "đ": "d"})


def slug(s: str) -> str:
    s = s.translate(_TRANSLIT)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "", s.title())


# ------------------------------------------------------------------ HTTP
class Throttled:
    """requests session with a minimum interval between calls (per instance)."""

    def __init__(self, min_interval: float):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.min_interval = min_interval
        self._last = 0.0

    def _wait(self):
        dt = time.monotonic() - self._last
        if dt < self.min_interval:
            time.sleep(self.min_interval - dt)
        self._last = time.monotonic()

    def get(self, url, **kw):
        self._wait()
        return self.s.get(url, timeout=kw.pop("timeout", 120), **kw)

    def post(self, url, **kw):
        self._wait()
        return self.s.post(url, timeout=kw.pop("timeout", 180), **kw)


class JsonCache:
    """One JSON file per key under data/cache/<ns>/ (hash-named)."""

    def __init__(self, ns: str):
        self.dir = CACHE / ns
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.dir / (hashlib.sha1(key.encode()).hexdigest()[:20] + ".json")

    def get(self, key: str):
        p = self._path(key)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))["value"]
        return None

    def set(self, key: str, value):
        self._path(key).write_text(json.dumps({"key": key, "value": value}, ensure_ascii=False), encoding="utf-8")


def unique_points(days: list[Day]) -> list[tuple[Day, Point]]:
    seen, out = set(), []
    for d in days:
        for p in d.points:
            if p.key not in seen:
                seen.add(p.key)
                out.append((d, p))
    return out
