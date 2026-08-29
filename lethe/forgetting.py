# forgetting.py performs syntactical forgetting VarForget. Only manipulates the formula. Does not create a truth table.


from __future__ import annotations

from typing import Iterable

from .syntax import (
    And,
    BOTTOM,
    Constant,
    Formula,
    Iff,
    Implies,
    Not,
    Or,
    TOP,
)

# substitutes the atom for the truth value TOP or BOTTOM
def substitute(formula: Formula, atom: str, value: bool) -> Formula:
    return formula.substitute(atom, value)


# true if the two formulas are X and !X, in either order
# the goal is to fold them away: a | !a becomes 1, a & !a becomes 0
# left is !a, left.sub is a and right is a, then true
# the same the other way round: right is !a, right.sub is a and left is a
def _complementary(left: Formula, right: Formula) -> bool:
    if (isinstance(left, Not) and left.sub == right) or (isinstance(right, Not) and right.sub == left):
        return True
    return False

# true if inner is a conjunction and outer is one of its parts
# the goal is to drop the longer side: a | (a & b) becomes a
def _absorbs(outer: Formula, inner: Formula) -> bool:
    if not isinstance(inner, And):
        return False
    return outer in _conjuncts(inner)


def _conjuncts(formula: Formula) -> list[Formula]:
    # checking if formula is of type AND
    if isinstance(formula, And):
        # recursion because: And holds two children, and each child can be another And, at any depth
        return _conjuncts(formula.left) + _conjuncts(formula.right)
    return [formula]

