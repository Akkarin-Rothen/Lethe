# This file is necessary so that it can be imported as a regular package without the need for a namespace
# Look at for https://docs.python.org/3/reference/import.html#regular-packages

from __future__ import annotations

from .aggregation import majority, maximum, minimum, threshold
from .formulas import CATALOG
from .forgetting import var_forget
from .marginalization import forget
from .parser import ParseError, parse
from .truth_tables import TruthTable
from .syntax import (
    And,
    Atom,
    BOTTOM,
    Formula,
    Iff,
    Implies,
    Not,
    Or,
    TOP,
    signature,
)

__all__ = [
    "And",
    "Atom",
    "BOTTOM",
    "CATALOG",
    "Formula",
    "Iff",
    "Implies",
    "Not",
    "Or",
    "ParseError",
    "TOP",
    "TruthTable",
    "forget",
    "parse",
    "signature",
    "majority",
    "maximum",
    "minimum",
    "threshold",
    "var_forget",
]
