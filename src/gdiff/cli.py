"""CLI entry point for gdiff."""

import sys
import os
import hashlib
import argparse
import subprocess
import webbrowser

from gdiff import __version__, __author__
from gdiff.parser import parse_diff
from gdiff.html_gen import generate_html


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def _repo_id() -> "str | None":
    """Return a short unique ID for the current git repo root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return hashlib.sha1(result.stdout.strip().encode()).hexdigest()[:16]


def _checkpoint_path(repo_id: str) -> str:
    base = os.path.join(os.path.expanduser("~"), ".config", "gdiff", "checkpoints")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, repo_id)


def _load_checkpoint(repo_id: str) -> "str | None":
    path = _checkpoint_path(repo_id)
    if os.path.exists(path):
        h = open(path).read().strip()
        return h or None
    return None


def _save_checkpoint(repo_id: str) -> None:
    """Snapshot current working tree state via git stash create (non-destructive)."""
    result = subprocess.run(
        ["git", "stash", "create"], capture_output=True, text=True
    )
    h = result.stdout.strip()
    if not h:
        # Working tree is clean - checkpoint at HEAD
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        )
        h = result.stdout.strip()
    if h:
        open(_checkpoint_path(repo_id), "w").write(h)


def _clear_checkpoint(repo_id: str) -> None:
    path = _checkpoint_path(repo_id)
    if os.path.exists(path):
        os.remove(path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Visualize git diffs in browser (VS Code inline style)",
    )
    parser.add_argument("args", nargs="*", help="Arguments passed to git diff")
    parser.add_argument(
        "--staged", "--cached", action="store_true",
        help="Show staged changes",
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Show all changes, ignoring the reviewed checkpoint",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Clear the reviewed checkpoint for this repo",
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

    # ------------------------------------------------------------------
    # Checkpoint: only active for plain `git diff` (no pipe, no --staged)
    # ------------------------------------------------------------------
    use_stdin = (not sys.stdin.isatty()) and not opts.args and not opts.staged
    use_checkpoint = (
        not use_stdin
        and not opts.staged
        and not opts.full
        and not opts.reset
    )

    repo_id = _repo_id() if use_checkpoint else None
    checkpoint = _load_checkpoint(repo_id) if repo_id else None

    # --reset: clear checkpoint and exit
    if opts.reset:
        if repo_id:
            _clear_checkpoint(repo_id)
            print("Checkpoint cleared. Next run will show all changes.")
        else:
            print("Not inside a git repository.")
        sys.exit(0)

    # ------------------------------------------------------------------
    # Get diff text
    # ------------------------------------------------------------------
    if use_stdin:
        import select
        diff_text = sys.stdin.read() if select.select([sys.stdin], [], [], 0.1)[0] else ""
    else:
        cmd = ["git", "diff", "--no-color"]
        if opts.staged:
            cmd.append("--staged")
        elif checkpoint:
            # Diff from checkpoint to current working tree
            cmd.append(checkpoint)
        cmd.extend(opts.args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and result.stderr:
            print(f"git diff error: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        diff_text = result.stdout

    if not diff_text.strip():
        if checkpoint:
            print("No new changes since last review.")
            print("  Run 'gdiff --full' to see all changes.")
            print("  Run 'gdiff --reset' to clear the checkpoint.")
        else:
            print("No diff to display.")
        sys.exit(0)

    files = parse_diff(diff_text)
    if not files:
        print("No diff to display.")
        sys.exit(0)

    # ------------------------------------------------------------------
    # Generate and open HTML
    # ------------------------------------------------------------------
    is_incremental = bool(checkpoint)
    out_path = opts.output or "/tmp/gdiff.html"
    html_content = generate_html(files, incremental=is_incremental)

    with open(out_path, "w") as f:
        f.write(html_content)

    # Save checkpoint AFTER generating, so the user sees the current state
    if repo_id and not opts.staged:
        _save_checkpoint(repo_id)

    if not opts.no_open:
        webbrowser.open(f"file://{os.path.abspath(out_path)}")
        if is_incremental:
            print(f"Showing new changes since last review. ({out_path})")
        else:
            print(f"Opened {out_path} in browser.")
    else:
        print(f"Written to {out_path}")
