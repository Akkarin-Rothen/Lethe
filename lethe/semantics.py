# For error-free use of annotations
from __future__ import annotations
# provides tool for iterations
import itertools
# helps to work with classes because it constructs default functions like __init__
from dataclasses import dataclass

# Import type alias Assignment, class Formula and fuction signature from syntax.py
from .syntax import Assignment, Formula, signature

# omega[i] belongs to sigma[i], only correct because signature() sorts
# a tuple and not a dict, so it can be a dict key, a set element and can be sorted
Interpretation = tuple[bool, ...]

# gives back a list of tuples with every possible truth value combination for a signature of that size
def create_truth_value_combinations(size: int) -> list[Interpretation]:
    if size < 0:
        raise ValueError("a signature cannot have a negative size")
    # itertools.product() returns the Cartesian product.
    # The Cartesian product gives an ordered list of all possible combinations of for each input
    # a={a,b} and b={1,2} will yield {a,1},{a,2},{b,1},{b,2}
    # First element of first set + first element of second set, then First element of first set + second element of second set and so on.
    # "repeat" repeats the same inputs the specified time.
    # itertools.product((False, True), repeat=3)) == itertools.product((False,True),(False,True),(False,True)))
    return list(itertools.product((False, True), repeat=size))


# pairs the atoms with their truth values, the form Formula.evaluate needs
def as_assignment(atoms: tuple[str, ...], truth_values: Interpretation) -> Assignment:
    # zip stops at the shorter input and says nothing
    if len(atoms) != len(truth_values):
        raise ValueError(
            f"interpretation of length {len(truth_values)} does not fit signature "
            f"of size {len(atoms)}"
        )
    # zip combines the given tuples. zip(('a','b','c'), (True, False, True)) returns [('a', True), ('b', False), ('c', True)]
    # That matches the Assignment from syntax.py
    return dict(zip(atoms, truth_values))

# holds the complete truth table of one formula over a fixed signature
@dataclass(frozen=True)
class TruthTable:
    formula: Formula
    # alphabetically sorted, so sigma[i] always belongs to position i of every row
    sigma: tuple[str, ...]
    # every truth value combination over sigma, one per table row
    rows: tuple[Interpretation, ...]
    # the truth value of the formula per row, values[i] belongs to rows[i]
    values: tuple[bool, ...]

    # builds the finished table from a formula
    # sigma can be larger than the atoms of the formula, then the table gets more rows
    # @classmethod changes what the first parameter in the function is.
    # We want it to be "cls", the class itself. Without it the first parameter in a function in a class is always "self"
    @classmethod
    def build(cls, formula: Formula, sigma: tuple[str, ...] | None = None) -> TruthTable:
        sigma = signature(formula) if sigma is None else tuple(sigma)
        missing = formula.atoms() - set(sigma)
        if missing:
            raise ValueError(
                f"signature {sigma} does not cover the atoms "
                f"{sorted(missing)} of the formula"
            )
        rows = tuple(create_truth_value_combinations(len(sigma)))
        values = []
        for truth_values in rows:
            assignment = as_assignment(sigma, truth_values)
            values.append(formula.evaluate(assignment))
        return cls(formula, sigma, rows, tuple(values))

    # defines what len() does when it is called with len(<TruthTable_obj>)
    def __len__(self) -> int:
        return len(self.rows)


    # gives back the rows where the formula is true
    def models(self) -> tuple[Interpretation, ...]:
        found = []
        # zip pairs row i with value i
        for truth_values, value in zip(self.rows, self.values):
            if value:
                found.append(truth_values)
        return tuple(found)

    # counts how many rows are true, True is 1 in Python so sum works
    def true_rows(self) -> int:
        return sum(self.values)

    # true if at least one row is true
    def is_satisfiable(self) -> bool:
        return any(self.values)

    # true if every row is true
    def is_tautology(self) -> bool:
        return all(self.values)