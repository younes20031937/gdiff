"""CLI entry point for gdiff."""

import sys
import os
import argparse
import subprocess
import webbrowser

from gdiff import __version__, __author__
from gdiff.parser import parse_diff
from gdiff.html_gen import generate_html


def main():
    parser = argparse.ArgumentParser(
        description="Visualize git diffs in a side-by-side web view",
    )
    parser.add_argument("args", nargs="*", help="Arguments passed to git diff")
    parser.add_argument(
        "--staged", "--cached", action="store_true",
        help="Show staged changes",
    )
    parser.add_argument(
        "--no-open", action="store_true",
        help="Generate HTML but do not open browser",
    )
    parser.add_argument(
        "-o", "--output", type=str, default=None,
        help="Output HTML file path (default: /tmp/gdiff.html)",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"gdiff {__version__} by {__author__}",
    )

    opts = parser.parse_args()

    # If args are provided, always run git diff (don't read stdin).
    # Only read from stdin when it's piped AND no file args given.
    use_stdin = (not sys.stdin.isatty()) and not opts.args and not opts.staged

    if use_stdin:
        import select
        if select.select([sys.stdin], [], [], 0.1)[0]:
            diff_text = sys.stdin.read()
        else:
            diff_text = ""
    else:
        cmd = ["git", "diff", "--no-color"]
        if opts.staged:
            cmd.append("--staged")
        cmd.extend(opts.args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and result.stderr:
            print(
                f"git diff error: {result.stderr.strip()}", file=sys.stderr
            )
            sys.exit(1)
        diff_text = result.stdout

    if not diff_text.strip():
        print("No diff to display.")
        sys.exit(0)

    files = parse_diff(diff_text)
    if not files:
        print("No diff to display.")
        sys.exit(0)

    out_path = opts.output or "/tmp/gdiff.html"
    html_content = generate_html(files)

    with open(out_path, "w") as f:
        f.write(html_content)

    if not opts.no_open:
        webbrowser.open(f"file://{os.path.abspath(out_path)}")
        print(f"Opened {out_path} in browser.")
    else:
        print(f"Written to {out_path}")
