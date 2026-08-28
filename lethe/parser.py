# parser.py does the opposite of printing: it reads a text like "(a|b)&c" and builds the tree, in two stages — a tokenizer that cuts the text into pieces, and a recursive-descent parser that turns those pieces into nodes.
# The precedence is not a number here but the order of the parser methods, and a while loop or a recursive call decides left- against right-associativity.

# For error-free use of annotations
from __future__ import annotations
# imports RegEx
import re
# helps to work with classes because it constructs default functions like __init__
from dataclasses import dataclass

from . import syntax

# Named capture groups.
# (?P<space>\s+) to filter out whitespace
# (?P<atom>[A-Za-z][0-9]*) to get atoms. Atoms are allowed to be like a, B, p1, D3
# (?P<const>[01]) to get constants "true/1" and "false/0"
# (?P<op>[!&|>=()]) to get operators  ! & | > = ( )
# (?P<unicode>[¬∧∨→↔⊤⊥]) to get unicode chars  ¬ ∧ ∨ → ↔ ⊤ ⊥
_TOKEN_PATTERN = re.compile(
    r"(?P<space>\s+)|(?P<atom>[A-Za-z][0-9]*)|(?P<const>[01])|(?P<op>[!&|>=()])|(?P<unicode>[¬∧∨→↔⊤⊥])"
)

# Accept the mathematical symbols as well, so formulas can be copied out of the thesis without rewriting them.
# Mapping them for calculations
# The editor flags the unicode keys as ambiguous characters. That warning is irrelevant here.
_UNICODE_ALIASES = {
    "¬": "!",  # not
    "∧": "&",  # and
    "∨": "|",  # or
    "→": ">",  # implies
    "↔": "=",  # iff
    "⊤": "1",  # top
    "⊥": "0",  # bottom
}

class ParseError(ValueError):
    """Raised when an input string is not a well-formed formula."""

@dataclass(frozen=True)
class _Token:
    kind: str  # "atom", "const" or "op"
    text: str
    position: int

def _tokenize(text: str) -> list[_Token]:
    # empty token list, returned at the end
    tokens: list[_Token] = []
    index = 0
    # loop over the text and apply pattern
    while index < len(text):
        match = _TOKEN_PATTERN.match(text, index)
        if match is None:
            raise ParseError(
                f"unexpected character {text[index]!r} at position {index}"
            )
        # set new index to start from for the next round.
        # Necessary because a match can be longer than one character, like a1.
        index = match.end()
        # Get the matched pattern group
        kind = match.lastgroup

        # skip whitespace tokens, they carry no meaning
        if kind == "space":
            continue
        # get the value of the matched group.
        # To decide whether a unicode char is a constant or an operator
        value = match.group()
        if kind == "unicode":
            value = _UNICODE_ALIASES[value]
            kind = "const" if value in "01" else "op"
        # add the found token to the token list
        tokens.append(_Token(kind, value, match.start()))
    return tokens


# Parese a list of given tokens. 
class _Parser:
    # constructor function
    def __init__(self, tokens: list[_Token], source: str) -> None:
        self._tokens = tokens
        self._source = source
        self._index = 0

    def _peek(self) -> _Token | None:
        if self._index < len(self._tokens):
            return self._tokens[self._index]
        return None

    def _consume_operator(self, symbol: str) -> bool:
        token = self._peek()
        if token is not None and token.kind == "op" and token.text == symbol:
            self._index += 1
            return True
        return False