"""CLI: python -m lwhroute {geocode|snap|bypass|basemap|route|fuel|build|validate|all} [--tet]"""
from __future__ import annotations

import json
import os
import sys

if "--tet" in sys.argv:   # before .common is imported: it picks the output folders
    os.environ["LWH_TET"] = "1"

from .common import DATA


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "all"
    if cmd in ("geocode", "all"):
        from . import geocode
        rows = geocode.run()
        flagged = geocode.print_table(rows)
        (DATA / "geocode_report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        if cmd == "all" and flagged > 5 and "--force" not in argv:
            print(f"\n{flagged} points flagged (> 5): resolve with `override:` in route.yaml, then re-run.")
            return 2
    if cmd == "snap":   # apply road-snap suggestions from the last geocode run as overrides
        from . import geocode
        rows = json.loads((DATA / "geocode_report.json").read_text(encoding="utf-8"))
        print(f"{geocode.apply_snaps(rows)} override(s) written")
        return 0
    if cmd == "bypass":   # move town-centre vias that cause U-turns onto the through-route
        from . import bypass
        print(f"{bypass.run()} change(s) written – re-run `route`")
        return 0
    if cmd == "basemap" or (cmd == "all" and not (DATA / "basemap.json").exists()):
        from . import basemap
        basemap.run()
        if cmd == "basemap":
            return 0
    if cmd in ("route", "all"):
        from . import routing
        routing.run()
    if cmd in ("fuel", "all"):
        from . import fuel
        fuel.run()
    if cmd in ("build", "all"):
        from . import build
        build.run()
    if cmd in ("validate", "all"):
        from . import validate
        return validate.run()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
