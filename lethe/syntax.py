# For error free use of annotations
from __future__ import annotations
# helps to work with classes cause it constructs default functions like __init__ 
from dataclasses import dataclass
# Mapping is used for key,value data structures
# ClassVar is used for class variables that belong to the class and not to every single object
from typing import ClassVar, Mapping

# is used to store truth values for atoms
Assignment = Mapping[str, bool]

# Binding strength, used to place the minimal number of parentheses.
# Private variables
_PREC_ATOM = 5
_PREC_NOT = 4
_PREC_AND = 3
_PREC_OR = 2
_PREC_IMPLIES = 1
_PREC_IFF = 0



# Base class for other classes to inherit from
class Formula: 
    # prevent every inhereting class to get a dict
    __slots__ = ()

    #: binding strength of the outermost connective
    precedence: int = _PREC_ATOM

    # raise NotImplementedError to force every inhereting class to do an implementation
    def evaluate(self, assignment: Assignment) -> bool:
        raise NotImplementedError

    # frozenset[str] is an unchanged set of values
    def atoms(self) -> frozenset[str]:
        raise NotImplementedError

    def substitute(self, atom: str, value: bool) -> Formula:
        raise NotImplementedError

    def to_latex(self) -> str:
        raise NotImplementedError

    # used for parenthese rendering
    # it decides if a child formula need parentheses or not
    # A ∧ (B ∨ C) has the child B ∨ C
    def _wrap(self, child: Formula, strict: bool, latex: bool) -> str:
        text = child.to_latex() if latex else str(child)
        # sets needs=true if the precedence of the child is smaller then the own or id both are the same andt strict=true
        # strict is used to prevent (a>b)>c to be printet as  a > b > c
        # < is used because the = case is handled on the or case
        # strict is set on a rendering call
        needs = child.precedence < self.precedence or (strict and child.precedence == self.precedence )
        return f"({text})" if needs else text



# apply dataclass to Atom and make it unchangeable
@dataclass(frozen=True)
class Atom(Formula):
    name: str
    precedence = _PREC_ATOM

    def evaluate(self, assignment: Assignment) -> bool:
        try:
            return assignment[self.name]
        except KeyError:
            raise KeyError(
                f"atom {self.name!r} has no truth value in the assignment"
            ) from None

    def atoms(self) -> frozenset[str]:
        return frozenset({self.name})

    # substitute atom string with top or bottom
    def substitute(self, atom: str, value: bool) -> Formula:
        if self.name != atom:
            return self
        return TOP if value else BOTTOM

    # return latex compatible string   
    def to_latex(self) -> str:
        return self.name

    # return a string for the computation
    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Constant(Formula):
    value: bool
    precedence = _PREC_ATOM

    def evaluate(self, assignment: Assignment) -> bool:
        return self.value

    def atoms(self) -> frozenset[str]:
        return frozenset()

    def substitute(self, atom: str, value: bool) -> Formula:
        return self

    def to_latex(self) -> str:
        return r"\top" if self.value else r"\bot"

    def __str__(self) -> str:
        return "1" if self.value else "0"


TOP = Constant(True)
BOTTOM = Constant(False)

# goal is to replace a not with either \lnot for latex or ! for the calculation
@dataclass(frozen=True)
class Not(Formula):
    # holds the part of the formaula that Not negates
    sub: Formula
    precedence = _PREC_NOT

    def evaluate(self, assignment: Assignment) -> bool:
        return not self.sub.evaluate(assignment)

    def atoms(self) -> frozenset[str]:
        return self.sub.atoms()

    def substitute(self, atom: str, value: bool) -> Formula:
        return Not(self.sub.substitute(atom, value))

    def to_latex(self) -> str:
        return r"\lnot " + self._wrap(self.sub, strict=False, latex=True)

    def __str__(self) -> str:
        return "!" + self._wrap(self.sub, strict=False, latex=False)

    