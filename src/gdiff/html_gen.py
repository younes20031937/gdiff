"""HTML generation for the diff viewer."""

import html as _html
import difflib
from typing import List, Tuple

from gdiff import __version__, __author__
from gdiff.parser import DiffRow, FileDiff
from gdiff.highlight import highlight_line

CSS = """\
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --border: #30363d;
    --add-bg: rgba(46,160,67,.15);
    --add-ln-bg: rgba(46,160,67,.30);
    --add-text: #3fb950;
    --add-word-bg: rgba(46,160,67,.45);
    --del-bg: rgba(248,81,73,.15);
    --del-ln-bg: rgba(248,81,73,.30);
    --del-text: #f85149;
    --del-word-bg: rgba(248,81,73,.45);
    --hunk-bg: rgba(56,139,253,.10);
    --hunk-text: #58a6ff;
    --ln-text: #484f58;
    --ln-w: 52px;
    --mono: 'SF Mono','Monaco','Inconsolata','Fira Code','Droid Sans Mono',
            'Source Code Pro', monospace;
    --fs: 13px;
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg-primary);color:var(--text-primary);
     font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.5}
header{position:sticky;top:0;z-index:100;background:var(--bg-secondary);
       border-bottom:1px solid var(--border);padding:12px 24px;
       display:flex;align-items:center;gap:20px;flex-wrap:wrap}
header h1{font-size:18px;font-weight:600}
.file-nav{display:flex;gap:6px;flex-wrap:wrap}
.file-nav a{color:var(--hunk-text);text-decoration:none;font-size:12px;
            padding:2px 8px;border-radius:4px;background:var(--bg-tertiary);
            font-family:var(--mono)}
.file-nav a:hover{background:var(--border)}
.stats{font-size:12px;color:var(--text-secondary);margin-left:auto}
.stats .add-count{color:var(--add-text)}
.stats .del-count{color:var(--del-text)}
.file-section{margin:20px;border:1px solid var(--border);border-radius:8px;
              overflow:hidden}
.file-header{background:var(--bg-secondary);padding:10px 16px;
             border-bottom:1px solid var(--border);display:flex;
             align-items:center;gap:12px}
.file-path{font-family:var(--mono);font-size:13px;font-weight:600}
.badge{font-size:10px;padding:1px 6px;border-radius:3px;font-weight:700;
       text-transform:uppercase}
.badge.new{background:var(--add-bg);color:var(--add-text)}
.badge.deleted{background:var(--del-bg);color:var(--del-text)}
.diff-container{display:flex;overflow:hidden}
.diff-side{flex:1;min-width:0;overflow-x:auto}
.diff-side table{width:100%;border-collapse:collapse;
                 font-family:var(--mono);font-size:var(--fs);line-height:20px}
.diff-divider{width:1px;min-width:1px;background:var(--border);flex-shrink:0}
td{padding:0 8px;vertical-align:top;white-space:pre}
td.ln{width:var(--ln-w);min-width:var(--ln-w);text-align:right;
      color:var(--ln-text);user-select:none;padding-right:10px;
      border-right:1px solid var(--border);position:sticky;left:0;z-index:1}
td.code{tab-size:4;-moz-tab-size:4}
tr.ctx td.code{background:var(--bg-primary)}
tr.ctx td.ln{background:var(--bg-primary)}
tr.del td.code{background:var(--del-bg)}
tr.del td.ln{background:var(--del-ln-bg)}
tr.add td.code{background:var(--add-bg)}
tr.add td.ln{background:var(--add-ln-bg)}
tr.empty td.code{background:var(--bg-tertiary)}
tr.empty td.ln{background:var(--bg-tertiary)}
tr.hunk td{background:var(--hunk-bg);color:var(--hunk-text);
           font-style:italic;padding:4px 16px;text-align:center}
tr.hunk td.ln{background:var(--hunk-bg)}
.wd{border-radius:3px;padding:1px 1px}
.wd-del{background:var(--del-word-bg)}
.wd-add{background:var(--add-word-bg)}
footer{text-align:center;padding:16px;color:var(--text-secondary);
       font-size:11px;border-top:1px solid var(--border);margin-top:24px}
footer a{color:var(--hunk-text);text-decoration:none}
footer a:hover{text-decoration:underline}
"""

JS = """\
// Keyboard navigation between files
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

// Sync vertical scroll between left and right panels
document.querySelectorAll('.diff-container').forEach(container=>{
  const sides=container.querySelectorAll('.diff-side');
  if(sides.length!==2)return;
  let syncing=false;
  sides.forEach((side,i)=>{
    side.addEventListener('scroll',()=>{
      if(syncing)return;
      syncing=true;
      const other=sides[1-i];
      other.scrollTop=side.scrollTop;
      syncing=false;
    });
  });
});
"""


def _word_diff(old_text: str, new_text: str) -> Tuple[str, str]:
    """Compute word-level diff and return HTML with inline highlights.

    Splits lines into character-level tokens and uses SequenceMatcher
    to find exactly which segments changed.
    """
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


def _side_row(line_num: str, code_html: str, row_cls: str) -> str:
    """Generate a single <tr> for one side of the diff."""
    return (
        f'<tr class="{row_cls}">'
        f'<td class="ln">{line_num}</td>'
        f'<td class="code">{code_html}</td>'
        f"</tr>"
    )


def _rows_html(
    rows: List[DiffRow], filename: str
) -> Tuple[str, str]:
    """Generate left-side and right-side table rows for a file."""
    left_rows: list = []
    right_rows: list = []

    for row in rows:
        if row.old.line_type == "hunk_header":
            ctx = _html.escape(row.old.content)
            hunk = (
                f'<tr class="hunk">'
                f'<td class="ln"></td>'
                f'<td class="code">{ctx}</td>'
                f"</tr>"
            )
            left_rows.append(hunk)
            right_rows.append(hunk)
            continue

        old, new = row.old, row.new
        oln = str(old.line_num) if old.line_num is not None else ""
        nln = str(new.line_num) if new.line_num is not None else ""

        # Changed line pair: compute word-level diff
        if old.line_type == "del" and new.line_type == "add":
            old_html, new_html = _word_diff(old.content, new.content)
            left_rows.append(_side_row(oln, old_html, "del"))
            right_rows.append(_side_row(nln, new_html, "add"))
        else:
            # Old side
            if old.line_type == "empty":
                left_rows.append(_side_row("", "", "empty"))
            elif old.line_type == "del":
                left_rows.append(
                    _side_row(oln, highlight_line(old.content, filename), "del")
                )
            else:
                left_rows.append(
                    _side_row(oln, highlight_line(old.content, filename), "ctx")
                )

            # New side
            if new.line_type == "empty":
                right_rows.append(_side_row("", "", "empty"))
            elif new.line_type == "add":
                right_rows.append(
                    _side_row(
                        nln, highlight_line(new.content, filename), "add"
                    )
                )
            else:
                right_rows.append(
                    _side_row(
                        nln, highlight_line(new.content, filename), "ctx"
                    )
                )

    return "\n".join(left_rows), "\n".join(right_rows)


def generate_html(files: List[FileDiff]) -> str:
    """Generate a self-contained HTML page for the given file diffs."""
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
            body_inner = (
                '<div class="diff-container">'
                '<div style="padding:16px;text-align:center;width:100%;'
                'color:var(--text-secondary)">Binary file</div></div>'
            )
        else:
            left_html, right_html = _rows_html(fd.rows, fd.new_path)
            body_inner = (
                f'<div class="diff-container">\n'
                f'  <div class="diff-side">\n'
                f"    <table><tbody>\n{left_html}\n    </tbody></table>\n"
                f"  </div>\n"
                f'  <div class="diff-divider"></div>\n'
                f'  <div class="diff-side">\n'
                f"    <table><tbody>\n{right_html}\n    </tbody></table>\n"
                f"  </div>\n"
                f"</div>"
            )

        file_sections.append(
            f'<section id="file-{idx}" class="file-section">\n'
            f'  <div class="file-header">\n'
            f'    <span class="file-path">'
            f"{_html.escape(fd.display_path)}</span>\n"
            f"    {badge}\n"
            f"  </div>\n"
            f"  {body_inner}\n"
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
    <span class="add-count">+{total_add}</span>&nbsp;
    <span class="del-count">-{total_del}</span>
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
