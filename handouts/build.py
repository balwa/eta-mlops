"""Build the class handout PDFs from the Markdown in handouts/src/.

    uv run --with markdown python handouts/build.py              # every src/*.md
    uv run --with markdown python handouts/build.py some/file.md # just one file

Each src/<name>.md becomes handouts/<name>.pdf; a file given by path gets its
PDF next to it. Needs Google Chrome installed
(it prints the HTML to PDF in headless mode). Edit the .md, run this again.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
OUT = HERE
BAND = "ETA MLOps · Weekend One · class handout"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: A4; margin: 14mm 15mm 14mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10.6pt;
       line-height: 1.45; color: #1d232a; margin: 0; }
.band { font-size: 8pt; letter-spacing: .06em; text-transform: uppercase; color: #6b7785;
        border-bottom: 2px solid #e4572e; padding-bottom: 4px; margin-bottom: 12px; }
h1 { font-size: 20pt; margin: 0 0 4px; color: #12263a; line-height: 1.15; }
h2 { font-size: 13pt; margin: 16px 0 6px; color: #12263a; border-bottom: 1px solid #dde3ea;
     padding-bottom: 3px; break-after: avoid; }
h3 { font-size: 11pt; margin: 12px 0 4px; color: #12263a; break-after: avoid; }
p { margin: 5px 0; }
ul, ol { margin: 4px 0 6px; padding-left: 22px; }
li { margin: 2px 0; }
code { font-family: Menlo, "SF Mono", Consolas, monospace; font-size: 9pt;
       background: #f1f4f7; padding: 1px 4px; border-radius: 3px; }
pre { background: #0f1b2a; color: #e8eef5; padding: 8px 11px; border-radius: 6px;
      margin: 5px 0 8px; overflow: hidden; white-space: pre-wrap; word-break: break-word;
      break-inside: avoid; }
pre code { background: none; color: inherit; padding: 0; font-size: 8.8pt; line-height: 1.4; }
pre.out { background: #f6f8fa; color: #24303c; border: 1px solid #dde3ea; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px; font-size: 9.4pt;
        break-inside: avoid; }
th, td { border: 1px solid #dde3ea; padding: 4px 7px; text-align: left; vertical-align: top; }
th { background: #f1f4f7; }
blockquote { margin: 8px 0; padding: 7px 11px; border-radius: 6px; border-left: 4px solid #8a99a8;
             background: #f6f8fa; break-inside: avoid; }
blockquote p { margin: 3px 0; }
blockquote.tip   { border-left-color: #2a9d8f; background: #eef8f6; }
blockquote.stuck { border-left-color: #e9a23b; background: #fdf6ea; }
blockquote.think { border-left-color: #5b6ee1; background: #f0f2fd; }
blockquote.warn  { border-left-color: #e4572e; background: #fdf0ec; }
.meta { color: #4a5663; margin: 2px 0 10px; }
.meta strong { color: #12263a; }
hr { border: none; border-top: 1px dashed #c9d2db; margin: 12px 0; }
.pb { break-before: page; }
"""

CALLOUTS = {"tip": "tip", "stuck": "stuck", "think": "think", "careful": "warn",
            "important": "warn", "say": "think", "fallback": "stuck", "note": "tip"}


def to_html(md_text: str) -> str:
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
    # > **Tip** ...  ->  <blockquote class="tip">
    def cls(m: re.Match) -> str:
        word = m.group(1).strip().rstrip(":?!").lower().split()[0]
        return f'<blockquote class="{CALLOUTS.get(word, "")}">\n<p><strong>{m.group(1)}'
    body = re.sub(r"<blockquote>\s*<p><strong>([^<]+)", cls, body)
    # ```text blocks are program output: light style
    body = body.replace('<pre><code class="language-text">', '<pre class="out"><code>')
    # <p class="meta"> for the line right under the title
    body = re.sub(r"<p>(<strong>File:)", r'<p class="meta">\1', body, count=1)
    body = body.replace("<p>[[pagebreak]]</p>", '<div class="pb"></div>')
    return body


def build(md: Path, band: str, out: Path = OUT) -> Path:
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>{md.stem}</title>'
            f"<style>{CSS}</style></head><body><div class=\"band\">{band}</div>"
            f"{to_html(md.read_text())}</body></html>")
    pdf = out / f"{md.stem}.pdf"
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / f"{md.stem}.html"
        page.write_text(html)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", page.as_uri()],
                       check=True, capture_output=True)
    return pdf


def main() -> None:
    files = [Path(a).resolve() for a in sys.argv[1:]]
    if files:
        for md in files:
            band = "instructor only · do not share" if "instructor" in md.name else BAND
            print("wrote", build(md, band, md.parent))
        return
    for md in sorted(SRC.glob("*.md")):
        print("wrote", build(md, BAND).relative_to(HERE.parent))


if __name__ == "__main__":
    main()
