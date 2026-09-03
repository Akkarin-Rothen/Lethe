# aggregation.py holds the aggregate functions.
# every group of a grouped truth table holds n = 2 ** |Gamma| truth values. an aggregate turns them into one.

# For error-free use of annotations
from __future__ import annotations

# Sequence is used to annotate something with a length and an index
# Callable is used to annotate a function that is passed around as a value
from typing import Callable, Sequence

# the truth values of one group, one per row
# Sequence and not Iterable, because majority needs len()
# example: (F, F, F, T) is a group of four rows with one true row
Group = Sequence[bool]

# what every aggregate looks like from outside: one group in, one truth value out
# example: maximum, minimum and majority all match this shape
Aggregate = Callable[[Group], bool]


# true if at least one value in the group is true
# this is the classical case, it reproduces VarForget
# example: (F, F, F, T) gives True, (F, F, F, F) gives False
def maximum(group: Group) -> bool:
    return any(group)


# true if every value in the group is true
# one false value is enough to make the whole group false
# example: (T, T, T) gives True, (F, F, F, T) gives False
def minimum(group: Group) -> bool:
    return all(group)


# true if at least half of the values are true
# >= is the tie rule, a tie counts as true
# 2 * sum keeps the comparison in whole numbers, no float is compared
# example: (T, F) gives True, that is the tie
# example: (F, F, F, T) gives False, one true row out of four
def majority(group: Group) -> bool:
    return 2 * sum(group) >= len(group)


# true if at least k values of the group are true
# Th_k is the general case, Th_1 is max, Th_n is min, Th_ceil(n/2) is majority
# the only aggregate that takes a second argument, the caller has to supply k
# example: (T, T, F) with k=2 gives True, with k=3 gives False
# example: k=0 and k>n both raise ValueError
def threshold(group: Group, k: int) -> bool:
    if k < 1:
        raise ValueError(f"the threshold k must be at least 1, got {k}")
    elif k > len(group):
        raise ValueError(f"threshold k={k} exceeds the group size n={len(group)}")

    return sum(group) >= k


# the short names used as column titles in the output
# a name that is not in here is printed as it is, for example th2
# example: "maximum" is printed as max
COLUMN_TITLES = {
    "maximum": "max",
    "minimum": "min",
    "majority": "maj",
}


# the column title of one aggregate name
# example: "maximum" gives "max", "th2" gives "th2"
def column_title(name: str) -> str:
    return COLUMN_TITLES.get(name, name)
