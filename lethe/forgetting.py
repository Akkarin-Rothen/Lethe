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


# simplifies one And node
# both children are already simple when this function runs
# the rules are:
#   1 & X gives X
#   0 & X gives 0
#   X & X gives X
#   X & !X gives 0
# no rule fits, then the function builds a new And
def _simplify_and(left: Formula, right: Formula) -> Formula:
    if isinstance(left, Constant):
        return right if left.value else BOTTOM
    if isinstance(right, Constant):
        return left if right.value else BOTTOM
    if left == right:  # idempotence
        return left
    if _complementary(left, right):
        return BOTTOM
    return And(left, right)


# simplifies one Or node
# both children are already simple when this function runs
# the rules are:
#   1 | X gives 1
#   0 | X gives X
#   X | X gives X
#   X | !X gives 1
#   X | (X & Y) gives X
# no rule fits, then the function builds a new Or
def _simplify_or(left: Formula, right: Formula) -> Formula:
    if isinstance(left, Constant):
        return TOP if left.value else right
    if isinstance(right, Constant):
        return TOP if right.value else left
    if left == right:  # idempotence
        return left
    if _complementary(left, right):
        return TOP
    if _absorbs(left, right):
        return left
    if _absorbs(right, left):
        return right
    return Or(left, right)

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

