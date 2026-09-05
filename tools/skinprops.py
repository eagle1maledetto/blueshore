# Blueshore skin for the Zimbra Classic web client
# Copyright (C) 2026 Gianluca Zamagni, Parvati Srl
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. See the LICENSE file for details.
"""Read and merge Zimbra `skin.properties` files (stdlib only).

A properties file is a list of `Name = value` lines; values may reference
other tokens as @Name@ (resolved server-side by Zimbra, one level here for
tools that need the literal colour, e.g. the icon generator).
"""
import re

# Only blanks (not newlines) around "=": with keepends lines a \s* after "="
# would swallow the newline of an EMPTY value and push the merged value onto
# the next line (bit us with PreviewCard on 2026-08-22).
LINE_RE = re.compile(r"^([ \t]*)([A-Za-z][\w-]*)([ \t]*=[ \t]*)(.*?)[ \t]*$")


def read_raw(path, strict=False):
    """{name: value} exactly as written (aliases unresolved).

    strict=True (hand-written palettes): a line that is neither blank, a
    comment nor `Name = value`, or a name defined twice, raises ValueError
    with file and line number instead of being silently ignored. Zimbra's own
    skin.properties files are read tolerantly."""
    raw = {}
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = LINE_RE.match(line)
        if not m:
            if strict:
                raise ValueError(f"{path.name}:{n}: expected `Name = value`, got {line.strip()!r}")
            continue
        if strict and m.group(2) in raw:
            raise ValueError(f"{path.name}:{n}: {m.group(2)} is defined twice")
        raw[m.group(2)] = m.group(4)
    return raw


def read_tokens(path):
    """{name: value} with @Ref@ aliases resolved one level."""
    raw = read_raw(path)
    return {k: re.sub(r"@([\w-]+)@", lambda r: raw.get(r.group(1), r.group(0)), v)
            for k, v in raw.items()}


def merge_properties(text, overrides):
    """Replace the value of every token named in `overrides`, keeping the
    layout and comments of `text`. Returns (new_text, names_not_found)."""
    pending = dict(overrides)
    out = []
    for line in text.splitlines(keepends=True):
        m = LINE_RE.match(line)
        if m and not line.lstrip().startswith("#") and m.group(2) in pending:
            nl = "\n" if line.endswith("\n") else ""
            line = f"{m.group(1)}{m.group(2)}{m.group(3)}{pending.pop(m.group(2))}{nl}"
        out.append(line)
    return "".join(out), set(pending)
