#!/usr/bin/env python3
"""Check local href targets in HTML files. Skips anchors, javascript:, http(s)."""
import os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']')
SKIP_DIRS = {".git", "__pycache__", "book-output"}
skip_book = "--skip-book" in sys.argv
if skip_book:
    SKIP_DIRS.add("susv5-book")

broken = []
checked = 0
for dirpath, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if not f.endswith(".html"):
            continue
        p = os.path.join(dirpath, f)
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in HREF_RE.finditer(text):
            href = m.group(1)
            checked += 1
            if href.startswith(("#", "javascript:", "http://", "https://", "mailto:", "ftp://")):
                continue
            target = os.path.normpath(os.path.join(dirpath, href.split("#")[0]))
            if not os.path.exists(target):
                broken.append((os.path.relpath(p, ROOT), href))

print(f"links checked: {checked}")
print(f"broken: {len(broken)}")
if broken:
    cnt = Counter(h for _, h in broken)
    print("=== by target ===")
    for h, c in cnt.most_common(30):
        print(f"  {c:5d}  {h}")
    sys.exit(1)
