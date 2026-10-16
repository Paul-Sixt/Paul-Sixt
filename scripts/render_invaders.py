"""Neon Space Invaders: a ship shoots down the contribution graph, one cell at a time."""
import math
import random

from common import plural, MONO, SANS, CYAN, VIOLET, MAGENTA, AMBER, LEVEL_COLORS, card, pct, esc, stars

W, H = 1000, 560
PITCH, CELL = 17, 13
GY0 = 92                 # top of the formation
SHIP_Y = 478             # ship nose
LASER_T = 0.22           # laser travel time (s)
BURST_T = 0.55           # particle burst duration (s)
N_PART = 6


def render(data):
    grid = data["grid"][-53:]
    cols = len(grid)
    gx0 = (W - (cols * PITCH - (PITCH - CELL))) / 2
    rnd = random.Random(1)

    def cell_xy(c, r):
        return gx0 + c * PITCH, GY0 + r * PITCH

    # ---------------------------------------------------------- build timeline
    targets = []  # (col, row, level, hits)
    for c, col in enumerate(grid):
        for r in range(6, -1, -1):  # bottom row first
            v = col[r]
            if v and v[0] > 0:
                lvl = max(1, v[1])
                targets.append((c, r, lvl, 1 if lvl <= 2 else 2))
    n_hits = sum(t[3] for t in targets)
    t0 = 1.6  # formation warp-in
    shots, kills, ship_stops = [], {}, [(0.0, W / 2)]
    if targets:
        dt = min(0.28, max(0.055, 22.0 / n_hits))
        t, x_prev = t0, W / 2
        cur_col = None
        for (c, r, lvl, hits) in targets:
            x = cell_xy(c, r)[0] + CELL / 2
            if c != cur_col:
                move = max(0.08, abs(x - x_prev) * 0.0016)
                ship_stops.append((t, x_prev))
                t += move
                ship_stops.append((t, x))
                x_prev, cur_col = x, c
            for h in range(hits):
                shots.append((t, x, c, r, lvl, h == hits - 1))
                t += dt
        t_last = t + LASER_T
        ship_stops.append((t_last, x_prev))
        ship_stops.append((t_last + 1.2, W / 2))
        t_clear = t_last + 0.5
        T = t_clear + 3.2
        t_desc_end = t_last
    else:
        T = 9.0
        t_clear = None
        ship_stops = [(0, W / 2), (2.2, 260), (4.5, 740), (6.8, 260), (9.0, W / 2)]
    ship_stops.append((T, W / 2))

    css, body = [], []
    P = lambda s: pct(s, T)
    DESC = 70.0

    def off(t):
        if not targets:
            return 0.0
        return DESC * max(0.0, min(1.0, (t - t0) / max(0.1, t_desc_end - t0)))

    # ---------------------------------------------------------- background
    sa, sb = stars(rnd, W, H, 70), stars(rnd, W, H, 30, rmax=2.2)
    body.append(f'<g class="starsA"><g>{sa}</g><g transform="translate(0 -{H})">{sa}</g></g>')
    body.append(f'<g class="starsB"><g>{sb}</g><g transform="translate(0 -{H})">{sb}</g></g>')
    body.append(f'<ellipse cx="{W/2}" cy="{H+40}" rx="560" ry="120" fill="{VIOLET}" opacity=".18" filter="url(#soft)"/>')

    # HUD
    hi = f"{data['contributions']:06d}"
    body.append(f'''<g font-family="{MONO}" font-size="14" font-weight="700" letter-spacing="2">
  <text x="36" y="44" fill="{CYAN}">1UP</text><text x="86" y="44" fill="#e6edf3">{esc(data["user"].upper())}</text>
  <text x="{W/2}" y="44" text-anchor="middle" fill="#8b949e">WAVE · LAST 12 MONTHS</text>
  <text x="{W - 36}" y="44" text-anchor="end" fill="#e6edf3"><tspan fill="{MAGENTA}">HI-SCORE </tspan>{hi}</text>
</g>
<line x1="36" y1="60" x2="{W - 36}" y2="60" stroke="#ffffff" stroke-opacity=".06"/>''')

    # ---------------------------------------------------------- formation
    form = []
    for c, col in enumerate(grid):
        for r in range(7):
            if col[r] is None:
                continue
            x, y = cell_xy(c, r)
            form.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="3" fill="none" '
                        f'stroke="#30363d" stroke-width="1"/>')
    form_ghost = f'<g class="ghost">{"".join(form)}</g>'

    # per-cell life keyframes
    hits_by_cell = {}
    for (ts, x, c, r, lvl, kill) in shots:
        hits_by_cell.setdefault((c, r), []).append((ts + LASER_T, kill))
    cells = []
    for i, (c, r, lvl, hits) in enumerate(targets):
        x, y = cell_xy(c, r)
        t_in = 0.25 + c * 0.018 + r * 0.03
        hs = hits_by_cell[(c, r)]
        kf = [f"0%,{P(t_in)}%{{opacity:0;transform:scale(0)}}",
              f"{P(t_in + 0.35)}%{{opacity:1;transform:scale(1);fill:{LEVEL_COLORS[lvl]}}}"]
        if len(hs) == 2:
            th = hs[0][0]
            kf += [f"{P(th - 0.01)}%{{fill:{LEVEL_COLORS[lvl]};transform:scale(1)}}",
                   f"{P(th)}%{{fill:#ffffff;transform:scale(1.25)}}",
                   f"{P(th + 0.08)}%{{fill:{LEVEL_COLORS[lvl - 1]};transform:scale(1)}}"]
        tk = hs[-1][0]
        prev_fill = LEVEL_COLORS[lvl - 1] if len(hs) == 2 else LEVEL_COLORS[lvl]
        kf += [f"{P(tk - 0.01)}%{{opacity:1;fill:{prev_fill};transform:scale(1)}}",
               f"{P(tk)}%{{opacity:1;fill:#ffffff;transform:scale(1.6)}}",
               f"{P(tk + 0.14)}%{{opacity:0;transform:scale(.2)}}",
               "100%{opacity:0;transform:scale(0)}"]
        css.append(f"@keyframes k{i}{{{''.join(kf)}}}")
        cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="3" '
                     f'fill="{LEVEL_COLORS[lvl]}" class="cell" style="animation-name:k{i}"/>')
    body.append(f'<g class="descend">{form_ghost}<g class="formation">{"".join(cells)}</g></g>')
    if targets:
        css.append(f"@keyframes descend{{0%,{P(t0)}%{{transform:translateY(0)}}{P(t_desc_end)}%,{P(T - 0.05)}%{{transform:translateY({DESC}px)}}100%{{transform:translateY(0)}}}}")
        css.append(f".descend{{animation:descend {T:.3f}s linear infinite}}")

    # ---------------------------------------------------------- lasers, impacts, particles
    fx = []
    for (ts, x, c, r, lvl, kill) in shots:
        _, cy = cell_xy(c, r)
        ty = cy + CELL / 2
        th = ts + LASER_T
        ty += off(th)
        dy = ty - (SHIP_Y - 24)
        fx.append(f'<rect x="{x - 1.5:.1f}" y="{SHIP_Y - 24}" width="3" height="20" rx="1.5" class="laser" '
                  f'style="--dy:{dy:.1f}px;animation-delay:{ts:.3f}s"/>')
        cx = x
        fx.append(f'<circle cx="{cx:.1f}" cy="{ty:.1f}" r="{13 if kill else 7}" class="boom{" big" if kill and lvl >= 3 else ""}" '
                  f'style="animation-delay:{th:.3f}s"/>')
        if kill:
            col = LEVEL_COLORS[lvl] if lvl > 1 else VIOLET
            for k in range(N_PART):
                fx.append(f'<rect x="{cx - 2:.1f}" y="{ty - 2:.1f}" width="4" height="4" class="p p{k}" '
                          f'style="fill:{col};animation-delay:{th:.3f}s"/>')
    body.append(f'<g>{"".join(fx)}</g>')

    # particle direction keyframes
    pe = P(BURST_T)
    for k in range(N_PART):
        a = 2 * math.pi * k / N_PART + 0.4
        dist = 34 + (k % 3) * 9
        dx, dy = math.cos(a) * dist, math.sin(a) * dist
        css.append(f"@keyframes p{k}{{0%{{opacity:1;transform:translate(0,0) rotate(0)}}"
                   f"{pe}%{{opacity:0;transform:translate({dx:.1f}px,{dy:.1f}px) rotate(180deg)}}100%{{opacity:0}}}}")
    css.append(f".p{{opacity:0;animation:p0 {T:.3f}s cubic-bezier(.1,.7,.3,1) infinite;transform-box:fill-box;transform-origin:center}}")
    css.extend(f".p{k}{{animation-name:p{k}}}" for k in range(N_PART))
    lt = P(LASER_T)
    css.append(f"@keyframes laser{{0%{{opacity:1;transform:translateY(0)}}{lt}%{{opacity:1;transform:translateY(var(--dy))}}"
               f"{float(lt) + 0.01:.3f}%,100%{{opacity:0;transform:translateY(var(--dy))}}}}")
    css.append(f".laser{{opacity:0;fill:{CYAN};animation:laser {T:.3f}s linear infinite;filter:url(#glow)}}")
    bt = P(0.3)
    css.append(f"@keyframes boom{{0%{{opacity:.95;transform:scale(.2)}}{bt}%{{opacity:0;transform:scale(1.6)}}100%{{opacity:0}}}}")
    css.append(f".boom{{opacity:0;fill:none;stroke:#e0fbff;stroke-width:2.5;animation:boom {T:.3f}s ease-out infinite;transform-box:fill-box;transform-origin:center}}")
    css.append(f".boom.big{{stroke:{AMBER};stroke-width:3.5}}")

    # ---------------------------------------------------------- ship
    stops = sorted(ship_stops)
    kf = []
    for (ts, x) in stops:
        kf.append(f"{P(ts)}%{{transform:translateX({x - W / 2:.1f}px)}}")
    css.append(f"@keyframes ship{{{''.join(kf)}}}")
    flashes = "".join(f'<circle cx="{W/2}" cy="{SHIP_Y - 2}" r="4" class="muzzle" style="animation-delay:{ts:.3f}s"/>'
                      for (ts, *_r) in shots)
    mt = P(0.09)
    css.append(f"@keyframes muzzle{{0%{{opacity:1;transform:scale(1)}}{mt}%{{opacity:0;transform:scale(2)}}100%{{opacity:0}}}}")
    css.append(f".muzzle{{opacity:0;fill:{CYAN};animation:muzzle {T:.3f}s ease-out infinite;transform-box:fill-box;transform-origin:center}}")
    cx = W / 2
    body.append(f'''<g class="ship">
  <g class="hover"><g transform="translate({cx} {SHIP_Y + 20}) scale(1.35) translate({-cx} {-(SHIP_Y + 20)})">
    <path d="M{cx - 7} {SHIP_Y + 34} L{cx} {SHIP_Y + 54} L{cx + 7} {SHIP_Y + 34} Z" fill="{MAGENTA}" class="flame"/>
    <path d="M{cx} {SHIP_Y} L{cx + 10} {SHIP_Y + 16} L{cx + 30} {SHIP_Y + 30} L{cx + 30} {SHIP_Y + 38} L{cx + 10} {SHIP_Y + 34}
             L{cx - 10} {SHIP_Y + 34} L{cx - 30} {SHIP_Y + 38} L{cx - 30} {SHIP_Y + 30} L{cx - 10} {SHIP_Y + 16} Z"
          fill="#0b1020" stroke="{CYAN}" stroke-width="2.5" stroke-linejoin="round" filter="url(#glow)"/>
    <path d="M{cx} {SHIP_Y + 8} L{cx + 5} {SHIP_Y + 20} L{cx - 5} {SHIP_Y + 20} Z" fill="{MAGENTA}"/>
    <circle cx="{cx - 24}" cy="{SHIP_Y + 34}" r="2" fill="{MAGENTA}" class="blink"/>
    <circle cx="{cx + 24}" cy="{SHIP_Y + 34}" r="2" fill="{MAGENTA}" class="blink"/>
  </g>
    {flashes}
  </g>
</g>''')

    # ground
    body.append(f'<line x1="36" y1="{SHIP_Y + 66}" x2="{W - 36}" y2="{SHIP_Y + 66}" stroke="{MAGENTA}" stroke-opacity=".5" stroke-width="2"/>')

    # wave cleared / idle text
    if t_clear is not None:
        css.append(f"@keyframes clear{{0%,{P(t_clear)}%{{opacity:0;transform:scale(.6)}}{P(t_clear + 0.35)}%{{opacity:1;transform:scale(1.08)}}"
                   f"{P(t_clear + 0.6)}%{{transform:scale(1)}}{P(T - 0.7)}%{{opacity:1;transform:scale(1)}}{P(T - 0.25)}%,100%{{opacity:0;transform:scale(1.3)}}}}")
        body.append(f'''<g class="clear">
  <text x="{W/2}" y="300" text-anchor="middle" font-family="{SANS}" font-size="54" font-weight="900" letter-spacing="6" fill="url(#txt)" filter="url(#glow)">WAVE CLEARED</text>
  <text x="{W/2}" y="338" text-anchor="middle" font-family="{MONO}" font-size="16" letter-spacing="4" fill="#c9d1d9">{plural(data["contributions"], "CONTRIBUTION")} DESTROYED</text>
</g>''')
        css.append(f".clear{{opacity:0;animation:clear {T:.3f}s linear infinite;transform-box:fill-box;transform-origin:center}}")
    else:
        body.append(f'''<text x="{W/2}" y="300" text-anchor="middle" font-family="{MONO}" font-size="18" letter-spacing="4" fill="#8b949e" class="blink">NO INVADERS DETECTED · WAITING FOR COMMITS</text>''')

    # ---------------------------------------------------------- screen shake on big kills
    shakes, last = [], -9
    for (ts, x, c, r, lvl, kill) in shots:
        th = ts + LASER_T
        if kill and lvl == 4 and th - last > 0.35 and len(shakes) < 80:
            shakes.append(th)
            last = th
    if shakes:
        kf = ["0%{transform:translate(0,0)}"]
        for th in shakes:
            kf += [f"{P(th - 0.005)}%{{transform:translate(0,0)}}", f"{P(th + 0.04)}%{{transform:translate(-4px,2px)}}",
                   f"{P(th + 0.08)}%{{transform:translate(3px,-2px)}}", f"{P(th + 0.13)}%{{transform:translate(0,0)}}"]
        kf.append("100%{transform:translate(0,0)}")
        css.append(f"@keyframes shake{{{''.join(kf)}}}")
        scene_style = f'style="animation:shake {T:.3f}s linear infinite"'
    else:
        scene_style = ""

    css += [
        f".cell{{opacity:0;transform-box:fill-box;transform-origin:center;animation-duration:{T:.3f}s;animation-iteration-count:infinite;animation-timing-function:linear}}",
        f".ship{{animation:ship {T:.3f}s ease-in-out infinite}}",
        ".hover{animation:hover 2.4s ease-in-out infinite}",
        "@keyframes hover{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}",
        ".flame{transform-box:fill-box;transform-origin:center top;animation:flame .12s steps(2) infinite alternate}",
        "@keyframes flame{from{transform:scaleY(.6);opacity:.7}to{transform:scaleY(1.2);opacity:1}}",
        ".blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}",
        f".ghost{{animation:ghost {T:.3f}s linear infinite}}",
        f"@keyframes ghost{{0%{{opacity:0}}{P(1.0)}%{{opacity:1}}{P(T - 0.6)}%{{opacity:1}}100%{{opacity:0}}}}",
        ".star{animation:tw 4s ease-in-out infinite}@keyframes tw{50%{opacity:.15}}",
        f".starsA{{animation:drift 30s linear infinite}}.starsB{{animation:drift 14s linear infinite}}",
        f"@keyframes drift{{from{{transform:translateY(0)}}to{{transform:translateY({H}px)}}}}",
    ]

    defs = f'''<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>
  <linearGradient id="txt" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/></linearGradient>'''
    hud, rest = body[:3], body[3:]
    content = "".join(hud) + f'<g {scene_style}>{"".join(rest)}</g>'
    return card(W, H, content, "Space Invaders", defs=defs, css="\n  ".join(css))
