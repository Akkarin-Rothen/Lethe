# marginalization.py forgets atoms semantically.
# it groups the rows of a truth table and turns every group into one truth value.

# For error-free use of annotations
from __future__ import annotations

# combinations builds every subsignature of a given size
import itertools
from dataclasses import dataclass
from typing import Iterable, Sequence

from .aggregation import Aggregate, maximum
from .forgetting import var_forget
from .syntax import Formula, signature
from .truth_tables import Interpretation, TruthTable


# one group of rows, named by the truth values of the kept atoms
@dataclass(frozen=True)
class MarginalGroup:
    # which group this is
    # example: (False,) is the group a = 0
    key: Interpretation
    # the rows in this group, in table order
    # example: ((F,F,F), (F,F,T), (F,T,F), (F,T,T))
    rows: tuple[Interpretation, ...]
    # what the formula gives in these rows
    # example: (F, F, F, T)
    values: tuple[bool, ...]

    # how many rows are in the group
    # example: (F, F, F, T) gives 4
    def size(self) -> int:
        return len(self.values)

    # how many of them are true, c_1 in the thesis
    # example: (F, F, F, T) gives 1
    def true_count(self) -> int:
        return sum(self.values)


# everything one forgetting run produced
# it holds both sides, the semantic one and the syntactic one
@dataclass(frozen=True)
class ForgetResult:
    # the formula
    # example: (a | b) & c
    formula: Formula
    # the atoms of the formula
    # example: ('a', 'b', 'c')
    atom_names: tuple[str, ...]
    # the atoms that were forgotten
    # example: ('b', 'c')
    forgotten: tuple[str, ...]
    # the atoms that are left
    # example: ('a',)
    kept: tuple[str, ...]
    # the truth table of the formula
    # example: 8 rows, values (F,F,F,T,F,T,F,T)
    table: TruthTable
    # the rows, grouped and sorted
    # example: two groups, a = 0 and a = 1
    groups: tuple[MarginalGroup, ...]
    # the aggregates this run used
    # example: (maximum, minimum, majority)
    aggregates: tuple[Aggregate, ...]
    # per aggregate one truth value per group
    # example: {'maximum': (T, T), 'minimum': (F, F), 'majority': (F, T)}
    aggregated: dict[str, tuple[bool, ...]]
    # the result of the syntactic side, VarForget(A, Gamma)
    # example: forgetting b and c from (a | b) & c gives the constant 1
    var_forget_formula: Formula
    # its truth values over the kept atoms
    # example: (T, T), the constant 1 over kept = ('a',) has two rows
    var_forget_values: tuple[bool, ...]

    # how many rows every group has, n = 2 ** |Gamma|
    # example: forgetting ('b', 'c') gives 4
    def group_size(self) -> int:
        return 2 ** len(self.forgotten)

    # the values of one aggregate, one per group
    # the name is the function name, for example maximum
    # example: values_of('majority') gives (F, T)
    def values_of(self, name: str) -> tuple[bool, ...]:
        return self.aggregated[name]

    # true if this aggregate gives the same as the syntactic side
    # example: 'maximum' gives True, 'minimum' gives False
    def agrees_with_var_forget(self, name: str) -> bool:
        return self.values_of(name) == self.var_forget_values

    # the test oracle, the maximum has to give the same as VarForget
    # example: True for the whole catalog
    def oracle_holds(self) -> bool:
        return self.agrees_with_var_forget("maximum")



def model_marginalization(
    models: Iterable[Interpretation],
    atom_names: Sequence[str],
    kept: Sequence[str],
) -> set[Interpretation]:
    positions = _positions_of(kept, atom_names)

    projected = set()
    for row in models:
        projected.add(_key_of(row, positions))
    return projected



# forgets atoms both ways and puts both results in one ForgetResult
# semantic: group the rows, aggregate every group
# syntactic: call var_forget
#
# example: forget((a | b) & c, ['b', 'c'], (maximum, minimum, majority))
#   atom_names  ('a', 'b', 'c')
#   forgotten   ('b', 'c')
#   kept        ('a',)
#   groups      a = 0 with values (F, F, F, T)
#               a = 1 with values (F, T, F, T)
#   aggregated  maximum (T, T), majority (F, T), minimum (F, F)
#   var_forget  the constant 1, values (T, T) over kept
#   the maximum matches, the other two do not
def forget(
    formula: Formula,
    forgotten: Iterable[str],
    aggregates: Sequence[Aggregate] = (maximum,),
    atom_names: tuple[str, ...] | None = None,
) -> ForgetResult:
    if atom_names is None:
        atom_names = signature(formula)
    else:
        atom_names = tuple(atom_names)

    # set drops duplicates, sorted keeps the order stable
    # example: ['c', 'b', 'c'] gives ('b', 'c')
    forgotten = tuple(sorted(set(forgotten)))

    if not forgotten:
        raise ValueError("the set of atoms to forget must not be empty")

    unknown = []
    for atom in forgotten:
        if atom not in atom_names:
            unknown.append(atom)
    if unknown:
        raise ValueError(
            f"cannot forget {unknown}, the formula only has {atom_names}"
        )

    # walks atom_names, so kept stays alphabetical
    # example: atom_names ('a','b','c') minus forgotten ('b','c') gives ('a',)
    kept = []
    for atom in atom_names:
        if atom not in forgotten:
            kept.append(atom)
    kept = tuple(kept)

    if not kept:
        raise ValueError(
            "forgetting every atom leaves nothing to group by"
        )

    table = TruthTable.build(formula, atom_names)
    groups = _group_rows(table, kept)

    # one entry per aggregate, the key is the function name
    # example: {'maximum': (T, T), 'majority': (F, T), 'minimum': (F, F)}
    aggregates = tuple(aggregates)
    aggregated = {}
    for aggregate in aggregates:
        values = []
        for group in groups:
            values.append(aggregate(group.values))
        aggregated[aggregate.__name__] = tuple(values)


    # build the reference table over kept, not over its own atoms
    # the constant 1 has one row on its own, but two over kept = ('a',)
    # example: var_forget((a | b) & c, ('b','c')) is 1, its values are (T, T)
    forgotten_formula = var_forget(formula, forgotten)
    reference = TruthTable.build(forgotten_formula, kept)

    return ForgetResult(
        formula=formula,
        atom_names=atom_names,
        forgotten=forgotten,
        kept=kept,
        table=table,
        groups=groups,
        aggregates=aggregates,
        aggregated=aggregated,
        var_forget_formula=forgotten_formula,
        var_forget_values=reference.values,
    )



# where the kept atoms sit in a row
# example: atom_names ('a','b','c') and kept ('a','c') gives [0, 2]
def _positions_of(kept: Sequence[str], atom_names: Sequence[str]) -> list[int]:
    positions = []
    for atom in kept:
        positions.append(atom_names.index(atom))
    return positions


# picks those places out of one row
# example: row (T,F,T) at positions [0, 2] gives (T, T)
def _key_of(row: Interpretation, positions: Sequence[int]) -> Interpretation:
    key = []
    for position in positions:
        key.append(row[position])
    return tuple(key)


# sorts the rows into groups, one group per assignment of the kept atoms
# example: (a | b) & c with kept ('a',) gives the groups a = 0 and a = 1
def _group_rows(table: TruthTable, kept: tuple[str, ...]) -> tuple[MarginalGroup, ...]:
    positions = _positions_of(kept, table.atom_names)

    # one bucket per group
    buckets = {}
    for row, value in zip(table.rows, table.values):
        key = _key_of(row, positions)
        buckets.setdefault(key, []).append((row, value))

    # sorted, so group i belongs to row i of the reference table
    # without sorted the oracle fails sometimes, not always
    groups = []
    for key in sorted(buckets):
        rows = []
        values = []
        for row, value in buckets[key]:
            rows.append(row)
            values.append(value)
        groups.append(MarginalGroup(key, tuple(rows), tuple(values)))
    return tuple(groups)


# every set of atoms that can be forgotten
# proper=True leaves out the full signature, there would be nothing left to group by
# example: ('a','b','c') gives 6, three of size 1 and three of size 2
def subsignatures(
    atom_names: Sequence[str], *, proper: bool = True
) -> list[tuple[str, ...]]:
    largest = len(atom_names)
    if proper:
        largest = largest - 1

    result = []
    for size in range(1, largest + 1):
        result.extend(itertools.combinations(atom_names, size))
    return result