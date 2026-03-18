"""HTML generation for the diff viewer."""

import html as _html
import difflib
from typing import List, Tuple

from gdiff import __version__, __author__
from gdiff.parser import DiffRow, FileDiff
from gdiff.highlight import highlight_line

CSS = """\
:root {
    --bg: #1e1e1e;
    --bg-secondary: #252526;
    --bg-tertiary: #2d2d2d;
    --text: #d4d4d4;
    --text-muted: #858585;
    --border: #3e3e3e;
    --del-bg: rgba(255,0,0,.18);
    --del-ln-bg: rgba(255,0,0,.25);
    --del-gutter: #6e3030;
    --del-word: rgba(255,0,0,.40);
    --add-bg: rgba(0,180,0,.15);
    --add-ln-bg: rgba(0,180,0,.22);
    --add-gutter: #2e5d30;
    --add-word: rgba(0,180,0,.38);
    --hunk-bg: rgba(86,156,214,.08);
    --hunk-text: #569cd6;
    --ln-text: #858585;
    --mono: Consolas,'Courier New','SF Mono','Monaco',monospace;
    --fs: 13px;
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);
     font-family:'Segoe UI',-apple-system,sans-serif;line-height:1.5}

/* Header */
header{position:sticky;top:0;z-index:100;background:var(--bg-secondary);
       border-bottom:1px solid var(--border);padding:10px 20px;
       display:flex;align-items:center;gap:16px;flex-wrap:wrap}
header h1{font-size:14px;font-weight:600;color:var(--text-muted)}
.file-nav{display:flex;gap:4px;flex-wrap:wrap}
.file-nav a{color:var(--hunk-text);text-decoration:none;font-size:12px;
            padding:2px 8px;border-radius:3px;background:var(--bg-tertiary);
            font-family:var(--mono)}
.file-nav a:hover{background:var(--border)}
.stats{font-size:12px;color:var(--text-muted);margin-left:auto}
.stats .s-add{color:#4ec94e}
.stats .s-del{color:#f14c4c}

/* File sections */
.file-section{margin:16px 20px;border:1px solid var(--border);
              border-radius:4px;overflow:hidden}
.file-header{background:var(--bg-secondary);padding:8px 14px;
             border-bottom:1px solid var(--border);display:flex;
             align-items:center;gap:10px}
.file-path{font-family:var(--mono);font-size:12px;font-weight:600}
.badge{font-size:10px;padding:1px 6px;border-radius:3px;font-weight:700;
       text-transform:uppercase;letter-spacing:.3px}
.badge.new{background:var(--add-bg);color:#4ec94e}
.badge.deleted{background:var(--del-bg);color:#f14c4c}

/* Diff table */
.diff-wrap{overflow-x:auto}
table.diff{min-width:100%;width:max-content;border-collapse:collapse;
           font-family:var(--mono);font-size:var(--fs);line-height:20px}
td{padding:0;vertical-align:top;white-space:pre}
td.ln{width:50px;min-width:50px;text-align:right;color:var(--ln-text);
      user-select:none;padding-right:8px;font-size:12px}
td.ln-old{border-right:1px solid var(--border)}
td.gutter{width:16px;min-width:16px;text-align:center;font-size:11px;
          user-select:none}
td.code{padding:0 12px}

/* Row types */
tr.ctx td.code{background:var(--bg)}
tr.ctx td.ln{background:var(--bg)}
tr.ctx td.gutter{background:var(--bg)}

tr.del td.code{background:var(--del-bg)}
tr.del td.ln{background:var(--del-ln-bg)}
tr.del td.gutter{background:var(--del-gutter);color:#f14c4c}

tr.add td.code{background:var(--add-bg)}
tr.add td.ln{background:var(--add-ln-bg)}
tr.add td.gutter{background:var(--add-gutter);color:#4ec94e}

tr.hunk td{background:var(--hunk-bg);color:var(--hunk-text);
           font-style:italic;font-size:12px}
tr.hunk td.code{padding:4px 12px}

/* Word-level highlights */
.wd{border-radius:2px;padding:0 1px}
.wd-del{background:var(--del-word)}
.wd-add{background:var(--add-word)}

/* Collapsed context */
tr.fold td{background:var(--bg-secondary);text-align:center;
           color:var(--text-muted);font-size:11px;cursor:pointer;
           padding:2px 12px;border-top:1px solid var(--border);
           border-bottom:1px solid var(--border)}
tr.fold:hover td{background:var(--bg-tertiary)}

footer{text-align:center;padding:12px;color:var(--text-muted);
       font-size:11px;border-top:1px solid var(--border);margin-top:20px}
"""

JS = """\
document.querySelectorAll('.file-nav a').forEach(a=>{
  a.addEventListener('click',e=>{
    e.preventDefault();
    document.querySelector(a.getAttribute('href'))
      .scrollIntoView({behavior:'smooth',block:'start'});
  });
});
let sections=document.querySelectorAll('.file-section');
let cur=0;
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
  if(e.key==='j'){cur=Math.min(cur+1,sections.length-1);
    sections[cur].scrollIntoView({behavior:'smooth',block:'start'});}
  if(e.key==='k'){cur=Math.max(cur-1,0);
    sections[cur].scrollIntoView({behavior:'smooth',block:'start'});}
});
"""


def _word_diff(old_text: str, new_text: str) -> Tuple[str, str]:
    """Compute character-level diff, return HTML with inline highlights."""
    sm = difflib.SequenceMatcher(None, old_text, new_text, autojunk=False)
    old_parts: list = []
    new_parts: list = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        old_seg = _html.escape(old_text[i1:i2])
        new_seg = _html.escape(new_text[j1:j2])

        if tag == "equal":
            old_parts.append(old_seg)
            new_parts.append(new_seg)
        elif tag == "delete":
            old_parts.append(f'<span class="wd wd-del">{old_seg}</span>')
        elif tag == "insert":
            new_parts.append(f'<span class="wd wd-add">{new_seg}</span>')
        elif tag == "replace":
            old_parts.append(f'<span class="wd wd-del">{old_seg}</span>')
            new_parts.append(f'<span class="wd wd-add">{new_seg}</span>')

    return "".join(old_parts), "".join(new_parts)


def _inline_row(
    old_ln: str, new_ln: str, gutter: str, code_html: str, cls: str
) -> str:
    """Single table row: old_line# | new_line# | +/- gutter | code."""
    return (
        f'<tr class="{cls}">'
        f'<td class="ln ln-old">{old_ln}</td>'
        f'<td class="ln">{new_ln}</td>'
        f'<td class="gutter">{gutter}</td>'
        f'<td class="code">{code_html}</td>'
        f"</tr>"
    )


def _file_rows(rows: List[DiffRow], filename: str) -> str:
    """Generate inline diff rows for a single file (VS Code style)."""
    html_rows: list = []

    for row in rows:
        if row.old.line_type == "hunk_header":
            ctx = _html.escape(row.old.content)
            html_rows.append(
                f'<tr class="hunk">'
                f'<td class="ln ln-old"></td><td class="ln"></td>'
                f'<td class="gutter"></td>'
                f'<td class="code">{ctx}</td></tr>'
            )
            continue

        old, new = row.old, row.new
        oln = str(old.line_num) if old.line_num is not None else ""
        nln = str(new.line_num) if new.line_num is not None else ""

        # Changed pair: show deleted line then added line with word diff
        if old.line_type == "del" and new.line_type == "add":
            old_html, new_html = _word_diff(old.content, new.content)
            html_rows.append(
                _inline_row(oln, "", "\u2212", old_html, "del")
            )
            html_rows.append(
                _inline_row("", nln, "+", new_html, "add")
            )
        elif old.line_type == "del":
            html_rows.append(
                _inline_row(
                    oln, "", "\u2212",
                    highlight_line(old.content, filename), "del",
                )
            )
        elif new.line_type == "add":
            html_rows.append(
                _inline_row(
                    "", nln, "+",
                    highlight_line(new.content, filename), "add",
                )
            )
        elif old.line_type == "ctx":
            html_rows.append(
                _inline_row(
                    oln, nln, "",
                    highlight_line(old.content, filename), "ctx",
                )
            )
        # skip empty rows (padding from side-by-side) - not needed inline

    return "\n".join(html_rows)


def generate_html(files: List[FileDiff]) -> str:
    """Generate a self-contained HTML page (VS Code inline diff style)."""
    total_add = 0
    total_del = 0
    for f in files:
        for r in f.rows:
            if r.old.line_type == "del":
                total_del += 1
            if r.new.line_type == "add":
                total_add += 1

    nav_links = []
    file_sections = []

    for idx, fd in enumerate(files):
        nav_links.append(
            f'<a href="#file-{idx}">{_html.escape(fd.display_path)}</a>'
        )

        badge = ""
        if fd.is_new:
            badge = '<span class="badge new">new</span>'
        elif fd.is_deleted:
            badge = '<span class="badge deleted">deleted</span>'

        if fd.is_binary:
            table_html = (
                '<div style="padding:16px;text-align:center;'
                'color:var(--text-muted)">Binary file</div>'
            )
        else:
            rows_html = _file_rows(fd.rows, fd.new_path)
            table_html = (
                f'<div class="diff-wrap">\n'
                f'<table class="diff"><tbody>\n'
                f"{rows_html}\n"
                f"</tbody></table>\n"
                f"</div>"
            )

        file_sections.append(
            f'<section id="file-{idx}" class="file-section">\n'
            f'  <div class="file-header">\n'
            f'    <span class="file-path">'
            f"{_html.escape(fd.display_path)}</span>\n"
            f"    {badge}\n"
            f"  </div>\n"
            f"  {table_html}\n"
            f"</section>"
        )

    title = f"gdiff: {len(files)} file(s) changed"
    nav = "\n    ".join(nav_links)
    sections = "\n\n".join(file_sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
{CSS}
</style>
</head>
<body>
<header>
  <h1>gdiff</h1>
  <div class="file-nav">
    {nav}
  </div>
  <div class="stats">
    <span class="s-add">+{total_add}</span>&nbsp;
    <span class="s-del">&minus;{total_del}</span>
  </div>
</header>

{sections}

<footer>
  gdiff v{__version__} &mdash; by {__author__}
</footer>

<script>
{JS}
</script>
</body>
</html>"""
