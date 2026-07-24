#!/usr/bin/env python3
"""Generate Bomberman contribution animation SVG with +1 padding border."""

import os, sys, json, re, urllib.request
from typing import Optional, List, Tuple

USERNAME = "Mufid2225"
OUTPUT = "assets/contribution"

CELL = 13
GAP = 2
PITCH = CELL + GAP
COLS, ROWS = 52, 7
PAD = 1
GC = COLS + PAD * 2
GR = ROWS + PAD * 2
PX = PY = 30
SW = GC * PITCH + PX * 2
SH = GR * PITCH + PX * 2

MOVE_MS = 60
EXPLODE_MS = 600

PALETTE = {
    "dark": {
        "bg": "#0d1117",
        "cell": ["#161b22", "#01311f", "#034525", "#0f6d31", "#00c647"],
        "helmet": "#3b82f6", "helmet_dark": "#2563eb",
        "body": "#ffffff", "face": "#f5f5f5",
        "eye": "#1f2937", "boot": "#78350f",
        "bomb": "#374151", "fuse": "#ef4444",
        "boom_c": "#f97316", "boom_x": "#facc15", "boom_g": "#fbbf24",
    },
    "light": {
        "bg": "#ffffff",
        "cell": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "helmet": "#2563eb", "helmet_dark": "#1d4ed8",
        "body": "#1f2937", "face": "#fbbf24",
        "eye": "#000000", "boot": "#78350f",
        "bomb": "#4b5563", "fuse": "#dc2626",
        "boom_c": "#ea580c", "boom_x": "#eab308", "boom_g": "#facc15",
    },
}

LV = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]


# ─── Fetch ────────────────────────────────────────────────────────────────────

def fetch_graphql(username: str, token: Optional[str] = None) -> Optional[List[List[int]]]:
    q = """
    query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{weeks{contributionDays{contributionLevel weekday date}}}}}}
    """
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        h["Authorization"] = f"bearer {token}"
    try:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": q, "variables": {"l": username}}).encode(),
            headers=h,
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read())["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        grid = [[0] * ROWS for _ in range(COLS)]
        for wi, w in enumerate(d["weeks"]):
            if wi >= COLS:
                break
            for day in w["contributionDays"]:
                lv = LV.index(day["contributionLevel"]) if day["contributionLevel"] in LV else 0
                grid[wi][day["weekday"]] = lv
        n = sum(1 for w in grid for l in w if l > 0)
        print(f"GraphQL: {n} active cells")
        return grid
    except Exception as e:
        print(f"GraphQL failed: {e}", file=sys.stderr)
        return None


def fetch_html(username: str) -> Optional[List[List[int]]]:
    try:
        url = f"https://github.com/users/{username}/contributions"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode()
        cells = re.findall(r'data-level="(\d)"', html)
        if not cells:
            return None
        grid = [[0] * ROWS for _ in range(COLS)]
        for i, lv in enumerate(cells):
            if i >= COLS * ROWS:
                break
            grid[i // ROWS][i % ROWS] = int(lv)
        n = sum(1 for w in grid for l in w if l > 0)
        print(f"HTML: {n} active cells")
        return grid
    except Exception as e:
        print(f"HTML failed: {e}", file=sys.stderr)
        return None


# ─── Grid ops ─────────────────────────────────────────────────────────────────

def expand(grid: List[List[int]]) -> List[List[int]]:
    eg = [[0] * GR for _ in range(GC)]
    for x in range(COLS):
        for y in range(ROWS):
            eg[x + PAD][y + PAD] = grid[x][y]
    return eg


def xys(x: int, y: int) -> Tuple[float, float]:
    return (PX + x * PITCH + CELL / 2, PY + y * PITCH + CELL / 2)


def bfs(eg: List[List[int]], sx: int, sy: int, tx: int, ty: int, ok):
    if sx == tx and sy == ty:
        return []
    v = [[False] * GR for _ in range(GC)]
    p = [[None] * GR for _ in range(GC)]
    q = [(sx, sy)]
    v[sx][sy] = True
    for nx, ny in q:
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            ax, ay = nx + dx, ny + dy
            if 0 <= ax < GC and 0 <= ay < GR and not v[ax][ay] and ok(eg[ax][ay]):
                v[ax][ay] = True
                p[ax][ay] = (nx, ny)
                q.append((ax, ay))
                if ax == tx and ay == ty:
                    path = []
                    cx, cy = tx, ty
                    while p[cx][cy]:
                        path.append((cx, cy))
                        cx, cy = p[cx][cy]
                    path.reverse()
                    return path
    return None


def compute_path(eg_in: List[List[int]]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int, int]]]:
    eg = [row[:] for row in eg_in]
    ok = lambda l: l == 0
    cx = cy = PAD
    path = [(cx, cy)]
    bombs = []

    for x in range(PAD, PAD + COLS):
        for y in range(PAD, PAD + ROWS):
            if eg[x][y] == 0:
                continue
            tx, ty = x, y
            adj = []
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                ax, ay = tx + dx, ty + dy
                if 0 <= ax < GC and 0 <= ay < GR and ok(eg[ax][ay]):
                    adj.append((ax, ay))
            if not adj:
                continue
            target = min(adj, key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
            seg = bfs(eg, cx, cy, target[0], target[1], ok)
            if seg is None:
                continue
            path.extend(seg)
            path.append((target[0], target[1]))
            cx, cy = target
            bombs.append((tx, ty, len(path) - 1))
            eg[tx][ty] = 0
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = tx + dx, ty + dy
                if 0 <= nx < GC and 0 <= ny < GR:
                    eg[nx][ny] = 0

    return path, bombs


# ─── SVG generator ────────────────────────────────────────────────────────────

def make_svg(theme: str, eg_orig: List[List[int]], path: List[Tuple[int, int]], bombs: List[Tuple[int, int, int]]) -> str:
    P = PALETTE[theme]
    eg = [row[:] for row in eg_orig]
    ts = len(path)
    td = ts * MOVE_MS
    ts_sec = td / 1000
    ep = EXPLODE_MS / td * 100

    cross_all = set()
    for bx, by, bi in bombs:
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            ax, ay = bx + dx, by + dy
            if 0 <= ax < GC and 0 <= ay < GR:
                cross_all.add((ax, ay))

    # Bomberman keyframes
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SW:.0f} {SH:.0f}" width="{SW:.0f}" height="{SH:.0f}">']
    lines.append("<style>")
    lines.append(f"  svg {{ background:{P['bg']}; }}")
    lines.append(f"  .bm {{ animation:bm {ts_sec:.3f}s linear infinite; }}")
    for bx, by, bi in bombs:
        lines.append(f"  .ex-{bx}-{by} {{ animation:ex-{bx}-{by} {ts_sec:.3f}s linear infinite; }}")
    for cx, cy in sorted(cross_all):
        lines.append(f"  .xf-{cx}-{cy} {{ animation:xf-{cx}-{cy} {ts_sec:.3f}s linear infinite; }}")
    lines.append("</style>")
    lines.append(f'<rect x="0" y="0" width="{SW:.0f}" height="{SH:.0f}" fill="{P["bg"]}"/>')

    # Grid cells (expand original for rendering)
    eg_vis = expand(eg_orig)
    for x in range(GC):
        for y in range(GR):
            lv = eg_vis[x][y]
            sx, sy = xys(x, y)
            fill = P["cell"][lv] if lv < len(P["cell"]) else P["cell"][0]
            lines.append(f'  <rect x="{sx - CELL/2:.1f}" y="{sy - CELL/2:.1f}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}"/>')

    # Bomberman pixel art
    hw = CELL * 2
    lines.append('<g class="bm">')
    lines.append(f'  <rect x="{-hw}" y="{-CELL*1.5}" width="{CELL*4}" height="{CELL}" rx="2" fill="{P["helmet"]}"/>')
    lines.append(f'  <rect x="{-hw}" y="{-CELL*0.5}" width="{CELL*4}" height="{CELL}" rx="2" fill="{P["helmet"]}"/>')
    lines.append(f'  <rect x="{-CELL/2}" y="{-CELL*0.5}" width="{CELL}" height="{CELL}" rx="2" fill="{P["helmet_dark"]}"/>')
    lines.append(f'  <rect x="{-hw}" y="{CELL*0.5}" width="{CELL}" height="{CELL}" rx="2" fill="{P["face"]}"/>')
    lines.append(f'  <rect x="{hw-CELL}" y="{CELL*0.5}" width="{CELL}" height="{CELL}" rx="2" fill="{P["face"]}"/>')
    lines.append(f'  <rect x="{-CELL/2}" y="{CELL*0.5}" width="{CELL}" height="{CELL}" rx="2" fill="{P["body"]}"/>')
    lines.append(f'  <circle cx="{-2}" cy="{CELL*0.7}" r="1.5" fill="{P["eye"]}"/>')
    lines.append(f'  <circle cx="{2}" cy="{CELL*0.7}" r="1.5" fill="{P["eye"]}"/>')
    lines.append(f'  <rect x="{-CELL*1.2}" y="{CELL*1.5}" width="{CELL*2.4}" height="{CELL}" rx="2" fill="{P["body"]}"/>')
    lines.append(f'  <rect x="{-CELL*1.2}" y="{CELL*2.5}" width="{CELL}" height="{CELL*0.4}" rx="1" fill="{P["boot"]}"/>')
    lines.append(f'  <rect x="{CELL*0.2}" y="{CELL*2.5}" width="{CELL}" height="{CELL*0.4}" rx="1" fill="{P["boot"]}"/>')
    lines.append('</g>')

    # Bomberman movement keyframes
    lines.append("<style>")
    lines.append("@keyframes bm {")
    for i, (x, y) in enumerate(path):
        sx, sy = xys(x, y)
        pct = (i / ts) * 100 if i < ts else 100
        lines.append(f"  {pct:.3f}% {{ transform:translate({sx:.1f}px,{sy:.1f}px); }}")
    lines.append("}")
    lines.append("</style>")

    # Bomb explosions
    for bx, by, bi in bombs:
        cx, cy = xys(bx, by)
        sp = (bi / ts) * 100
        ep_ct = sp + ep
        lines.append("<style>")
        lines.append(f"@keyframes ex-{bx}-{by} {{")
        lines.append(f"  0%,{sp - 0.1:.3f}% {{ opacity:0; transform:scale(0); transform-origin:{cx:.1f}px {cy:.1f}px; }}")
        lines.append(f"  {sp:.3f}%,{sp + 0.5:.3f}% {{ opacity:1; transform:scale(0.8); transform-origin:{cx:.1f}px {cy:.1f}px; }}")
        lines.append(f"  {sp + 0.8:.3f}%,{sp + 1.5:.3f}% {{ opacity:1; transform:scale(1.3); transform-origin:{cx:.1f}px {cy:.1f}px; }}")
        lines.append(f"  {sp + 1.8:.3f}%,{ep_ct - 0.5:.3f}% {{ opacity:1; transform:scale(1); transform-origin:{cx:.1f}px {cy:.1f}px; }}")
        lines.append(f"  {ep_ct:.3f}%,100% {{ opacity:0; transform:scale(0); transform-origin:{cx:.1f}px {cy:.1f}px; }}")
        lines.append("}")
        lines.append("</style>")

        lines.append(f'<g class="ex-{bx}-{by}" style="opacity:0">')
        lines.append(f'  <rect x="{cx - 3:.1f}" y="{cy - 3:.1f}" width="6" height="6" rx="1.5" fill="{P["bomb"]}"/>')
        lines.append(f'  <circle cx="{cx:.1f}" cy="{cy - 4:.1f}" r="1.2" fill="{P["fuse"]}"/>')
        lines.append(f'  <rect x="{cx - CELL/2:.1f}" y="{cy - CELL/2:.1f}" width="{CELL}" height="{CELL}" rx="2" fill="{P["boom_c"]}" style="opacity:0.9"/>')
        lines.append('</g>')

    # Cross explosions
    for cx, cy in sorted(cross_all):
        sx, sy = xys(cx, cy)
        sp = 100
        for bx, by, bi in bombs:
            if abs(bx - cx) + abs(by - cy) == 1:
                tsp = (bi / ts) * 100
                if tsp < sp:
                    sp = tsp
        ep_ct = sp + ep
        lines.append("<style>")
        lines.append(f"@keyframes xf-{cx}-{cy} {{")
        lines.append(f"  0%,{sp + 1:.3f}% {{ opacity:0; transform:scale(0); transform-origin:{sx:.1f}px {sy:.1f}px; }}")
        lines.append(f"  {sp + 1.5:.3f}%,{sp + 2.5:.3f}% {{ opacity:0.8; transform:scale(1); transform-origin:{sx:.1f}px {sy:.1f}px; }}")
        lines.append(f"  {ep_ct:.3f}%,100% {{ opacity:0; transform:scale(0); transform-origin:{sx:.1f}px {sy:.1f}px; }}")
        lines.append("}")
        lines.append("</style>")

        lines.append(f'  <rect class="xf-{cx}-{cy}" x="{sx - CELL/2:.1f}" y="{sy - CELL/2:.1f}" width="{CELL}" height="{CELL}" rx="2" fill="{P["boom_x"]}" style="opacity:0">')
        lines.append('  </rect>')

    lines.append('</svg>')
    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    token = os.environ.get("GITHUB_TOKEN")

    print(f"Fetching {username}...")
    grid = fetch_graphql(username, token) or fetch_html(username)
    if not grid:
        print("Error: no data", file=sys.stderr)
        sys.exit(1)

    total = sum(1 for w in grid for l in w if l > 0)
    print(f"Active: {total}/{COLS * ROWS}")

    eg = expand(grid)
    path, bombs = compute_path(eg)
    print(f"Path: {len(path)} steps, bombs: {len(bombs)}")
    print(f"Anim: {len(path) * MOVE_MS / 1000:.1f}s")

    os.makedirs(OUTPUT, exist_ok=True)
    for theme in ["dark", "light"]:
        svg = make_svg(theme, grid, path, bombs)
        fp = os.path.join(OUTPUT, f"bomberman-{theme}.svg")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(svg)
        kb = os.path.getsize(fp) / 1024
        print(f"  {fp} ({kb:.1f}KB)")

    print("Done!")


if __name__ == "__main__":
    main()