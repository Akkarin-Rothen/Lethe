# parser.py reads a text like "(a|b)&c" and builds the tree.
# it works in two stages: a tokenizer cuts the text into pieces, a recursive descent parser turns those pieces into nodes.
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
# example: "(a|1)&c" is cut into ( a | 1 ) & c, seven tokens
_TOKEN_PATTERN = re.compile(
    r"(?P<space>\s+)|(?P<atom>[A-Za-z][0-9]*)|(?P<const>[01])|(?P<op>[!&|>=()])|(?P<unicode>[¬∧∨→↔⊤⊥])"
)

# Accept the mathematical symbols as well, so formulas can be copied out of the thesis without rewriting them.
# Mapping them for calculations
# The editor flags the unicode keys as ambiguous characters. That warning is irrelevant here.
# example: "(a∨b)∧c" is read like "(a|b)&c"
_UNICODE_ALIASES = {
    "¬": "!",  # not
    "∧": "&",  # and
    "∨": "|",  # or
    "→": ">",  # implies
    "↔": "=",  # iff
    "⊤": "1",  # top
    "⊥": "0",  # bottom
}


# raised when an input string is not a well formed formula
# the class body is empty, pass is the placeholder Python needs
class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class _Token:
    kind: str  # "atom", "const" or "op"
    text: str
    position: int


# example: "a&b" gives the tokens atom a, op &, atom b
# example: "a $ b" raises ParseError, $ is no token
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
    # example: at the start of "a&b" it gives the atom a and does not move on
    def _peek(self) -> _Token | None:
        if self._index < len(self._tokens):
            return self._tokens[self._index]
        return None

    # moves one step forward only if the next token is that operator
    # returns False and changes nothing otherwise
    # example: on "&b" with symbol "&" it gives True and moves one step
    # example: on "&b" with symbol "|" it gives False and stays put
    def _consume_operator(self, symbol: str) -> bool:
        token = self._peek()
        if token is not None and token.kind == "op" and token.text == symbol:
            self._index += 1
            return True
        return False

    # rejects an empty list, builds the tree, then rejects leftover tokens
    # example: "(a|b)&c" gives And(Or(Atom(a), Atom(b)), Atom(c))
    # example: "a b" raises ParseError, b is left over
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
    # example: a = b = c gives (a = b) = c
    def _iff(self) -> Formula:
        formula = self._implies()
        while self._consume_operator("="):
            formula = Iff(formula, self._implies())
        return formula

    # the call to itself makes > right-associative: a > b > c gives a > (b > c)
    # example: a > b > c gives a > (b > c)
    def _implies(self) -> Formula:
        formula = self._disjunction()
        if self._consume_operator(">"):
            return Implies(formula, self._implies())
        return formula

    # & binds tighter, so _conjunction runs first and takes its tokens
    # that is how a | b & c gives a | (b & c)
    # example: a | b | c gives (a | b) | c
    def _disjunction(self) -> Formula:
        formula = self._conjunction()
        while self._consume_operator("|"):
            formula = Or(formula, self._conjunction())
        return formula

    # same shape one level down, ! binds tighter than &
    # example: a & b & c gives (a & b) & c
    def _conjunction(self) -> Formula:
        formula = self._negation()
        while self._consume_operator("&"):
            formula = And(formula, self._negation())
        return formula

    # calls itself again, so !!a works
    # example: !!a gives Not(Not(Atom(a)))
    def _negation(self) -> Formula:
        if self._consume_operator("!"):
            return Not(self._negation())
        return self._primary()

    # builds the leaves: atoms, constants and brackets
    # the only rule that can reject a token
    # example: "a" gives Atom(a), "1" gives TOP, "(a|b)" gives the Or inside
    # example: "(a" raises ParseError and names the position of the open bracket
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
        raise ParseError(f"unexpected {token.text!r} at position {token.position}")


# runs both stages, the tokenizer and the parser
# a new _Parser per call, because _index would keep the old read position
# example: parse("(a|b)&c") gives the tree, and str() of it gives "(a | b) & c"
# example: parse("1") is TOP, the same object every time
def parse(text: str) -> Formula:
    return _Parser(_tokenize(text), text).parse()
