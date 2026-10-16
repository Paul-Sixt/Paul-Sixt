#!/usr/bin/env python3
"""Generates every data-driven graphic in generated/ (run by .github/workflows/profile.yml).

Usage: python3 scripts/generate.py          # real data (needs GITHUB_TOKEN)
       python3 scripts/generate.py --mock   # example data for local previews
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import profile_data  # noqa: E402
import render_dashboard, render_invaders, render_solar, render_tetris  # noqa: E402

OUT_DIR = os.environ.get("OUT_DIR", "generated")


def main():
    if "--mock" in sys.argv:
        data = profile_data.mock()
    else:
        if not profile_data.TOKEN:
            print("No GITHUB_TOKEN set - keeping the existing graphics.")
            return
        try:
            data = profile_data.load()
        except Exception as e:  # keep yesterday's graphics instead of failing
            print(f"Warning: could not load GitHub data ({e}). Keeping the existing graphics.")
            return

    updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    os.makedirs(OUT_DIR, exist_ok=True)
    jobs = {
        "dashboard.svg": lambda: render_dashboard.render(data, updated),
        "invaders.svg": lambda: render_invaders.render(data),
        "tetris.svg": lambda: render_tetris.render(data),
        "solar.svg": lambda: render_solar.render(data),
    }
    for name, job in jobs.items():
        try:
            svg = job()
        except Exception as e:  # one broken graphic must not block the others
            print(f"Warning: {name} failed ({e}).")
            continue
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"{name}: {len(svg) // 1024} KB")


if __name__ == "__main__":
    main()
