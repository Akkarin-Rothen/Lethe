# syntax.py defines what a formula is: an immutable tree of atoms, the two constants and five connectives.
# Every node can do four things: give its truth value for an assignment, name its atoms, replace an atom by TOP or BOTTOM, and print itself as text or as LaTeX.

# For error-free use of annotations
from __future__ import annotations
# helps to work with classes because it constructs default functions like __init__
from dataclasses import dataclass
# Mapping is used for key, value data structures
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
    # binding strength of the outermost connective
    precedence: int = _PREC_ATOM

    # raise NotImplementedError to force every inheriting class to do an implementation
    def evaluate(self, assignment: Assignment) -> bool:
        raise NotImplementedError

    # frozenset[str] is an unchangeable set of values
    def atoms(self) -> frozenset[str]:
        raise NotImplementedError

    # replaces one atom everywhere by TOP or BOTTOM and gives a new tree
    def substitute(self, atom: str, value: bool) -> Formula:
        raise NotImplementedError

    # every object already has __str__, so only to_latex is declared here
    def to_latex(self) -> str:
        raise NotImplementedError

    # decides if a child formula needs parentheses
    # A ∧ (B ∨ C) has the child B ∨ C
    def _wrap(self, child: Formula, *, strict: bool, latex: bool) -> str:
        text = child.to_latex() if latex else str(child)
        # sets needs=True if the child binds more weakly than self,
        # or if both bind equally and strict=True
        # strict is used to prevent (a>b)>c from being printed as a > b > c
        # < is used because the = case is handled on the or case
        # strict is set on a rendering call
        needs = child.precedence < self.precedence or (strict and child.precedence == self.precedence )
        return f"({text})" if needs else text



# apply dataclass to Atom and make it unchangeable
@dataclass(frozen=True)
class Atom(Formula):
    name: str
    precedence = _PREC_ATOM

    # reads the own name from the assignment
    # "from None" hides the first error, so only the clear message is shown
    def evaluate(self, assignment: Assignment) -> bool:
        try:
            return assignment[self.name]
        except KeyError:
            raise KeyError(
                f"atom {self.name!r} has no truth value in the assignment"
            ) from None

    # an atom is a leaf, so the recursion stops here
    def atoms(self) -> frozenset[str]:
        return frozenset({self.name})

    # substitute atom string with top or bottom
    # another name gives self back, because the tree cannot change
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


# the two constants of Boole, TOP and BOTTOM
# a constant binds like an atom, so it never gets parentheses
@dataclass(frozen=True)
class Constant(Formula):
    value: bool
    precedence = _PREC_ATOM

    # the assignment has no effect here
    def evaluate(self, assignment: Assignment) -> bool:
        return self.value

    # a constant holds no atom
    def atoms(self) -> frozenset[str]:
        return frozenset()

    # nothing to replace
    def substitute(self, atom: str, value: bool) -> Formula:
        return self

    def to_latex(self) -> str:
        return r"\top" if self.value else r"\bot"

    def __str__(self) -> str:
        return "1" if self.value else "0"


# the only two constant objects of the program
# "is TOP" works only if all constants come from here
# so never write Constant(True) at another place
TOP = Constant(True)
BOTTOM = Constant(False)

# goal is to replace a not with either \lnot for latex or ! for the calculation
@dataclass(frozen=True)
class Not(Formula):
    # holds the part of the whole formula that Not() negates
    sub: Formula
    precedence = _PREC_NOT

    # invert the value of the child
    def evaluate(self, assignment: Assignment) -> bool:
        return not self.sub.evaluate(assignment)

    # Not adds no atom
    def atoms(self) -> frozenset[str]:
        return self.sub.atoms()

    # builds a new Not, the old tree stays as it is
    def substitute(self, atom: str, value: bool) -> Formula:
        return Not(self.sub.substitute(atom, value))

    # the space after \lnot is needed, else LaTeX reads the command \lnota
    def to_latex(self) -> str:
        return r"\lnot " + self._wrap(self.sub, strict=False, latex=True)

    # strict=False keeps !!a free of parentheses, !(a | b) still gets them
    def __str__(self) -> str:
        return "!" + self._wrap(self.sub, strict=False, latex=False)


# shared base of the four two-place connectives
# a subclass sets only the symbols, the precedence and evaluate
@dataclass(frozen=True)
class BinaryConnective(Formula):
    # a child can be any node type, so the tree can nest
    left: Formula
    right: Formula

    # program syntax symbol, filled in by subclasses
    symbol: ClassVar[str] = ""
    # latex syntax symbol, filled in by subclasses
    latex_symbol: ClassVar[str] = ""
    # True only for Implies, the one right-associative connective
    right_associative: ClassVar[bool] = False

    # here | is the set union of Python, not the disjunction of the logic
    def atoms(self) -> frozenset[str]:
        return self.left.atoms() | self.right.atoms()

    # type(self) gives the concrete class, so And builds an And, Iff an Iff
    def substitute(self, atom: str, value: bool) -> Formula:
        return type(self)(
            self.left.substitute(atom, value), self.right.substitute(atom, value)
        )

    # one method for both outputs, only the symbols differ
    # left-associative (& | =): left free, right in parentheses -> a | b | c
    # right-associative (>):    the other way round             -> a > b > c
    def _render(self, *, latex: bool) -> str:
        symbol = self.latex_symbol if latex else self.symbol
        left = self._wrap(self.left, strict=self.right_associative, latex=latex)
        right = self._wrap(
            self.right, strict=not self.right_associative, latex=latex
        )
        return f"{left} {symbol} {right}"

    def to_latex(self) -> str:
        return self._render(latex=True)

    def __str__(self) -> str:
        return self._render(latex=False)


@dataclass(frozen=True)
class And(BinaryConnective):
    symbol: ClassVar[str] = "&"
    latex_symbol: ClassVar[str] = r"\land"
    precedence = _PREC_AND

    def evaluate(self, assignment: Assignment) -> bool:
        return self.left.evaluate(assignment) and self.right.evaluate(assignment)


@dataclass(frozen=True)
class Or(BinaryConnective):
    symbol: ClassVar[str] = "|"
    latex_symbol: ClassVar[str] = r"\lor"
    precedence = _PREC_OR

    def evaluate(self, assignment: Assignment) -> bool:
        return self.left.evaluate(assignment) or self.right.evaluate(assignment)

@dataclass(frozen=True)
class Implies(BinaryConnective):
    symbol: ClassVar[str] = ">"
    latex_symbol: ClassVar[str] = r"\rightarrow"
    # the only right-associative connective, so a > b > c means a > (b > c)
    right_associative: ClassVar[bool] = True
    precedence = _PREC_IMPLIES

    # material implication, written as !a | b
    # false in one case only: left true and right false
    def evaluate(self, assignment: Assignment) -> bool:
        return (not self.left.evaluate(assignment)) or self.right.evaluate(
            assignment
        )


@dataclass(frozen=True)
class Iff(BinaryConnective):
    symbol: ClassVar[str] = "="
    latex_symbol: ClassVar[str] = r"\leftrightarrow"
    # binds most weakly, so a & b = c means (a & b) = c
    precedence = _PREC_IFF

    # two truth values are equivalent if they are equal
    def evaluate(self, assignment: Assignment) -> bool:
        return self.left.evaluate(assignment) == self.right.evaluate(assignment)


# a function and not a method, because it works on the whole tree
# sorted and a tuple, so position i always belongs to the same atom
# the truth tables and the group keys later depend on this order
def signature(formula: Formula) -> tuple[str, ...]:
    return tuple(sorted(formula.atoms()))
