"""Export one gameweek of FPL ownership vs points for the xFPL quadrants site (public/).

    python update.py        # the current gameweek (what the scheduled GitHub Action runs)
    python update.py 6      # a specific gameweek

Writes public/data/gw<N>.json, adds the GW to public/data/gameweeks.json and downloads any missing team badges.
Points are provisional until FPL confirms bonus; rerunning picks up the final numbers.
The files are only rewritten when the numbers change, so a run with nothing new makes no commit.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests

SITE = Path(__file__).resolve().parent / "public"
API = "https://fantasy.premierleague.com/api"
BADGE_URL = "https://resources.premierleague.com/premierleague/badges/70/t{code}.png"
HEADERS = {"User-Agent": "Mozilla/5.0"}
OWN_CUT, PTS_CUT = 10, 3   # % ownership (high vs low), points that count as a return (2 or fewer = a blank)


def get(url):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()


fpl = get(f"{API}/bootstrap-static/")
if len(sys.argv) > 1:
    GW = int(sys.argv[1])
else:
    current = next((e for e in fpl["events"] if e["is_current"]), None)
    if current is None:
        print("No current gameweek yet (pre-season). Nothing to export.")
        sys.exit(0)
    GW = current["id"]

event = next(e for e in fpl["events"] if e["id"] == GW)
managers = event["ranked_count"]
teams = {t["id"]: t for t in fpl["teams"]}
positions = {p["id"]: p["singular_name_short"] for p in fpl["element_types"]}
fixtures = get(f"{API}/fixtures/?event={GW}")
pending = [f"{teams[f['team_h']]['short_name']} v {teams[f['team_a']]['short_name']}"
           for f in fixtures if not f["finished_provisional"]]

with ThreadPoolExecutor(max_workers=8) as pool:
    histories = dict(pool.map(lambda e: (e["id"], get(f"{API}/element-summary/{e['id']}/")["history"]),
                              fpl["elements"]))

players = []
for e in fpl["elements"]:
    rows = [h for h in histories[e["id"]] if h["round"] == GW]   # a double gameweek has two rows
    if not rows:
        continue
    total = lambda k: sum(int(h[k]) for h in rows)
    players.append({
        "id": e["id"], "name": e["web_name"], "full": f"{e['first_name']} {e['second_name']}",
        "team": teams[e["team"]]["short_name"], "pos": positions[e["element_type"]],
        "own": round(rows[0]["selected"] / managers * 100, 2),   # 'selected' is the same on both DGW rows
        "pts": total("total_points"), "min": total("minutes"), "g": total("goals_scored"),
        "a": total("assists"), "cs": total("clean_sheets"), "bonus": total("bonus"),
        "price": rows[0]["value"] / 10,
    })

played = sum(p["min"] > 0 for p in players)
if not played:
    print(f"GW{GW}: no matches played yet. Nothing to export.")
    sys.exit(0)

out = {
    "gw": GW, "managers": managers, "finished": event["finished"], "pending": pending,
    "own_cut": OWN_CUT, "pts_cut": PTS_CUT, "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
    "teams": {t["short_name"]: {"name": t["name"], "badge": f"badges/t{t['code']}.png"} for t in teams.values()},
    "players": players,
}
path = SITE / "data" / f"gw{GW}.json"
path.parent.mkdir(parents=True, exist_ok=True)
old = json.loads(path.read_text()) if path.exists() else None
if old and {**old, "updated": None} == {**out, "updated": None}:
    print(f"GW{GW}: no change since {old['updated']}.")
else:
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"GW{GW}: {len(players)} players ({played} with minutes), {managers:,} managers, "
          f"finished={event['finished']}, still to play: {pending or 'none'}")

index_path = SITE / "data" / "gameweeks.json"
index = json.loads(index_path.read_text()) if index_path.exists() else {"gameweeks": []}
if GW not in index["gameweeks"]:
    index["gameweeks"] = sorted(index["gameweeks"] + [GW])
    index_path.write_text(json.dumps(index))

(SITE / "badges").mkdir(exist_ok=True)
for t in teams.values():
    badge = SITE / "badges" / f"t{t['code']}.png"
    if not badge.exists():
        badge.write_bytes(requests.get(BADGE_URL.format(code=t["code"]), headers=HEADERS, timeout=60).content)
