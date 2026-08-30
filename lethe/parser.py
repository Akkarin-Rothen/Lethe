# parser.py does the opposite of printing: it reads a text like "(a|b)&c" and builds the tree, in two stages — a tokenizer that cuts the text into pieces, and a recursive-descent parser that turns those pieces into nodes.
# The precedence is not a number here but the order of the parser methods, and a while loop or a recursive call decides left- against right-associativity.

# For error-free use of annotations
from __future__ import annotations
# imports RegEx
import re
# helps to work with classes because it constructs default functions like __init__
from dataclasses import dataclass

from .syntax import (
    And,
    Atom,
    BOTTOM,
    Formula,
    Iff,
    Implies,
    Not,
    Or,
    TOP,
)


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
            if value in "01":
                kind = "const"
            else:
                kind = "op"
        # add the found token to the token list
        tokens.append(_Token(kind, value, match.start()))
    return tokens


# Parse a list of given tokens.
class _Parser:
    # constructor function
    def __init__(self, tokens: list[_Token], source: str) -> None:
        self._tokens = tokens
        # only used for error messages
        self._source = source
        # read position in the token list
        self._index = 0

    # gives the next token without moving the read position
    # returns None at the end of the list, that is not an error here
    def _peek(self) -> _Token | None:
        if self._index < len(self._tokens):
            return self._tokens[self._index]
        return None

    # moves one step forward only if the next token is that operator
    # returns False and changes nothing otherwise
    def _consume_operator(self, symbol: str) -> bool:
        token = self._peek()
        if token is not None and token.kind == "op" and token.text == symbol:
            self._index += 1
            return True
        return False

    # rejects an empty list, builds the tree, then rejects leftover tokens
    def parse(self) -> Formula:
        if not self._tokens:
            raise ParseError("empty formula")
        formula = self._iff()
        # _iff stops at the first complete formula
        # without this check "a b" would return only a
        remaining = self._peek()
        if remaining is not None:
            raise ParseError(
                f"unexpected {remaining.text!r} at position {remaining.position}"
            )
        return formula

    # = binds weakest, so this is the first rule
    # the while loop makes = left-associative: a = b = c gives (a = b) = c
    def _iff(self) -> Formula:
        formula = self._implies()
        while self._consume_operator("="):
            formula = Iff(formula, self._implies())
        return formula

    # the call to itself makes > right-associative: a > b > c gives a > (b > c)
    def _implies(self) -> Formula:
        formula = self._disjunction()
        if self._consume_operator(">"):
            return Implies(formula, self._implies())
        return formula

    # & binds tighter, so _conjunction runs first and takes its tokens
    # that is how a | b & c gives a | (b & c)
    def _disjunction(self) -> Formula:
        formula = self._conjunction()
        while self._consume_operator("|"):
            formula = Or(formula, self._conjunction())
        return formula

    # same shape one level down, ! binds tighter than &
    def _conjunction(self) -> Formula:
        formula = self._negation()
        while self._consume_operator("&"):
            formula = And(formula, self._negation())
        return formula

    # calls itself again, so !!a works
    def _negation(self) -> Formula:
        if self._consume_operator("!"):
            return Not(self._negation())
        return self._primary()

    # builds the leaves: atoms, constants and brackets
    # the only rule that can reject a token
    def _primary(self) -> Formula:
        token = self._peek()
        if token is None:
            raise ParseError(f"unexpected end of formula in {self._source!r}")
        if token.kind == "atom":
            self._index += 1
            return Atom(token.text)
        if token.kind == "const":
            self._index += 1
            # TOP and BOTTOM come from syntax.py, so parse("1") is TOP is True
            if token.text == "1":
                return TOP
            else:
                return BOTTOM
        if token.text == "(":
            self._index += 1
            # inside a bracket the precedence starts again, so go back to _iff
            inner = self._iff()
            # the message gives the position of the opening bracket
            if not self._consume_operator(")"):
                raise ParseError(
                    f"missing closing parenthesis for the one at position "
                    f"{token.position}"
                )
            return inner
        raise ParseError(
            f"unexpected {token.text!r} at position {token.position}"
        )

# runs both stages, the tokenizer and the parser
# a new _Parser per call, because _index would keep the old read position
def parse(text: str) -> Formula:
    return _Parser(_tokenize(text), text).parse()