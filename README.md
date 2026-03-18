# gdiff

A web-based side-by-side git diff viewer. Generates a self-contained HTML page with syntax highlighting and opens it in your browser.

No more squinting at terminal diffs - see your changes clearly, side by side.

## Installation

```bash
pip install gdiff
```

For syntax highlighting (recommended):

```bash
pip install gdiff[highlight]
```

## Quick Start

```bash
gdiff path/to/file.py
```

This runs `git diff` on the file, generates an HTML page, and opens it in your browser.

## Usage

```bash
# Diff a specific file
gdiff path/to/file.py

# Staged changes
gdiff --staged path/to/file.py

# All unstaged changes
gdiff

# Pipe mode
git diff | gdiff

# Save without opening browser
gdiff --no-open -o diff.html

# Compare branches/commits
gdiff main..feature -- path/to/file.py

# Check version
gdiff --version
```

## Features

- **Side-by-side view** - old code on the left, new code on the right
- **Syntax highlighting** - 500+ languages via [Pygments](https://pygments.org/)
- **Dark theme** - GitHub-dark inspired, easy on the eyes
- **Line numbers** - on both sides for quick reference
- **File navigation** - sticky header with clickable jump links
- **Keyboard navigation** - `j`/`k` to jump between files
- **Multi-file support** - view all changed files in one page
- **Zero config** - works out of the box, no setup needed
- **Fully offline** - self-contained HTML, no external dependencies
- **Lightweight** - pure Python, no heavy frameworks

## How It Works

1. Runs `git diff` (or reads piped input)
2. Parses the unified diff into structured data
3. Generates a self-contained HTML file with inline CSS/JS
4. Opens it in your default browser

The generated HTML has no external dependencies - it works fully offline.

## Requirements

- Python 3.8+
- Git (must be available in PATH)
- [Pygments](https://pygments.org/) (optional, for syntax highlighting)

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

[MIT](LICENSE) - Younes Boukdir
