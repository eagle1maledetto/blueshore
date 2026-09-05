#!/usr/bin/env python3
# Blueshore skin for the Zimbra Classic web client
# Copyright (C) 2026 Gianluca Zamagni, Parvati Srl
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. See the LICENSE file for details.
"""Build deployable skins from the shared source and a colour palette.

    tools/build.py tide          -> skins/blueshoretide/
    tools/build.py tide sand     -> both
    tools/build.py --all         -> every palettes/*.properties

A palette is a skin.properties fragment: `SkinName = <dir and skin name>` plus
any token of src/blueshore/skin.properties whose value changes. Copy
palettes/tide.properties to start your own variant; unknown token names,
malformed lines and duplicate names are rejected so typos cannot silently fall
back to the default colour.

The output directory is regenerated from scratch on every successful build
(a failed one leaves the previous output untouched): icons.css and
img/images.css.js are produced by gen-icons.py from the merged tokens.
"""
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from skinprops import merge_properties, read_raw  # noqa: E402

ROOT = TOOLS.parent
SRC = ROOT / "src" / "blueshore"
PALETTES = ROOT / "palettes"
SKINS = ROOT / "skins"
GENERATED = ("icons.css", "images.css.js")


def build(palette_path):
    try:
        palette = read_raw(palette_path, strict=True)
    except ValueError as e:
        sys.exit(str(e))
    name = palette.get("SkinName")
    if not name:
        sys.exit(f"{palette_path.name}: SkinName is required")
    if not name.isalnum() or not name.isascii():
        # Zimbra's SkinResources servlet strips every [^A-Za-z0-9] from the
        # skin parameter before resolving it: "blueshore-tide" silently becomes
        # "blueshoretide", which does not exist, and the default skin is served.
        sys.exit(f"{palette_path.name}: SkinName must be ASCII letters/digits only "
                 f"(Zimbra drops any other character), got {name!r}")
    text, unknown = merge_properties((SRC / "skin.properties").read_text(), palette)
    if unknown:
        sys.exit(f"{palette_path.name}: tokens not defined in src skin.properties: "
                 + ", ".join(sorted(unknown)))
    # Generate next to the final directory and swap at the end, so a palette
    # or generator error leaves the previous build of this skin untouched.
    out = SKINS / name
    tmp = SKINS / f"{name}.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    try:
        shutil.copytree(SRC, tmp, ignore=shutil.ignore_patterns(*GENERATED, "__pycache__"))
        (tmp / "skin.properties").write_text(text)
        subprocess.run([sys.executable, str(TOOLS / "gen-icons.py"), str(tmp)], check=True)
    except subprocess.CalledProcessError:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(f"{palette_path.name}: gen-icons.py failed, {out.relative_to(ROOT)}/ left as it was")
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    # Two renames instead of delete-then-rename: the previous build is put
    # back if the new one cannot take its place.
    old = SKINS / f"{name}.old"
    if old.exists():
        shutil.rmtree(old)
    if out.exists():
        out.rename(old)
    try:
        tmp.rename(out)
    except OSError:
        if old.exists():
            old.rename(out)
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    shutil.rmtree(old, ignore_errors=True)
    print(f"built {out.relative_to(ROOT)}/ from palettes/{palette_path.name}")


def main(argv):
    if not argv or argv == ["--all"]:
        paths = sorted(PALETTES.glob("*.properties")) if argv else []
        if not paths:
            sys.exit(__doc__)
    else:
        paths = [PALETTES / (a if a.endswith(".properties") else f"{a}.properties") for a in argv]
    for p in paths:
        if not p.is_file():
            sys.exit(f"no such palette: {p}")
        build(p)


if __name__ == "__main__":
    main(sys.argv[1:])
