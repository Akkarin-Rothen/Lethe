# truth_tables.py builds the complete truth table of a formula over a fixed signature.

# For error-free use of annotations
from __future__ import annotations
# provides tool for iterations
import itertools
# helps to work with classes because it constructs default functions like __init__
from dataclasses import dataclass

# Import type alias Assignment, class Formula and function signature from syntax.py
from .syntax import Assignment, Formula, signature

# position i belongs to atom_names[i], only correct because signature() sorts
# a tuple and not a list, only a tuple can be a dict key or a set element
Interpretation = tuple[bool, ...]

# gives back a list of tuples with every possible truth value combination for that many atoms
# needed by TruthTable.build, it produces the rows of the table
def create_truth_value_combinations(size: int) -> list[Interpretation]:
    if size < 0:
        raise ValueError("the number of atoms cannot be negative")
    # itertools.product() returns the Cartesian product.
    # The Cartesian product gives an ordered list of all possible combinations of for each input
    # a={a,b} and b={1,2} will yield {a,1},{a,2},{b,1},{b,2}
    # First element of first set + first element of second set, then First element of first set + second element of second set and so on.
    # "repeat" repeats the same inputs the specified time.
    # itertools.product((False, True), repeat=3)) == itertools.product((False,True),(False,True),(False,True)))
    return list(itertools.product((False, True), repeat=size))


# pairs the atoms with their truth values, the form Formula.evaluate needs
# needed by TruthTable.build and later by marginalization.py
def as_assignment(atoms: tuple[str, ...], truth_values: Interpretation) -> Assignment:
    # zip stops at the shorter input and says nothing
    if len(atoms) != len(truth_values):
        raise ValueError(
            f"{len(truth_values)} truth values do not fit {len(atoms)} atoms"
        )
    # zip combines the given tuples. zip(('a','b','c'), (True, False, True)) returns [('a', True), ('b', False), ('c', True)]
    # That matches the Assignment from syntax.py
    return dict(zip(atoms, truth_values))

# holds the complete truth table of one formula over a fixed signature
# everything later builds on it: the formula catalog, the forgetting and both renderers
@dataclass(frozen=True)
class TruthTable:
    formula: Formula
    # alphabetically sorted, so atom_names[i] always belongs to position i of every row
    atom_names: tuple[str, ...]
    # every truth value combination over atom_names, one per table row
    rows: tuple[Interpretation, ...]
    # the truth value of the formula per row, values[i] belongs to rows[i]
    values: tuple[bool, ...]

    # builds the finished table from a formula
    # atom_names can be larger than the atoms of the formula, then the table gets more rows
    # @classmethod changes what the first parameter in the function is.
    # We want it to be "cls", the class itself. Without it the first parameter in a function in a class is always "self"
    @classmethod
    def build(cls, formula: Formula, atom_names: tuple[str, ...] | None = None) -> TruthTable:
        if atom_names is None:
            atom_names = signature(formula)
        else:
            atom_names = tuple(atom_names)
        missing = formula.atoms() - set(atom_names)
        if missing:
            raise ValueError(
                f"the atoms {atom_names} do not cover "
                f"{sorted(missing)} of the formula"
            )
        rows = tuple(create_truth_value_combinations(len(atom_names)))
        values = []
        for truth_values in rows:
            assignment = as_assignment(atom_names, truth_values)
            values.append(formula.evaluate(assignment))
        return cls(formula, atom_names, rows, tuple(values))

    # defines what len() does when it is called with len(<TruthTable_obj>)
    def __len__(self) -> int:
        return len(self.rows)

    # counts how many rows are true, True is 1 in Python so sum works
    def true_rows(self) -> int:
        return sum(self.values)


# true if both formulas have the same models
# needed to show that a forgotten formula still means the same
def equivalent(left: Formula, right: Formula) -> bool:
    # both tables need the same signature, else the rows do not line up
    shared_atom_names = tuple(sorted(left.atoms() | right.atoms()))
    left_table = TruthTable.build(left, shared_atom_names)
    right_table = TruthTable.build(right, shared_atom_names)
    return left_table.values == right_table.values
