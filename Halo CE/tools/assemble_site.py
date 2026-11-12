#!/usr/bin/env python3
"""Assembles the whole GitHub Pages site into dist/:

    python tools/assemble_site.py

    site/          ->  dist/         the launcher (index.html) and any other
                                     games kept in folders there
    build/web/site ->  dist/halo/    the game, as `ninja web` built it

The service worker of the game (dist/halo/sw.js) takes the scope of its own
folder, so the other games and the launcher are not touched by it.
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = ROOT / "site"
GAME_BUILD = ROOT / "build" / "web" / "site"
GAME_FOLDER = "halo"
DIST = ROOT / "dist"


def main() -> int:
    if not (GAME_BUILD / "halo.wasm").is_file():
        print(f"{GAME_BUILD} has no build: run `ninja web` first", file=sys.stderr)
        return 1
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(LAUNCHER, DIST)
    if (DIST / GAME_FOLDER).exists():
        print(f"site/{GAME_FOLDER} would be overwritten by the game's build: rename that folder", file=sys.stderr)
        return 1
    shutil.copytree(GAME_BUILD, DIST / GAME_FOLDER)
    (DIST / ".nojekyll").touch()
    print(f"site/ + build/web/site -> {DIST.relative_to(ROOT)}/ (the game at /{GAME_FOLDER}/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
