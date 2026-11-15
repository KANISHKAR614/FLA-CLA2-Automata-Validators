"""Task 3: pushdown automata and context-free grammars (HTML tags, if-else/while, JSON)."""

from .html_tags import build_html_pda, lex_html, G_HTML
from .stmt import build_stmt_pda, lex_stmt, G_AMB, G_STMT
from .json_pda import build_json_pda, lex_json, G_JSON

__all__ = [
    "build_html_pda", "lex_html", "G_HTML",
    "build_stmt_pda", "lex_stmt", "G_AMB", "G_STMT",
    "build_json_pda", "lex_json", "G_JSON",
]
