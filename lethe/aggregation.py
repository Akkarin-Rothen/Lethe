# aggregation.py holds the aggregate functions.
# every group of a grouped truth table holds n = 2 ** |Gamma| truth values. an aggregate turns them into one.

# For error-free use of annotations
from __future__ import annotations

# Sequence is used to annotate something with a length and an index
# Callable is used to annotate a function that is passed around as a value
from typing import Callable, Sequence

# the truth values of one group, one per row
# Sequence and not Iterable, because majority needs len()
Group = Sequence[bool]

# what every aggregate looks like from outside: one group in, one truth value out
Aggregate = Callable[[Group], bool]


# true if at least one value in the group is true
# this is the classical case, it reproduces VarForget
def maximum(group: Group) -> bool:
    return any(group)


# true if every value in the group is true
# one false value is enough to make the whole group false
def minimum(group: Group) -> bool:
    return all(group)


# true if at least half of the values are true
# >= is the tie rule, a tie counts as true
# 2 * sum keeps the comparison in whole numbers, no float is compared
def majority(group: Group) -> bool:
    return 2 * sum(group) >= len(group)


# true if at least k values of the group are true
# Th_k is the general case, Th_1 is max, Th_n is min, Th_ceil(n/2) is majority
# the only aggregate that takes a second argument, the caller has to supply k
def threshold(group: Group, k: int) -> bool:
    if k < 1:
        raise ValueError(f"the threshold k must be at least 1, got {k}")
    elif k > len(group):
        raise ValueError(
            f"threshold k={k} exceeds the group size n={len(group)}"
        )

    return sum(group) >= k
