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
class Fromula: 
    # prevent every inhereting class to get a dict
    __slots__ = ()

    #: binding strength of the outermost connective
    precedence: int = _PREC_ATOM

    # raise NotImplementedError to force every inherting class to do an implementation
    def evaluate(self, assignment: Assignment) -> bool:
        raise NotImplementedError

    def atoms(self) -> frozenset[str]:
        raise NotImplementedError

    def substitute(self, atom: str, value: bool) -> Formula:
        raise NotImplementedError

    def to_latex(self) -> str:
        raise NotImplementedError

    def _wrap(self, child: Formula, *, strict: bool, latex: bool) -> str:
        text = child.to_latex() if latex else str(child)
        needs = child.precedence < self.precedence or (
            strict and child.precedence == self.precedence
        )
        return f"({text})" if needs else text




