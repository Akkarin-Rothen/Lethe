from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

# the truth values of one group, one per row
# Sequence and not Iterable, because majority needs len()
Group = Sequence[bool]


@dataclass(frozen=True)
class Aggregator:
    name: str
    label: str
    function: Callable[[Group], bool]

    def __call__(self, group: Group) -> bool:
        if not group:
            raise ValueError("cannot aggregate an empty group")
        return self.function(group)


# true if at least one value in the group is true
# this is the classical case, it reproduces VarForget
def maximum(group: Group) -> bool:
    return any(group)

# true if every value in the group is true
# one false value is enough to make the whole group false
def minimum(group: Group) -> bool:
    return all(group)


# true if at least half of the values are true, Th_ceil(n/2)
# >= is the tie rule, a tie counts as true
# 2 * sum keeps the comparison in whole numbers, no float is compared
def majority(group: Group) -> bool:
    return 2 * sum(group) >= len(group)


