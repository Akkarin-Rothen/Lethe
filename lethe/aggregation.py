from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

#: A group of truth values taken from the rows of one group, with multiplicity.
Group = Sequence[bool]



# Returns true if at least one elemen in group is true
def maximum(group: Group) -> bool:
    return any(group)

# Returns true if all is true
# false wins if at least one value is false.xs
def minimum(group: Group) -> bool:
    return all(group)


def majority(group: Group) -> bool:
    return 2 * sum(group) >= len(group)

def binary_mean(group: Group) -> float:
    return sum(group) / len(group)