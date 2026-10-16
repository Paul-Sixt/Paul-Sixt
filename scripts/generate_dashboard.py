#!/usr/bin/env python3
"""Erzeugt generated/dashboard.svg – ein animiertes GitHub-Statistik-Dashboard.

Läuft automatisch im Workflow .github/workflows/profile.yml.
Benötigt nur die Python-Standardbibliothek.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape

USERNAME = os.environ.get("USERNAME", "Paul-Sixt")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT", "generated/dashboard.svg")

SANS = "'Segoe UI', Inter, -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Ubuntu, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
CYAN, VIOLET, MAGENTA, EMERALD, AMBER = "#22d3ee", "#a78bfa", "#f472b6", "#34d399", "#fbbf24"
FALLBACK_COLORS = [CYAN, VIOLET, MAGENTA, EMERALD, AMBER, "#60a5fa", "#fb7185", "#c084fc"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    pullRequests { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC,
                 orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# ------------------------------------------------------------------ Daten
def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "profile-dashboard"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors") or not payload.get("data", {}).get("user"):
        raise RuntimeError(payload.get("errors"))
    return payload["data"]["user"]


def summarize(u):
    repos = u["repositories"]["nodes"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    counts = [d["contributionCount"] for d in days]

    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    current = 0
    tail = counts[:]
    if tail and tail[-1] == 0:  # heute noch nichts – Streak zählt ab gestern
        tail = tail[:-1]
    for c in reversed(tail):
        if c > 0:
            current += 1
        else:
            break

    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            if n not in langs:
                langs[n] = [0, e["node"]["color"]]
            langs[n][0] += e["size"]
    total = sum(v[0] for v in langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]
    languages = [(n, v[0] / total * 100, v[1]) for n, v in top]

    return {
        "contributions": cal["totalContributions"],
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "prs": u["pullRequests"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "repos": u["repositories"]["totalCount"],
        "current": current,
        "longest": longest,
        "languages": languages,
        "last30": counts[-30:] if counts else [0] * 30,
    }


# ---------------------------------------------------------------- Rendern
def fmt(n):
    return f"{n:,}".replace(",", ".")


def rolling_number(value, cx, baseline, fs, uid, delay, fill):
    """Zahl, deren Ziffern wie ein Zählwerk auf den Endwert rollen."""
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
    W, H = 1000, 520
    parts = []

    # Kacheln
    tiles = [("BEITRÄGE · 12 MON.", s["contributions"], CYAN),
             ("COMMITS · 12 MON.", s["commits"], VIOLET),
             ("PULL REQUESTS", s["prs"], MAGENTA),
             ("STERNE", s["stars"], AMBER),
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

    # Streak-Ring
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
  <text x="{cx}" y="{cy + 40}" text-anchor="middle" font-family="{SANS}" font-size="12" font-weight="700" letter-spacing="2" fill="#8b949e">TAGE IN FOLGE</text>
  <text x="{cx}" y="{py + ph - 22}" text-anchor="middle" font-family="{SANS}" font-size="13" fill="#c9d1d9">Längste Serie: <tspan font-weight="800" fill="{MAGENTA}">{fmt(s["longest"])} Tage</tspan></text>
</g>''')

    # Sprachen
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
                     f'fill="#8b949e">Sobald öffentliche Repositories existieren, erscheinen hier die Sprachen.</text>')
    parts.append("</g>")

    # Aktivität letzte 30 Tage
    ax, ay, aw, ah = 340, 350, 630, 140
    vals = s["last30"]
    mx = max(vals) or 1
    n = len(vals)
    slot = (aw - 40) / n
    parts.append(f'''<g class="pop" style="animation-delay:.9s">
  <rect x="{ax}" y="{ay}" width="{aw}" height="{ah}" rx="16" fill="#111827" stroke="#1f2937"/>
  <text x="{ax + 20}" y="{ay + 30}" font-family="{MONO}" font-size="13" fill="#8b949e">// letzte 30 tage</text>
  <text x="{ax + aw - 20}" y="{ay + 30}" text-anchor="end" font-family="{SANS}" font-size="13" fill="#c9d1d9"><tspan font-weight="800" fill="{CYAN}">{fmt(sum(vals))}</tspan> Beiträge</text>
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

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="GitHub-Statistiken">
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
  <text x="{W - 30}" y="43" text-anchor="end" font-family="{MONO}" font-size="12" fill="#8b949e">aktualisiert {updated}</text>
  {''.join(parts)}
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="21" fill="none" stroke="#ffffff" stroke-opacity=".07" stroke-width="2"/>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="21" fill="none" stroke="url(#border)" stroke-width="2.5" stroke-linecap="round" class="run"/>
</svg>'''


def main():
    if "--mock" in sys.argv:
        data = {"contributions": 1287, "commits": 942, "prs": 37, "stars": 64, "repos": 18,
                "current": 12, "longest": 41,
                "languages": [("Python", 46.3, "#3572A5"), ("TypeScript", 21.8, "#3178c6"), ("Java", 12.4, "#b07219"),
                              ("C++", 9.1, "#f34b7d"), ("Jupyter Notebook", 6.2, "#DA5B0B"), ("Shell", 4.2, "#89e051")],
                "last30": [3, 5, 0, 8, 12, 4, 0, 0, 6, 9, 14, 7, 3, 2, 0, 5, 11, 16, 9, 4, 6, 0, 2, 7, 10, 13, 8, 5, 9, 12]}
    else:
        if not TOKEN:
            print("Kein GITHUB_TOKEN gesetzt – Dashboard wird nicht aktualisiert.")
            return
        try:
            data = summarize(fetch())
        except Exception as e:  # bestehendes Dashboard behalten
            print(f"Warnung: Statistiken konnten nicht geladen werden ({e}). Dashboard bleibt unverändert.")
            return
    updated = dt.datetime.now(dt.timezone.utc).strftime("%d.%m.%Y")
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(data, updated))
    print(f"{OUT} geschrieben.")


if __name__ == "__main__":
    main()
