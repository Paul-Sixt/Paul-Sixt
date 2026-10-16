"""Loads GitHub data for all generated graphics (stdlib only)."""
import datetime as dt
import json
import os
import random
import urllib.request

USERNAME = os.environ.get("USERNAME", "Paul-Sixt")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

QUERY = """
query($login: String!) {
  user(login: $login) {
    pullRequests { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC,
                 orderBy: {field: CREATED_AT, direction: ASC}) {
      totalCount
      nodes {
        name
        createdAt
        diskUsage
        stargazerCount
        primaryLanguage { name color }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount contributionLevel } }
      }
    }
  }
}
"""

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "profile-graphics"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors") or not (payload.get("data") or {}).get("user"):
        raise RuntimeError(payload.get("errors"))
    return payload["data"]["user"]


def streaks(counts):
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    tail = counts[:]
    if tail and tail[-1] == 0:  # nothing today yet -> streak counts from yesterday
        tail = tail[:-1]
    current = 0
    for c in reversed(tail):
        if c <= 0:
            break
        current += 1
    return current, longest


def summarize(u):
    repos = u["repositories"]["nodes"]
    cal = u["contributionsCollection"]["contributionCalendar"]

    # grid[week][weekday] = (count, level) or None for days outside the range
    grid = []
    for w in cal["weeks"]:
        col = [None] * 7
        for d in w["contributionDays"]:
            col[d["weekday"]] = (d["contributionCount"], LEVELS.get(d["contributionLevel"], 0))
        grid.append(col)

    days = sorted((d for w in cal["weeks"] for d in w["contributionDays"]), key=lambda d: d["date"])
    counts = [d["contributionCount"] for d in days]
    current, longest = streaks(counts)

    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"]])
            langs[n][0] += e["size"]
    total = sum(v[0] for v in langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]

    planets = []
    for r in repos:
        lang = r.get("primaryLanguage") or {}
        planets.append({
            "name": r["name"],
            "created": r["createdAt"][:10],
            "size": max(1, r.get("diskUsage") or 1),
            "stars": r["stargazerCount"],
            "lang": lang.get("name") or "Other",
            "color": lang.get("color"),
        })

    return {
        "user": USERNAME,
        "contributions": cal["totalContributions"],
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "prs": u["pullRequests"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "repos": u["repositories"]["totalCount"],
        "current": current,
        "longest": longest,
        "languages": [(n, v[0] / total * 100, v[1]) for n, v in top],
        "last30": counts[-30:] if counts else [0] * 30,
        "grid": grid,
        "planets": planets,
    }


def load():
    return summarize(fetch())


def mock(seed=4, activity=0.62, n_repos=9):
    """Realistic fake data for local previews."""
    rnd = random.Random(seed)
    end = dt.date(2026, 10, 16)
    start = end - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday
    grid, counts, d = [], [], start
    mood = 0.5
    while d <= end:
        col = [None] * 7
        for wd in range(7):
            if d > end:
                break
            mood = min(1, max(0, mood + rnd.uniform(-.25, .25)))
            active = rnd.random() < activity * (0.5 + mood) * (0.6 if wd in (0, 6) else 1)
            c = int(rnd.expovariate(1 / (2 + 9 * mood))) + 1 if active else 0
            lvl = 0 if c == 0 else 1 if c < 3 else 2 if c < 7 else 3 if c < 12 else 4
            col[wd] = (c, lvl)
            counts.append(c)
            d += dt.timedelta(days=1)
        grid.append(col)
    cur, lon = streaks(counts)
    langs = [("Python", "#3572A5"), ("TypeScript", "#3178c6"), ("Java", "#b07219"), ("C++", "#f34b7d"),
             ("Jupyter Notebook", "#DA5B0B"), ("Rust", "#dea584"), ("Go", "#00ADD8"), ("Shell", "#89e051")]
    names = ["neural-playground", "dotfiles", "algo-lab", "pixel-engine", "ml-pipeline", "tiny-compiler",
             "web-portfolio", "cli-tools", "data-viz-kit", "chess-bot", "rust-raytracer", "notes-app"]
    planets = []
    for i in range(n_repos):
        ln, col = langs[i % len(langs)]
        planets.append({"name": names[i % len(names)], "created": f"202{3 + i // 4}-0{1 + i % 9}-01",
                        "size": int(rnd.lognormvariate(7, 1.4)) + 20, "stars": int(rnd.expovariate(1 / 6)),
                        "lang": ln, "color": col})
    return {
        "user": USERNAME, "contributions": sum(counts), "commits": int(sum(counts) * .78), "prs": 37,
        "stars": sum(p["stars"] for p in planets), "repos": n_repos, "current": cur, "longest": lon,
        "languages": [("Python", 46.3, "#3572A5"), ("TypeScript", 21.8, "#3178c6"), ("Java", 12.4, "#b07219"),
                      ("C++", 9.1, "#f34b7d"), ("Jupyter Notebook", 6.2, "#DA5B0B"), ("Shell", 4.2, "#89e051")],
        "last30": counts[-30:], "grid": grid, "planets": planets,
    }
