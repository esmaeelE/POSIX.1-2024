# POSIX.1-2024 (The Open Group Base Specifications, Issue 8)

The mdBook build of the POSIX.1-2024 / IEEE Std 1003.1-2024 standards documentation.

## How to read it

Open `book-output/index.html` in a browser — that is the entry point. The book is built from `susv5-book/` (generated); the HTML volumes below are the source they come from.

```
book-output/    # open this: the rendered book (mdBook output)
susv5-book/     # mdBook project source: SUMMARY.md + src/**.md + book.toml
```

## How to build it

```
python3 convert_to_mdbook.py   # HTML tree -> susv5-book/ (requires: pip install markdownify)
cd susv5-book
mdbook build                   # rebuilds book-output/
mdbook serve -o                # watch + serve the book while you work on it
```

Both `mdbook` commands must run from `susv5-book/` — that is where `book.toml` lives.

Both are reproducible; `book-output/` is generated output (gitignored).

## Structure

| Directory | Volume |
|---|---|
| `basedefs/` | XBD — Base Definitions (C headers, V1 history chapters) |
| `functions/` | XSH — System Interfaces (one page per function) |
| `utilities/` | XCU — Shell and Utilities (one page per utility) |
| `xrat/` | XRAT — Rationale (informative) |
| `frontmatter/` | Preface, notices, participants, historical chapters |
| `idx/` | Alphabetic and topical index pages |
| `help/` | Help pages and margin-code legend (`help/codes.html`) |
| `jscript/` | Small window-opening scripts used by the spec pages (`codes.js`) |
| `images/`, `Figures/` | Illustrations |

Every reference page starts with NAME / SYNOPSIS / DESCRIPTION and links to related pages (SEE ALSO) — internal links only; the HTML is self-contained.

Repo hygiene: `README.md` (this file), `convert_to_mdbook.py`, `style.css`, `jscript/`, and `help/` are maintained; `susv5-book/` and `book-output/` are generated (both gitignored).
