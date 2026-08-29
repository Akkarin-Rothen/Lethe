from __future__ import annotations


import itertools
from dataclasses import dataclass

# Import type alias Assignment, class Formula and fuction signature from syntax.py
from .syntax import Assignment, Formula, signature

Interpretation = tuple[bool, ...]

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

