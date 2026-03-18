"""Syntax highlighting via pygments (optional dependency)."""

import os
import html as _html

try:
    from pygments import highlight as pygments_highlight
    from pygments.lexers import guess_lexer_for_filename, TextLexer
    from pygments.formatters import HtmlFormatter

    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False

_lexer_cache: dict = {}
_formatter = (
    HtmlFormatter(nowrap=True, noclasses=True, style="monokai")
    if HAS_PYGMENTS
    else None
)


def highlight_line(code: str, filename: str) -> str:
    """Syntax-highlight a single line, returning inline-styled HTML."""
    if not HAS_PYGMENTS:
        return _html.escape(code)
    ext = os.path.splitext(filename)[1]
    if ext not in _lexer_cache:
        try:
            _lexer_cache[ext] = guess_lexer_for_filename(filename, "")
        except Exception:
            _lexer_cache[ext] = TextLexer()
    return pygments_highlight(
        code + "\n", _lexer_cache[ext], _formatter
    ).rstrip("\n")
