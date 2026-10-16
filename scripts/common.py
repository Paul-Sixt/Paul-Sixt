"""Shared style constants and SVG helpers."""
from html import escape

SANS = "'Segoe UI', Inter, -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Ubuntu, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

CYAN, VIOLET, MAGENTA = "#22d3ee", "#a78bfa", "#f472b6"
EMERALD, AMBER, BLUE, ROSE = "#34d399", "#fbbf24", "#60a5fa", "#fb7185"
PALETTE = [CYAN, VIOLET, MAGENTA, EMERALD, AMBER, BLUE, ROSE, "#c084fc"]

# contribution level 0..4 -> neon colour
LEVEL_COLORS = ["#161b22", "#4c1d95", "#7c3aed", "#c026d3", "#22d3ee"]


def esc(s):
    return escape(str(s))


def fmt(n):
    return f"{n:,}"


def pct(t, total):
    """Seconds -> keyframe percentage string, clamped to 0..100."""
    return f"{max(0.0, min(100.0, t / total * 100)):.3f}"


def card(W, H, body, label, defs="", css="", bg="url(#bgGrad)"):
    """Dark rounded card with animated neon border, shared by all generated graphics."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(label)}">
<defs>
  <linearGradient id="borderGrad" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="{H}">
    <stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/>
  </linearGradient>
  <radialGradient id="bgGrad" cx=".2" cy="0" r="1.2"><stop offset="0" stop-color="#151b33"/><stop offset="1" stop-color="#0b0f1a"/></radialGradient>
  <clipPath id="cardClip"><rect width="{W}" height="{H}" rx="22"/></clipPath>
  {defs}
</defs>
<style>
  .borderRun{{stroke-dasharray:260 {2 * (W + H)};animation:borderRun 10s linear infinite}}
  @keyframes borderRun{{to{{stroke-dashoffset:-{2 * (W + H) + 260}}}}}
  {css}
</style>
<g clip-path="url(#cardClip)">
  <rect width="{W}" height="{H}" fill="{bg}"/>
  {body}
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="21" fill="none" stroke="#ffffff" stroke-opacity=".07" stroke-width="2"/>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="21" fill="none" stroke="url(#borderGrad)" stroke-width="2.5" stroke-linecap="round" class="borderRun"/>
</svg>'''


def stars(rnd, W, H, n, cls="star", rmax=1.6):
    out = []
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(0.5, rmax)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#e2e8f0" class="{cls}" '
                   f'style="animation-delay:-{rnd.uniform(0, 6):.2f}s;opacity:{rnd.uniform(.2, .9):.2f}"/>')
    return "".join(out)
