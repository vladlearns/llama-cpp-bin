#!/usr/bin/env python3

import json
import os
import re
import urllib.request
from pathlib import Path

REPO = os.environ["REPO"]
TAG = os.environ["TAG"]
TOKEN = os.environ["GITHUB_TOKEN"]

API_URL = f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def fetch_release():
    req = urllib.request.Request(API_URL, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def backend_from_filename(name):
    m = re.search(r"\+([a-zA-Z0-9.]+)-", name)
    if not m:
        return None
    raw = m.group(1)
    if raw.startswith("cu"):
        return raw
    if raw.startswith("rocm"):
        return "rocm"
    return raw


def generate_index():
    release = fetch_release()
    assets = [
        a
        for a in release.get("assets", [])
        if a["name"].endswith(".whl") or a["name"].endswith(".tar.gz")
    ]

    by_backend = {}
    universal = []
    for asset in assets:
        name = asset["name"]
        be = backend_from_filename(name)
        if be:
            by_backend.setdefault(be, []).append(asset)
        else:
            universal.append(asset)

    site = Path("site")
    site.mkdir(parents=True, exist_ok=True)
    (site / ".nojekyll").touch()

    all_backends = set(by_backend.keys())
    for be in all_backends:
        be_dir = site / "whl" / be / "llama-cpp-bin"
        be_dir.mkdir(parents=True, exist_ok=True)
        be_assets = by_backend[be] + universal
        links = [f'<a href="{a["browser_download_url"]}">{a["name"]}</a>' for a in be_assets]
        html = (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<body>\n"
            + "\n".join(links)
            + "\n</body>\n"
            "</html>"
        )
        (be_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"Generated {be} with {len(be_assets)} assets")


if __name__ == "__main__":
    generate_index()
