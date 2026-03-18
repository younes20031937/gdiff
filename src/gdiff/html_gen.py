"""HTML generation for the diff viewer."""

import html as _html
from typing import List

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
    --del-bg: rgba(248,81,73,.15);
    --del-ln-bg: rgba(248,81,73,.30);
    --del-text: #f85149;
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
.file-section{margin:20px;border:1px solid var(--border);border-radius:8px;overflow:hidden}
.file-header{background:var(--bg-secondary);padding:10px 16px;
             border-bottom:1px solid var(--border);display:flex;
             align-items:center;gap:12px}
.file-path{font-family:var(--mono);font-size:13px;font-weight:600}
.badge{font-size:10px;padding:1px 6px;border-radius:3px;font-weight:700;text-transform:uppercase}
.badge.new{background:var(--add-bg);color:var(--add-text)}
.badge.deleted{background:var(--del-bg);color:var(--del-text)}
.table-wrap{overflow-x:auto}
table.diff{width:100%;border-collapse:collapse;table-layout:fixed;
           font-family:var(--mono);font-size:var(--fs);line-height:20px}
col.ln-col{width:var(--ln-w)}
col.code-col{width:calc(50% - var(--ln-w) - .5px)}
col.div-col{width:1px}
td{padding:0 8px;vertical-align:top;white-space:pre;overflow:hidden;text-overflow:ellipsis}
td.ln{width:var(--ln-w);min-width:var(--ln-w);text-align:right;
      color:var(--ln-text);user-select:none;padding-right:10px;
      border-right:1px solid var(--border)}
td.divider{width:1px;padding:0;background:var(--border)}
.ctx td.code{background:var(--bg-primary)}
.del td.code.del-c{background:var(--del-bg)}
.add td.code.add-c{background:var(--add-bg)}
.del td.ln.del-ln{background:var(--del-ln-bg)}
.add td.ln.add-ln{background:var(--add-ln-bg)}
.changed td.code.del-c{background:var(--del-bg)}
.changed td.code.add-c{background:var(--add-bg)}
.changed td.ln.del-ln{background:var(--del-ln-bg)}
.changed td.ln.add-ln{background:var(--add-ln-bg)}
td.code.empty-c{background:var(--bg-tertiary)}
tr.hunk td{background:var(--hunk-bg);color:var(--hunk-text);
           font-style:italic;padding:4px 16px;text-align:center}
td.code{tab-size:4;-moz-tab-size:4}
footer{text-align:center;padding:16px;color:var(--text-secondary);
       font-size:11px;border-top:1px solid var(--border);margin-top:24px}
footer a{color:var(--hunk-text);text-decoration:none}
footer a:hover{text-decoration:underline}
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
  if(e.key==='j'){cur=Math.min(cur+1,sections.length-1);
    sections[cur].scrollIntoView({behavior:'smooth',block:'start'});}
  if(e.key==='k'){cur=Math.max(cur-1,0);
    sections[cur].scrollIntoView({behavior:'smooth',block:'start'});}
});
"""


def _row_html(row: DiffRow, filename: str) -> str:
    if row.old.line_type == "hunk_header":
        ctx = _html.escape(row.old.content)
        return f'<tr class="hunk"><td colspan="5">{ctx}</td></tr>'

    old, new = row.old, row.new

    if old.line_type == "del" and new.line_type == "add":
        rc = "changed"
    elif old.line_type == "del":
        rc = "del"
    elif new.line_type == "add":
        rc = "add"
    else:
        rc = "ctx"

    # old side
    oln = str(old.line_num) if old.line_num is not None else ""
    if old.line_type == "empty":
        ocode, occ, olc = "", "empty-c", "ln"
    else:
        ocode = highlight_line(old.content, filename)
        occ = f"{old.line_type}-c"
        olc = f"{old.line_type}-ln" if old.line_type == "del" else "ln"

    # new side
    nln = str(new.line_num) if new.line_num is not None else ""
    if new.line_type == "empty":
        ncode, ncc, nlc = "", "empty-c", "ln"
    else:
        ncode = highlight_line(new.content, filename)
        ncc = f"{new.line_type}-c"
        nlc = f"{new.line_type}-ln" if new.line_type == "add" else "ln"

    return (
        f'<tr class="{rc}">'
        f'<td class="ln {olc}">{oln}</td>'
        f'<td class="code {occ}">{ocode}</td>'
        f'<td class="divider"></td>'
        f'<td class="ln {nlc}">{nln}</td>'
        f'<td class="code {ncc}">{ncode}</td>'
        f"</tr>"
    )


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
            body = (
                '<tr><td colspan="5" style="padding:16px;text-align:center;'
                'color:var(--text-secondary)">Binary file</td></tr>'
            )
        else:
            body = "\n".join(_row_html(r, fd.new_path) for r in fd.rows)

        file_sections.append(
            f'<section id="file-{idx}" class="file-section">\n'
            f'  <div class="file-header">\n'
            f'    <span class="file-path">'
            f'{_html.escape(fd.display_path)}</span>\n'
            f"    {badge}\n"
            f"  </div>\n"
            f'  <div class="table-wrap">\n'
            f'  <table class="diff">\n'
            f'    <colgroup><col class="ln-col"><col class="code-col">'
            f'<col class="div-col"><col class="ln-col">'
            f'<col class="code-col"></colgroup>\n'
            f"    <tbody>\n{body}\n    </tbody>\n"
            f"  </table>\n"
            f"  </div>\n"
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
