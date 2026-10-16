"""Animated GitHub stats dashboard."""
from html import escape

from common import SANS, MONO, CYAN, VIOLET, MAGENTA, EMERALD, AMBER, PALETTE as FALLBACK_COLORS


# ------------------------------------------------------------------ render
def fmt(n):
    return f"{n:,}"


def rolling_number(value, cx, baseline, fs, uid, delay, fill):
    """Number whose digits roll like an odometer to the final value."""
    s = fmt(value)
    adv = fs * 0.62
    x = cx - len(s) * adv / 2
    lh = fs * 1.15
    out = [f'<clipPath id="clip{uid}"><rect x="{x - 4:.1f}" y="{baseline - fs:.1f}" '
           f'width="{len(s) * adv + 8:.1f}" height="{fs * 1.25:.1f}"/></clipPath>',
           f'<g clip-path="url(#clip{uid})" font-family="{SANS}" font-size="{fs}" font-weight="800" fill="{fill}" '
           f'style="font-variant-numeric:tabular-nums">']
    for i, ch in enumerate(s):
        cx_i = x + i * adv + adv / 2
        if ch.isdigit():
            d = int(ch)
            stack = "".join(f'<tspan x="{cx_i:.1f}" y="{baseline + k * lh:.1f}">{k % 10}</tspan>' for k in range(20))
            out.append(f'<g class="roll" style="--to:-{(10 + d) * lh:.1f}px;animation-delay:{delay + i * 0.08:.2f}s">'
                       f'<text text-anchor="middle">{stack}</text></g>')
        else:
            out.append(f'<text x="{cx_i:.1f}" y="{baseline}" text-anchor="middle">{escape(ch)}</text>')
    out.append("</g>")
    return "".join(out)


def render(s, updated):
    USERNAME = s["user"]
    W, H = 1000, 520
    parts = []

    # tiles
    tiles = [("CONTRIBUTIONS · 1Y", s["contributions"], CYAN),
             ("COMMITS · 1Y", s["commits"], VIOLET),
             ("PULL REQUESTS", s["prs"], MAGENTA),
             ("STARS", s["stars"], AMBER),
             ("REPOSITORIES", s["repos"], EMERALD)]
    tw, gap, x0, ty = 180, 10, 30, 70
    for i, (label, val, col) in enumerate(tiles):
        x = x0 + i * (tw + gap)
        d = 0.15 + i * 0.12
        parts.append(f'''<g class="pop" style="animation-delay:{d:.2f}s">
  <rect x="{x}" y="{ty}" width="{tw}" height="110" rx="14" fill="#111827" stroke="#1f2937"/>
  <rect x="{x}" y="{ty}" width="{tw}" height="110" rx="14" fill="{col}" opacity=".05"/>
  <text x="{x + tw / 2}" y="{ty + 28}" text-anchor="middle" font-family="{SANS}" font-size="11" font-weight="700" letter-spacing="1.5" fill="#8b949e">{label}</text>
  {rolling_number(val, x + tw / 2, ty + 78, 38, f"t{i}", d + 0.2, col)}
  <rect x="{x + 30}" y="{ty + 96}" width="{tw - 60}" height="3" rx="1.5" fill="{col}" class="bar" style="animation-delay:{d + 0.4:.2f}s"/>
</g>''')

    # streak ring
    px, py, pw, ph = 30, 200, 290, 290
    cx, cy, r = px + pw / 2, py + 135, 72
    circ = 2 * 3.14159265 * r
    frac = (s["current"] / s["longest"]) if s["longest"] else 0
    frac = max(0.0, min(1.0, frac))
    parts.append(f'''<g class="pop" style="animation-delay:.6s">
  <rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16" fill="#111827" stroke="#1f2937"/>
  <text x="{px + 20}" y="{py + 30}" font-family="{MONO}" font-size="13" fill="#8b949e">// streak</text>
  <circle cx="{cx}" cy="{cy}" r="{r + 16}" fill="none" stroke="{MAGENTA}" stroke-opacity=".25" stroke-width="1" stroke-dasharray="4 8" class="spin"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1f2937" stroke-width="12"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#ring)" stroke-width="12" stroke-linecap="round"
          transform="rotate(-90 {cx} {cy})" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ:.1f}" class="ring"
          style="--off:{circ * (1 - frac):.1f}" filter="url(#glow)"/>
  {rolling_number(s["current"], cx, cy + 14, 44, "ring", 0.9, "#f0f6fc")}
  <text x="{cx}" y="{cy + 40}" text-anchor="middle" font-family="{SANS}" font-size="12" font-weight="700" letter-spacing="2" fill="#8b949e">DAY STREAK</text>
  <text x="{cx}" y="{py + ph - 22}" text-anchor="middle" font-family="{SANS}" font-size="13" fill="#c9d1d9">Longest streak: <tspan font-weight="800" fill="{MAGENTA}">{fmt(s["longest"])} days</tspan></text>
</g>''')

    # languages
    lx, ly, lw, lh_ = 340, 200, 630, 140
    parts.append(f'''<g class="pop" style="animation-delay:.75s">
  <rect x="{lx}" y="{ly}" width="{lw}" height="{lh_}" rx="16" fill="#111827" stroke="#1f2937"/>
  <text x="{lx + 20}" y="{ly + 30}" font-family="{MONO}" font-size="13" fill="#8b949e">// top languages</text>''')
    langs = s["languages"]
    bx, by, bw = lx + 20, ly + 46, lw - 40
    if langs:
        parts.append(f'<clipPath id="lbar"><rect x="{bx}" y="{by}" width="{bw}" height="12" rx="6"/></clipPath>'
                     f'<rect x="{bx}" y="{by}" width="{bw}" height="12" rx="6" fill="#1f2937"/><g clip-path="url(#lbar)">')
        acc = 0.0
        for i, (name, pct, color) in enumerate(langs):
            color = color or FALLBACK_COLORS[i % len(FALLBACK_COLORS)]
            w = bw * pct / 100
            parts.append(f'<rect x="{bx + acc:.1f}" y="{by}" width="{w + 0.5:.1f}" height="12" fill="{color}" '
                         f'class="grow" style="animation-delay:{1.0 + i * 0.15:.2f}s"/>')
            acc += w
        parts.append("</g>")
        for i, (name, pct, color) in enumerate(langs):
            color = color or FALLBACK_COLORS[i % len(FALLBACK_COLORS)]
            col, row = i % 3, i // 3
            ex, ey = bx + col * (bw / 3), by + 44 + row * 28
            name = name if len(name) <= 13 else name[:12] + "…"
            parts.append(f'''<g class="fade" style="animation-delay:{1.1 + i * 0.1:.2f}s">
  <circle cx="{ex + 6}" cy="{ey - 4}" r="6" fill="{color}"/>
  <text x="{ex + 20}" y="{ey}" font-family="{SANS}" font-size="14" font-weight="600" fill="#e6edf3">{escape(name)}</text>
  <text x="{ex + bw / 3 - 24}" y="{ey}" text-anchor="end" font-family="{MONO}" font-size="13" fill="#8b949e">{pct:.1f}%</text>
</g>''')
    else:
        parts.append(f'<text x="{lx + lw / 2}" y="{ly + 90}" text-anchor="middle" font-family="{SANS}" font-size="14" '
                     f'fill="#8b949e">Languages will show up here once public repositories exist.</text>')
    parts.append("</g>")

    # activity, last 30 days
    ax, ay, aw, ah = 340, 350, 630, 140
    vals = s["last30"]
    mx = max(vals) or 1
    n = len(vals)
    slot = (aw - 40) / n
    parts.append(f'''<g class="pop" style="animation-delay:.9s">
  <rect x="{ax}" y="{ay}" width="{aw}" height="{ah}" rx="16" fill="#111827" stroke="#1f2937"/>
  <text x="{ax + 20}" y="{ay + 30}" font-family="{MONO}" font-size="13" fill="#8b949e">// last 30 days</text>
  <text x="{ax + aw - 20}" y="{ay + 30}" text-anchor="end" font-family="{SANS}" font-size="13" fill="#c9d1d9"><tspan font-weight="800" fill="{CYAN}">{fmt(sum(vals))}</tspan> contributions</text>
  <line x1="{ax + 20}" y1="{ay + ah - 18}" x2="{ax + aw - 20}" y2="{ay + ah - 18}" stroke="#30363d"/>''')
    base = ay + ah - 18
    maxh = ah - 62
    for i, v in enumerate(vals):
        h = max(3, v / mx * maxh) if v else 3
        bxx = ax + 20 + i * slot + slot * 0.18
        fill = "url(#barg)" if v else "#30363d"
        parts.append(f'<rect x="{bxx:.1f}" y="{base - h:.1f}" width="{slot * 0.64:.1f}" height="{h:.1f}" rx="2.5" '
                     f'fill="{fill}" class="up" style="animation-delay:{1.2 + i * 0.03:.2f}s"/>')
    parts.append("</g>")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="GitHub stats">
<defs>
  <linearGradient id="border" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="{H}">
    <stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/>
  </linearGradient>
  <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{MAGENTA}"/></linearGradient>
  <linearGradient id="barg" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{VIOLET}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
  <radialGradient id="bg" cx=".2" cy="0" r="1.2"><stop offset="0" stop-color="#151b33"/><stop offset="1" stop-color="#0b0f1a"/></radialGradient>
  <filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
</defs>
<style>
  .pop{{animation:pop .7s cubic-bezier(.2,.9,.3,1.2) both}}
  @keyframes pop{{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:none}}}}
  .roll{{animation:roll 1.6s cubic-bezier(.15,.85,.25,1) both}}
  @keyframes roll{{from{{transform:translateY(0)}}to{{transform:translateY(var(--to))}}}}
  .bar,.grow{{transform-box:fill-box;transform-origin:left center;animation:grow 1s cubic-bezier(.2,.8,.2,1) both}}
  @keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
  .up{{transform-box:fill-box;transform-origin:center bottom;animation:up .8s cubic-bezier(.2,.9,.3,1.3) both}}
  @keyframes up{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
  .fade{{animation:fade .6s ease-out both}}
  @keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
  .ring{{animation:ring 2s 1s cubic-bezier(.2,.8,.2,1) forwards}}
  @keyframes ring{{to{{stroke-dashoffset:var(--off)}}}}
  .spin{{transform-box:fill-box;transform-origin:center;animation:spin 18s linear infinite}}
  @keyframes spin{{to{{transform:rotate(360deg)}}}}
  .live{{animation:live 1.6s ease-in-out infinite}}
  @keyframes live{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
  .run{{stroke-dasharray:260 2800;animation:run 10s linear infinite}}
  @keyframes run{{to{{stroke-dashoffset:-3060}}}}
</style>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <circle cx="44" cy="38" r="6" fill="{EMERALD}" class="live"/>
  <text x="60" y="43" font-family="{MONO}" font-size="15" font-weight="700" fill="#e6edf3">github.stats<tspan fill="#8b949e"> --user {escape(USERNAME.lower())}</tspan></text>
  <text x="{W - 30}" y="43" text-anchor="end" font-family="{MONO}" font-size="12" fill="#8b949e">updated {updated}</text>
  {''.join(parts)}
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="21" fill="none" stroke="#ffffff" stroke-opacity=".07" stroke-width="2"/>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="21" fill="none" stroke="url(#border)" stroke-width="2.5" stroke-linecap="round" class="run"/>
</svg>'''
