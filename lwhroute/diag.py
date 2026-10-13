"""Diagnostics: per-leg routed km vs straight line (detour ratio). Usage: python -m lwhroute.diag D09 D26"""
import sys

from .common import haversine_km
from .routing import load_routed

sys.stdout.reconfigure(encoding="utf-8")
for day_id in sys.argv[1:]:
    r = load_routed(day_id)
    print(day_id)
    for part in r["parts"]:
        if part["kind"] == "ferry":
            print(f"   ~~ FERRY {part['from']} → {part['to']}")
            continue
        for l in part["legs"]:
            a, b = l["coords"][0], l["coords"][-1]
            crow = haversine_km(a[0], a[1], b[0], b[1])
            ratio = l["length_km"] / crow if crow > 0.5 else 0
            mark = "  <<" if ratio > 1.8 and l["length_km"] > 15 else ""
            print(f"   {l['from'][:28]:28} → {l['to'][:28]:28} {l['length_km']:6.1f} km  crow {crow:6.1f}  x{ratio:4.2f} [{l['engine']}]{mark}")
