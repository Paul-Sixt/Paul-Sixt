"""Contribution Tetris: neon blocks fall and stack into the real contribution graph."""
import random

from common import MONO, SANS, CYAN, VIOLET, MAGENTA, AMBER, EMERALD, BLUE, ROSE, card, pct, esc, stars

W, H = 1000, 430
PITCH, CELL = 17, 15
BY = 214          # board top
SPAWN_Y = 84      # where pieces appear
PIECE_COLORS = [CYAN, VIOLET, MAGENTA, AMBER, EMERALD, BLUE, ROSE]
FALL_T = 0.75


def pieces_from_grid(grid, rnd):
    active = {(c, r) for c, col in enumerate(grid) for r in range(7) if col[r] and col[r][0] > 0}
    level = {(c, r): max(1, grid[c][r][1]) for (c, r) in active}
    left = set(active)
    pieces = []
    for cell in sorted(active, key=lambda p: (-p[1], p[0])):
        if cell not in left:
            continue
        size = rnd.choice([4, 4, 4, 3])
        piece, frontier = [cell], [cell]
        left.discard(cell)
        while frontier and len(piece) < size:
            c, r = frontier.pop(rnd.randrange(len(frontier)))
            nbrs = [(c + 1, r), (c - 1, r), (c, r - 1), (c, r + 1)]
            rnd.shuffle(nbrs)
            for n in nbrs:
                if n in left and len(piece) < size:
                    left.discard(n)
                    piece.append(n)
                    frontier.append(n)
            if (c, r) not in frontier and len(piece) < size and frontier == []:
                break
        pieces.append([(c, r, level[(c, r)]) for (c, r) in piece])
    # land bottom rows first, sweep loosely left -> right
    pieces.sort(key=lambda p: (-max(q[1] for q in p), min(q[0] for q in p) + rnd.uniform(-6, 6)))
    return pieces


def render(data):
    grid = data["grid"][-53:]
    cols = len(grid)
    bw = cols * PITCH - (PITCH - CELL)
    bx = (W - bw) / 2
    rnd = random.Random(3)
    pieces = pieces_from_grid(grid, rnd)
    n = len(pieces)

    t0 = 0.6
    dt = min(0.35, max(0.07, 20.0 / max(n, 1)))
    lands = []
    for i in range(n):
        lands.append(t0 + i * dt + FALL_T)
    t_full = (lands[-1] if lands else t0) + 0.3
    t_rows = t_full + 0.9
    row_dt = 0.13
    t_hold = t_rows + 7 * row_dt + 0.4
    T = t_hold + 2.6
    P = lambda s: pct(s, T)

    css, body = [], []
    sa = stars(rnd, W, H, 50)
    body.append(f'<g class="drift"><g>{sa}</g><g transform="translate(0 -{H})">{sa}</g></g>')

    # HUD
    body.append(f'''<g font-family="{MONO}" font-size="14" font-weight="700" letter-spacing="2">
  <text x="36" y="44" fill="{CYAN}">TETRIS</text><text x="116" y="44" fill="#e6edf3">{esc(data["user"].upper())}</text>
  <text x="{W/2}" y="44" text-anchor="middle" fill="#8b949e">STACKING 12 MONTHS OF COMMITS</text>
  <text x="{W - 36}" y="44" text-anchor="end" fill="#e6edf3"><tspan fill="{MAGENTA}">SCORE </tspan>{data["contributions"]:06d}</text>
</g>
<line x1="36" y1="60" x2="{W - 36}" y2="60" stroke="#ffffff" stroke-opacity=".06"/>''')

    # well
    pad = 8
    body.append(f'''<g stroke-linecap="round" fill="none">
  <path d="M{bx - pad} {SPAWN_Y - 10} V{BY + 7 * PITCH + pad - 2} H{bx + bw + pad} V{SPAWN_Y - 10}" stroke="{VIOLET}" stroke-opacity=".25" stroke-width="10" filter="url(#soft)"/>
  <path d="M{bx - pad} {SPAWN_Y - 10} V{BY + 7 * PITCH + pad - 2} H{bx + bw + pad} V{SPAWN_Y - 10}" stroke="url(#wall)" stroke-width="3"/>
</g>''')
    ghost = []
    for c, col in enumerate(grid):
        for r in range(7):
            if col[r] is not None:
                ghost.append(f'<rect x="{bx + c * PITCH:.1f}" y="{BY + r * PITCH}" width="{CELL}" height="{CELL}" rx="2.5" '
                             f'fill="none" stroke="#ffffff" stroke-opacity=".05"/>')
    body.append(f'<g>{"".join(ghost)}</g>')

    # pieces
    pc = []
    for i, piece in enumerate(pieces):
        col = PIECE_COLORS[i % len(PIECE_COLORS)]
        t_spawn = t0 + i * dt
        t_land = lands[i]
        rmin = min(q[1] for q in piece)
        fall = (BY + rmin * PITCH) - SPAWN_Y
        steps = max(2, int(fall / PITCH))
        shift = rnd.choice([-3, -2, -1, 1, 2, 3]) * PITCH
        rot = rnd.choice([0, 90, -90, 180]) if len(piece) >= 3 else 0
        cells = []
        for (c, r, lvl) in piece:
            x, y = bx + c * PITCH, BY + r * PITCH
            op = 0.55 + 0.11 * lvl
            cells.append(f'<rect x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{col}" fill-opacity="{op:.2f}" '
                         f'stroke="{col}" stroke-width="1.2"/>'
                         f'<rect x="{x + 3:.1f}" y="{y + 3}" width="{CELL - 9}" height="3" rx="1.5" fill="#ffffff" opacity=".35"/>')
        ts, tl = P(t_spawn), P(t_land)
        css.append(f"@keyframes f{i}{{0%,{P(max(0, t_spawn - 0.01))}%{{opacity:0;transform:translate({shift}px,-{fall}px)}}"
                   f"{ts}%{{opacity:1;transform:translate({shift}px,-{fall}px);animation-timing-function:steps({steps},end)}}"
                   f"{tl}%,100%{{opacity:1;transform:translate(0,0)}}}}")
        if rot:
            tr = P(t_spawn + FALL_T * 0.45)
            css.append(f"@keyframes r{i}{{0%,{tr}%{{transform:rotate({rot}deg)}}{float(tr) + 0.01:.3f}%,100%{{transform:rotate(0)}}}}")
            inner = f'<g class="rot" style="animation-name:r{i}">{"".join(cells)}</g>'
        else:
            inner = "".join(cells)
        # landing flash
        flash = "".join(f'<rect x="{bx + c * PITCH:.1f}" y="{BY + r * PITCH}" width="{CELL}" height="{CELL}" rx="2.5" '
                        f'class="land" style="animation-delay:{t_land:.3f}s"/>' for (c, r, _l) in piece)
        pc.append(f'<g class="pc" style="animation-name:f{i}">{inner}</g>{flash}')
    body.append(f'<g class="board">{"".join(pc)}</g>')

    # row clear sweep
    rows = "".join(f'<rect x="{bx - 4}" y="{BY + r * PITCH - 1}" width="{bw + 8}" height="{CELL + 2}" rx="3" class="row" '
                   f'style="animation-delay:{t_rows + (6 - r) * row_dt:.3f}s"/>' for r in range(7))
    if n:
        body.append(rows)

    # banner
    css.append(f"@keyframes banner{{0%,{P(t_full)}%{{opacity:0;transform:translateY(14px) scale(.8)}}{P(t_full + 0.4)}%{{opacity:1;transform:none}}"
               f"{P(t_hold + 1.6)}%{{opacity:1;transform:none}}{P(t_hold + 2.1)}%,100%{{opacity:0;transform:scale(1.15)}}}}")
    label = "PERFECT STACK" if n else "AWAITING FIRST BLOCKS"
    sub = f"{n} PIECES · {sum(len(p) for p in pieces)} ACTIVE DAYS" if n else "COMMIT SOMETHING TO START THE GAME"
    body.append(f'''<g class="banner">
  <text x="{W/2}" y="{SPAWN_Y + 52}" text-anchor="middle" font-family="{SANS}" font-size="44" font-weight="900" letter-spacing="6" fill="url(#txt)" filter="url(#glow)">{label}</text>
  <text x="{W/2}" y="{SPAWN_Y + 82}" text-anchor="middle" font-family="{MONO}" font-size="15" letter-spacing="4" fill="#c9d1d9">{sub}</text>
</g>''')

    # footer hud
    body.append(f'''<g font-family="{MONO}" font-size="12" letter-spacing="2" fill="#8b949e">
  <text x="{bx}" y="{BY + 7 * PITCH + 40}">← 52 WEEKS AGO</text>
  <text x="{bx + bw}" y="{BY + 7 * PITCH + 40}" text-anchor="end">TODAY →</text>
  <text x="{W/2}" y="{BY + 7 * PITCH + 40}" text-anchor="middle" fill="#c9d1d9">BRIGHTER BLOCK = MORE COMMITS</text>
</g>''')

    rt = P(0.5)
    css += [
        f".pc{{opacity:0;animation-duration:{T:.3f}s;animation-iteration-count:infinite;animation-timing-function:linear}}",
        f".rot{{transform-box:fill-box;transform-origin:center;animation-duration:{T:.3f}s;animation-iteration-count:infinite;animation-timing-function:linear}}",
        f".land{{opacity:0;fill:#ffffff;animation:land {T:.3f}s ease-out infinite}}",
        f"@keyframes land{{0%{{opacity:.9}}{P(0.25)}%,100%{{opacity:0}}}}",
        f".row{{opacity:0;fill:#ffffff;animation:row {T:.3f}s ease-out infinite;filter:url(#glow)}}",
        f"@keyframes row{{0%{{opacity:.85;transform:scaleX(.2)}}{P(0.18)}%{{opacity:.9;transform:scaleX(1)}}{rt}%,100%{{opacity:0;transform:scaleX(1)}}}}",
        ".row{transform-box:fill-box;transform-origin:center}",
        f".board{{animation:board {T:.3f}s ease-in infinite;transform-box:fill-box;transform-origin:center}}",
        f"@keyframes board{{0%,{P(t_hold + 1.4)}%{{opacity:1;transform:none;filter:none}}{P(t_hold + 2.2)}%{{opacity:0;transform:translateY(40px) scaleY(.4)}}100%{{opacity:0}}}}",
        f".banner{{opacity:0;animation:banner {T:.3f}s ease-out infinite;transform-box:fill-box;transform-origin:center}}",
        ".star{animation:tw 4s ease-in-out infinite}@keyframes tw{50%{opacity:.15}}",
        f".drift{{animation:drift 40s linear infinite}}@keyframes drift{{to{{transform:translateY({H}px)}}}}",
    ]
    defs = f'''<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="8"/></filter>
  <linearGradient id="wall" gradientUnits="userSpaceOnUse" x1="{bx}" x2="{bx + bw}"><stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/></linearGradient>
  <linearGradient id="txt" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/></linearGradient>'''
    return card(W, H, "".join(body), "Contribution Tetris", defs=defs, css="\n  ".join(css))
