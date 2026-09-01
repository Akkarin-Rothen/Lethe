# forgetting.py performs syntactical forgetting VarForget.
# the module only manipulates the formula. it does not create a truth table.


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
# example: substitute((a | b) & c, 'c', True) gives (a | b) & 1
def substitute(formula: Formula, atom: str, value: bool) -> Formula:
    return formula.substitute(atom, value)


# forgets every atom of atoms from the formula
# VarForget(A, a) is A[a/1] | A[a/0], applied once per atom
# set removes duplicates, sorted makes the printed result reproducible
# simplify runs inside the loop, else the formula doubles with every atom
# example: var_forget((a | b) & c, ['c']) gives a | b
# example: var_forget((a | b) & c, ['b', 'c']) gives 1
# example: var_forget((a | b) & c, ['z']) gives the formula back, z does not occur
def var_forget(formula: Formula, atoms_to_forget: Iterable[str]) -> Formula:
    result = formula
    for atom in sorted(set(atoms_to_forget)):
        if atom not in result.atoms():
            # nothing to forget, the formula does not mention this atom
            continue
        result = simplify(
            Or(substitute(result, atom, True), substitute(result, atom, False))
        )
    return result

# simplifies a whole formula tree
# the function calls itself on the children first, then folds the node
# the rules for Not are:
#   !1 gives 0
#   !0 gives 1
#   !!X gives X
# And, Or, Implies and Iff go to _simplify_binary
# an Atom and a Constant are leaves, the function returns them unchanged
# example: ((a & 1) | 0) > ((b | 0) & 1) gives a > b
def simplify(formula: Formula) -> Formula:
    if isinstance(formula, Not):
        inner = simplify(formula.negated)
        if isinstance(inner, Constant):
            if inner.value:
                return BOTTOM
            else:
                return TOP
        if isinstance(inner, Not):
            return inner.negated
        return Not(inner)

    if isinstance(formula, (And, Or, Implies, Iff)):
        left = simplify(formula.left)
        right = simplify(formula.right)
        return _simplify_binary(type(formula), left, right)

    return formula


# folds one two-place node, the caller has already simplified both children
# node_type is the class of the node, so one function serves all four connectives
# And and Or have their own function, Implies and Iff are folded here
# the rules for Implies are:
#   1 > X gives X
#   0 > X gives 1
#   X > 1 gives 1
#   X > 0 gives !X
#   X > X gives 1
# the rules for Iff are:
#   1 = X gives X
#   0 = X gives !X
#   X = 1 gives X
#   X = 0 gives !X
#   X = X gives 1
# an unknown class raises TypeError
# example: node_type Or with left 1 gives 1, with left 0 gives the right side
def _simplify_binary(node_type: type[Formula], left: Formula, right: Formula) -> Formula:
    if node_type is And:
        return _simplify_and(left, right)
    if node_type is Or:
        return _simplify_or(left, right)
    if node_type is Implies:
        # A > B means the same as !A | B
        # the code keeps the Implies, so the printed formula stays close to the input
        if isinstance(left, Constant):
            if left.value:
                return right
            else:
                return TOP
        if isinstance(right, Constant):
            if right.value:
                return TOP
            else:
                return simplify(Not(left))
        if left == right:
            return TOP
        return Implies(left, right)
    if node_type is Iff:
        if isinstance(left, Constant):
            if left.value:
                return right
            else:
                return simplify(Not(right))
        if isinstance(right, Constant):
            if right.value:
                return left
            else:
                return simplify(Not(left))
        if left == right:
            return TOP
        return Iff(left, right)
    raise TypeError(f"cannot simplify {node_type!r}")

# simplifies one And node
# both children are already simple when this function runs
# the rules are:
#   1 & X gives X
#   0 & X gives 0
#   X & X gives X
#   X & !X gives 0
# no rule fits, then the function builds a new And
# example: 1 & a gives a, a & !a gives 0, a & b stays a & b
def _simplify_and(left: Formula, right: Formula) -> Formula:
    if isinstance(left, Constant):
        if left.value:
            return right
        else:
            return BOTTOM
    if isinstance(right, Constant):
        if right.value:
            return left
        else:
            return BOTTOM
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
# example: 1 | a gives 1, a | !a gives 1, a | (a & b) gives a
def _simplify_or(left: Formula, right: Formula) -> Formula:
    if isinstance(left, Constant):
        if left.value:
            return TOP
        else:
            return right
    if isinstance(right, Constant):
        if right.value:
            return TOP
        else:
            return left
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
# left is !a, left.negated is a and right is a, then true
# the same the other way round: right is !a, right.negated is a and left is a
def _complementary(left: Formula, right: Formula) -> bool:
    if (isinstance(left, Not) and left.negated == right) or (isinstance(right, Not) and right.negated == left):
        return True
    return False

# true if inner is a conjunction and outer is one of its parts
# the goal is to drop the longer side: a | (a & b) becomes a
def _absorbs(outer: Formula, inner: Formula) -> bool:
    if not isinstance(inner, And):
        return False
    return outer in _conjuncts(inner)


# example: a & b & c gives [a, b, c]
# example: a & (b | c) gives [a, b | c], the Or stays whole
# example: a | b gives [a | b], not an And, so one element
def _conjuncts(formula: Formula) -> list[Formula]:
    # checking if formula is of type AND
    if isinstance(formula, And):
        # recursion because: And holds two children, and each child can be another And, at any depth
        return _conjuncts(formula.left) + _conjuncts(formula.right)
    return [formula]

