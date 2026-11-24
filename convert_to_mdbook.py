#!/usr/bin/env python3
"""Convert SUSv5 HTML to mdBook format."""
import re, shutil
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

SRC = Path(__file__).resolve().parent
DST = SRC / "susv5-book"


class POSIXConverter(MarkdownConverter):
    def convert_pre(self, el, text, parent_tags):
        return "\n```\n%s\n```\n" % text if text else ""


def clean_html(html_text):
    soup = BeautifulSoup(html_text, "lxml")
    # Convert <tt> to <code> so markdownify renders backticks
    for tt in soup.find_all("tt"):
        tt.name = "code"
    for div in soup.find_all("div", class_="NAVHEADER"):
        div.decompose()
    for div in soup.find_all("div", class_="NAVFOOTER"):
        div.decompose()
    for script in soup.find_all("script"):
        script.decompose()
    for center in soup.find_all("center"):
        t = center.get_text()
        if "Open Group" in t or "IEEE Std" in t or ("Copyright" in t and len(t) < 200):
            center.decompose()
    for bf in soup.find_all("basefont"):
        bf.decompose()
    for hr in soup.find_all("hr"):
        if hr.get("noshade"):
            hr.decompose()
    for a in soup.find_all("a"):
        if "return to top" in a.get_text():
            nxt = a.find_next_sibling()
            if nxt and nxt.name == "br":
                nxt.decompose()
            a.decompose()
    for center in soup.find_all("center"):
        t = center.get_text()
        if "Main Index" in t or ("XBD" in t and "XSH" in t):
            center.decompose()
    for div in soup.find_all("div", class_="box"):
        em = div.find("em")
        if em and "End of informative text" in em.get_text():
            div.decompose()
    for img in soup.find_all("img"):
        s = img.get("src", "")
        if "opt-start" in s:
            img.replace_with("[")
        elif "opt-end" in s:
            img.replace_with("]")
    for a in soup.find_all("a"):
        h = a.get("href", "")
        if h.startswith("javascript:"):
            a.unwrap()
    # Remove margin-legend sups like [OH], [OF], [XSI].
    for sup in soup.find_all("sup"):
        if re.match(r'^\[[A-Z]{2,5}\]$', sup.get_text(strip=True)):
            sup.decompose()
    # Render SYNOPSIS blocks as <pre> to avoid broken inline-code blockquotes.
    for bq in soup.find_all("blockquote", class_="synopsis"):
        for sup in bq.find_all("sup"):
            if sup.get_text(strip=True).startswith("["):
                sup.decompose()
        for br in bq.find_all("br"):
            br.replace_with("\n")
        text = bq.get_text()
        text = re.sub(r'[ \t]+\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text).strip('\n')
        # Collapse whitespace inside [...] option groups in synopses.
        text = re.sub(r'\[([^\[\]]*)\]', lambda m: '[' + ' '.join(m.group(1).split()) + ']', text)
        pre = soup.new_tag("pre")
        pre.string = text
        bq.replace_with(pre)
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if not href or href.startswith(("#", "javascript:", "http")):
            continue
        frag = ""
        if "#" in href:
            hb, frag = href.split("#", 1)
            frag = "#" + frag
        else:
            hb = href
        if hb.startswith("http") or "download" in hb:
            continue
        if hb.endswith(".html"):
            a["href"] = hb.replace(".html", ".md") + frag
    return str(soup)


def escape_stray_tokens(text):
    """Escape stray POSIX metatokens (e.g. <tilde>, <National Body>) outside
    fenced/inline code so markdown readers don't parse them as unclosed
    HTML tags."""
    # Split on fenced code blocks and inline code spans to avoid mangling code.
    _split_re = re.compile(r'(```.*?```|``(?:[^`]|`(?!`))*?``|`[^`\n]+`)', re.S)
    # POSIX placeholder tokens: <word>, <word-word>, <Word Word>, possibly across a line break.
    # Avoid matching HTML comments/closing tags; allow after word chars (e.g. From<space>).
    _token_re = re.compile(r'<([A-Za-z][A-Za-z0-9-]*(?:[ \n][A-Za-z0-9-]+)*)>')
    parts = []
    idx = 0
    for m in _split_re.finditer(text):
        parts.append(_token_re.sub(r'&lt;\1&gt;', text[idx:m.start()]))
        parts.append(m.group(0))
        idx = m.end()
    parts.append(_token_re.sub(r'&lt;\1&gt;', text[idx:]))
    return ''.join(parts)


def html_to_md(html_file):
    html_text = html_file.read_text(encoding="utf-8", errors="replace")
    cleaned = clean_html(html_text)
    conv = POSIXConverter(heading_style="ATX", bullets="-", strong_em_symbol="*")
    m = conv.convert(cleaned)
    m = escape_stray_tokens(m)
    m = re.sub(r'\n{4,}', '\n\n\n', m)
    lines = [l.rstrip() for l in m.split('\n')]
    return '\n'.join(lines).strip() + '\n'


def parse_ul_entries(ul, depth=0):
    entries = []
    for li in ul.find_all("li", recursive=False):
        a = li.find("a", recursive=False)
        if not a:
            continue
        title = a.get_text().strip()
        href = a.get("href", "")
        if href:
            hc = href.split("#")[0]
            if hc.startswith("../"):
                hc = hc[3:]
            elif hc.startswith("./"):
                hc = hc[2:]
            if hc.endswith(".html"):
                hc = hc.replace(".html", ".md")
            entries.append((depth + 1, title, hc))
        sub = li.find("ul", recursive=False)
        if sub:
            entries.extend(parse_ul_entries(sub, depth + 1))
    return entries


def build_toc(html_file):
    soup = BeautifulSoup(html_file.read_text(encoding="utf-8", errors="replace"), "lxml")
    h2 = soup.find("h2")
    sname = h2.get_text().strip() if h2 else html_file.stem
    for h2e in soup.find_all("h2"):
        if "Table of Contents" in h2e.get_text():
            nxt = h2e.find_next_sibling()
            while nxt:
                if nxt.name == "ul":
                    return sname, parse_ul_entries(nxt)
                nxt = nxt.find_next_sibling()
            break
    return sname, []


def convert_vol(src_dir, dst_dir):
    dst_dir.mkdir(parents=True, exist_ok=True)
    sname, tocs = build_toc(src_dir / "contents.html")
    cnt = 0
    for hf in sorted(src_dir.glob("*.html")):
        if hf.name == "toc.html":
            continue
        try:
            (dst_dir / (hf.stem + ".md")).write_text(html_to_md(hf), encoding="utf-8")
        except Exception as e:
            print("  ERR %s: %s" % (hf.name, e))
            (dst_dir / (hf.stem + ".md")).write_text("# %s\n\n> Error: %s\n" % (hf.stem, e), encoding="utf-8")
        cnt += 1
    return sname, tocs, cnt


def main():
    print("=== SUSv5 HTML to mdBook ===")
    missing = []
    for mod in ("bs4", "markdownify"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        raise SystemExit(
            "Missing Python dependencies: %s\n"
            "Install with: pip install %s (needs Python >= 3.8)" % (", ".join(missing), " ".join(missing))
        )
    if DST.exists():
        # Reset only the generated src/ tree; book.toml and theme/ are
        # hand-maintained and not produced by this script.
        shutil.rmtree(DST / "src", ignore_errors=True)
    DST.mkdir(exist_ok=True)
    (DST / "src").mkdir(exist_ok=True)
    for d in ["frontmatter", "basedefs", "functions", "utilities", "xrat"]:
        (DST / "src" / d).mkdir()
    for im in ["images", "Figures"]:
        si = SRC / im
        if si.exists():
            shutil.copytree(si, DST / "src" / im.lower())
            print("Copied %s/" % im)
    print("Converting frontmatter...")
    for f in sorted((SRC / "frontmatter").glob("*.html")):
        (DST / "src" / "frontmatter" / (f.stem + ".md")).write_text(html_to_md(f), encoding="utf-8")
    mi = SRC / "mindex.html"
    if mi.exists():
        (DST / "src" / "intro.md").write_text(html_to_md(mi), encoding="utf-8")
        print("  mindex.html -> intro.md")
    cp = SRC / "copyr.html"
    if cp.exists():
        (DST / "src" / "copyr.md").write_text(html_to_md(cp), encoding="utf-8")
        print("  copyr.html -> copyr.md")
    vols = []
    for vd, vl in [("basedefs", "Base Definitions (XBD)"), ("functions", "System Interfaces (XSH)"), ("utilities", "Shell and Utilities (XCU)"), ("xrat", "Rationale (XRAT)")]:
        print("Converting %s..." % vl)
        sn, tc, c = convert_vol(SRC / vd, DST / "src" / vd)
        th = SRC / vd / "toc.html"
        if th.exists():
            (DST / "src" / vd / "toc.md").write_text(html_to_md(th), encoding="utf-8")
        print("  %d pages" % c)
        vols.append((vd, sn, tc, c))
    print("Building SUMMARY.md...")
    L = ["# Summary\n", "\n", "[Introduction](./intro.md)\n"]
    L.append("\n---\n")
    L.append("*Frontmatter*\n")
    for f in sorted((DST / "src" / "frontmatter").glob("*.md")):
        t = f.stem.replace("_", " ").title()
        L.append("[%s](frontmatter/%s)\n" % (t, f.name))
    L.append("\n---\n")
    L.append("[Copyright](./copyr.md)\n")
    for vd, sn, tc, c in vols:
        L.append("\n---\n")
        L.append("*%s*\n" % sn)
        L.append("[Table of Contents](%s/toc.md)\n" % vd)
        seen = set()
        for depth, title, mp in tc:
            if mp in seen:
                continue
            seen.add(mp)
            t = title.replace("[", "\\[").replace("]", "\\]")
            indent = "  " * (depth - 1)
            L.append("%s[%s](%s)\n" % (indent, t, mp))
        excl = set()
        for depth, title, mp in tc:
            excl.add(mp)
        listing = sorted(f.stem for f in (DST / "src" / vd).glob("*.md") if f.stem not in excl and f.stem != "toc")
        idxname = {"basedefs": "header-index", "functions": "function-index", "utilities": "utility-index"}.get(vd)
        if idxname and listing:
            idx_lines = ["# %s Index\n\n" % vd.capitalize()]
            for n in listing:
                idx_lines.append("- [%s](%s.md)\n" % (n, n))
            (DST / "src" / vd / (idxname + ".md")).write_text("".join(idx_lines), encoding="utf-8")
            L.append("[Index](%s/%s.md)\n" % (vd, idxname))
    (DST / "src" / "SUMMARY.md").write_text("".join(L), encoding="utf-8")
    total = sum(1 for _ in DST.rglob("*.md"))
    print("Done! %d markdown files, SUMMARY.md %d lines" % (total, len(L)))


if __name__ == "__main__":
    main()
