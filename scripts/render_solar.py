"""Repo solar system: public repositories orbit a star as planets."""
import math
import random

from common import MONO, SANS, CYAN, VIOLET, MAGENTA, AMBER, PALETTE, card, esc, stars

W, H = 1000, 580
CX, CY = 500, 300
TILT = 0.34
MAX_PLANETS = 10


def shade(hex_color, f):
    """Lighten (f>0) or darken (f<0) a #rrggbb colour."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if f >= 0:
        r, g, b = (int(v + (255 - v) * f) for v in (r, g, b))
    else:
        r, g, b = (int(v * (1 + f)) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def orbit_path(rx, ry):
    # starts at the front (bottom) point, runs clockwise on screen
    return (f"M{CX},{CY + ry:.1f} A{rx:.1f},{ry:.1f} 0 1 1 {CX},{CY - ry:.1f} "
            f"A{rx:.1f},{ry:.1f} 0 1 1 {CX},{CY + ry:.1f}")


def render(data):
    rnd = random.Random(5)
    repos = sorted(data["planets"], key=lambda p: -p["size"])[:MAX_PLANETS]
    repos.sort(key=lambda p: p["created"])  # oldest = innermost
    n = len(repos)

    defs, back, front, labels, css = [], [], [], [], []

    # ---------------------------------------------------------- background
    body = [f'''<g filter="url(#neb)" opacity=".55">
  <ellipse cx="190" cy="170" rx="230" ry="120" fill="{VIOLET}" opacity=".5"/>
  <ellipse cx="830" cy="420" rx="260" ry="130" fill="{MAGENTA}" opacity=".35"/>
  <ellipse cx="760" cy="110" rx="180" ry="90" fill="{CYAN}" opacity=".3"/>
</g>''', stars(rnd, W, H, 120, rmax=1.5)]

    # ---------------------------------------------------------- orbits & planets
    if n:
        sizes = [math.log(p["size"]) for p in repos]
        lo, hi = min(sizes), max(sizes)
        ring_idx = max(range(n), key=lambda i: (repos[i]["stars"], repos[i]["size"]))
    for i, p in enumerate(repos):
        rx = 200.0 if n == 1 else 105 + i * (272 / (n - 1))
        ry = rx * TILT
        rad = 14.0 if hi == lo else 7 + 13 * (math.log(p["size"]) - lo) / (hi - lo)
        col = p["color"] or PALETTE[i % len(PALETTE)]
        period = 11 * rx / 105
        phase = rnd.uniform(0, period)
        path = orbit_path(rx, ry)

        body.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{rx:.1f}" ry="{ry:.1f}" fill="none" stroke="url(#orbit)" '
                    f'stroke-width="1.2" stroke-dasharray="2 6" opacity=".55"/>')

        defs.append(f'''<radialGradient id="pl{i}" cx=".35" cy=".3" r=".8">
    <stop offset="0" stop-color="{shade(col, .65)}"/><stop offset=".45" stop-color="{col}"/><stop offset="1" stop-color="{shade(col, -.75)}"/>
  </radialGradient>''')

        ring = ""
        if i == ring_idx and n > 1:
            ring = (f'<ellipse rx="{rad * 2.1:.1f}" ry="{rad * 0.55:.1f}" fill="none" stroke="{shade(col, .5)}" '
                    f'stroke-width="2.4" opacity=".85" transform="rotate(-18)"/>')
        moons = ""
        for m in range(min(2, p["stars"] // 3 + (1 if p["stars"] else 0))):
            mr = rad + 9 + m * 7
            moons += (f'<g><circle cx="{mr:.1f}" cy="0" r="{2.2 + m * .6:.1f}" fill="#e2e8f0"/>'
                      f'<animateTransform attributeName="transform" type="rotate" from="{m * 140} 0 0" to="{360 + m * 140} 0 0" '
                      f'dur="{4 + m * 2.5:.1f}s" repeatCount="indefinite"/></g>')

        def planet(with_ring_back):
            return (f'<circle r="{rad * 2.2:.1f}" fill="{col}" opacity=".18" filter="url(#halo)"/>'
                    f'<circle r="{rad:.1f}" fill="url(#pl{i})"/>'
                    f'<circle r="{rad:.1f}" fill="none" stroke="{shade(col, .4)}" stroke-opacity=".5" stroke-width="1"/>'
                    + ring + moons)

        motion = (f'<animateMotion dur="{period:.2f}s" begin="-{phase:.2f}s" repeatCount="indefinite" path="{path}"/>')
        scale = (f'<animateTransform attributeName="transform" type="scale" values="1.18;0.72;1.18" keyTimes="0;.5;1" '
                 f'calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" dur="{period:.2f}s" begin="-{phase:.2f}s" repeatCount="indefinite"/>')
        name = p["name"] if len(p["name"]) <= 18 else p["name"][:17] + "…"
        star_txt = f' ★{p["stars"]}' if p["stars"] else ""
        label = (f'<g transform="translate({rad + 8:.1f} {-rad - 4:.1f})"><text font-family="{MONO}" font-size="11" fill="#e6edf3">{esc(name)}'
                 f'<tspan fill="{AMBER}">{star_txt}</tspan></text></g>')
        back.append(f'<g>{motion}<g>{scale}{planet(True)}{label}</g></g>')
        front.append(f'<g>{motion}<g>{scale}{planet(False)}{label}</g></g>')

    # asteroid belt
    belt_r = 425 if n else 300
    rocks = []
    for k in range(140):
        a = rnd.uniform(0, 2 * math.pi)
        rr = belt_r + rnd.gauss(0, 10)
        rocks.append(f'<circle cx="{math.cos(a) * rr:.1f}" cy="{math.sin(a) * rr:.1f}" r="{rnd.uniform(.6, 2.1):.1f}" '
                     f'fill="{rnd.choice(["#94a3b8", "#cbd5e1", "#a78bfa", "#64748b"])}"/>')
    belt = (f'<g transform="translate({CX} {CY}) scale(1 {TILT})"><g>{"".join(rocks)}'
            f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="160s" repeatCount="indefinite"/></g></g>')

    # star
    star = f'''<g>
  <circle cx="{CX}" cy="{CY}" r="130" fill="url(#corona)" class="pulse"/>
  <g class="rays" opacity=".5">{"".join(f'<rect x="{CX - 1.5}" y="{CY - 105}" width="3" height="60" rx="1.5" fill="url(#ray)" transform="rotate({k * 30} {CX} {CY})"/>' for k in range(12))}</g>
  <circle cx="{CX}" cy="{CY}" r="40" fill="url(#core)" filter="url(#starGlow)"/>
  <circle cx="{CX}" cy="{CY}" r="40" fill="url(#core)"/>
  <circle cx="{CX - 12}" cy="{CY - 12}" r="14" fill="#fff" opacity=".55" filter="url(#halo)"/>
</g>'''

    # comets
    comets = ""
    for k, (x0, y0, x1, y1, dur, delay) in enumerate([(-80, 60, 1100, 260, 14, 2), (1100, 470, -100, 380, 19, 9)]):
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        comets += (f'<g class="comet" style="--x0:{x0}px;--y0:{y0}px;--x1:{x1}px;--y1:{y1}px;animation-duration:{dur}s;animation-delay:{delay}s">'
                   f'<g transform="rotate({ang:.1f})"><rect x="-90" y="-1.5" width="90" height="3" rx="1.5" fill="url(#tail)"/>'
                   f'<circle r="3.2" fill="#fff"/></g></g>')

    body.append(belt)
    body.append(comets)
    body.append("".join(back))
    body.append(star)
    body.append(f'<g clip-path="url(#frontHalf)">{"".join(front)}</g>')

    # HUD
    total_stars = sum(p["stars"] for p in repos)
    body.append(f'''<g font-family="{MONO}" font-size="14" font-weight="700" letter-spacing="2">
  <text x="36" y="44" fill="{CYAN}">REPO SYSTEM</text><text x="168" y="44" fill="#e6edf3">{esc(data["user"].upper())}</text>
  <text x="{W - 36}" y="44" text-anchor="end" fill="#e6edf3">{n} <tspan fill="{MAGENTA}">{"PLANET" if n == 1 else "PLANETS"}</tspan> · {total_stars} <tspan fill="{AMBER}">{"STAR" if total_stars == 1 else "STARS"}</tspan></text>
</g>''')
    if n:
        legend, seen, lx = [], [], 36
        for p in repos:
            if p["lang"] not in [s[0] for s in seen]:
                seen.append((p["lang"], p["color"] or PALETTE[len(seen) % len(PALETTE)]))
        for name, col in seen[:6]:
            if lx + 30 + len(name) * 7.6 > 540:
                break
            legend.append(f'<circle cx="{lx + 5}" cy="{H - 34}" r="5" fill="{col}"/>'
                          f'<text x="{lx + 15}" y="{H - 30}" font-family="{SANS}" font-size="12" font-weight="600" fill="#c9d1d9">{esc(name)}</text>')
            lx += 34 + len(name) * 7.6
        body.append("".join(legend))
        body.append(f'<text x="{W - 36}" y="{H - 30}" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="1.5" fill="#8b949e">'
                    f'SIZE = CODEBASE · COLOUR = LANGUAGE · ORBIT = AGE</text>')
    else:
        body.append(f'<text x="{W/2}" y="{H - 40}" text-anchor="middle" font-family="{MONO}" font-size="15" letter-spacing="4" fill="#8b949e">'
                    f'NO PLANETS YET · FIRST REPO INCOMING</text>')

    css += [
        ".star{animation:tw 5s ease-in-out infinite}@keyframes tw{50%{opacity:.12}}",
        ".pulse{transform-box:fill-box;transform-origin:center;animation:pulse 4s ease-in-out infinite}",
        "@keyframes pulse{0%,100%{transform:scale(1);opacity:.9}50%{transform:scale(1.12);opacity:.65}}",
        f".rays{{transform-origin:{CX}px {CY}px;animation:spin 40s linear infinite}}@keyframes spin{{to{{transform:rotate(360deg)}}}}",
        ".comet{opacity:0;animation-name:comet;animation-timing-function:linear;animation-iteration-count:infinite}",
        "@keyframes comet{0%{opacity:0;transform:translate(var(--x0),var(--y0))}3%{opacity:1}22%{opacity:1}"
        "25%{opacity:0;transform:translate(var(--x1),var(--y1))}100%{opacity:0;transform:translate(var(--x1),var(--y1))}}",
    ]
    d = f'''<filter id="neb" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="60"/></filter>
  <filter id="halo" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="5"/></filter>
  <filter id="starGlow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="16"/></filter>
  <radialGradient id="core" cx=".42" cy=".4" r=".7"><stop offset="0" stop-color="#ffffff"/><stop offset=".35" stop-color="#fde68a"/><stop offset=".75" stop-color="{AMBER}"/><stop offset="1" stop-color="#f472b6"/></radialGradient>
  <radialGradient id="corona" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fbbf24" stop-opacity=".55"/><stop offset=".35" stop-color="#f472b6" stop-opacity=".25"/><stop offset="1" stop-color="#a78bfa" stop-opacity="0"/></radialGradient>
  <linearGradient id="ray" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fde68a" stop-opacity=".9"/><stop offset="1" stop-color="#fde68a" stop-opacity="0"/></linearGradient>
  <linearGradient id="orbit" gradientUnits="userSpaceOnUse" x1="0" x2="{W}"><stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/></linearGradient>
  <linearGradient id="tail" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset="1" stop-color="#e0fbff"/></linearGradient>
  <clipPath id="frontHalf"><rect x="0" y="{CY}" width="{W}" height="{H - CY}"/></clipPath>
  {"".join(defs)}'''
    return card(W, H, "".join(body), "Repo solar system", defs=d, css="\n  ".join(css))
