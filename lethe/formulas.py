# formulas.py holds the formulas for evaluation.
# each one is stored as text and parsed once when the entry is built.

# For error-free use of annotations
from __future__ import annotations

# field is needed for formula, the one attribute that is derived and not passed in
from dataclasses import dataclass, field

from .parser import parse
from .truth_tables import TruthTable
from .syntax import Formula


# one formula of the catalog
@dataclass(frozen=True)
class CatalogEntry:
    # the short name used on the command line
    # example: "F1"
    name: str
    # the formula as text, exactly as it is written in the thesis
    # example: "(a | b) & c"
    formula_str: str
    # the parsed tree, built from formula_str in __post_init__
    # field(init=False) keeps it out of __init__, so CatalogEntry takes two arguments
    # example: And(Or(Atom(a), Atom(b)), Atom(c))
    formula: Formula = field(init=False)

    # runs right after __init__ and fills the derived field
    # object.__setattr__ is needed because the class is frozen
    # self.formula = ... would raise FrozenInstanceError
    # it runs once, while the object is being built, so nothing is really changed later
    def __post_init__(self) -> None:
        object.__setattr__(self, "formula", parse(self.formula_str))

    # builds the truth table fresh on every call
    # example: F1 gives 8 rows with the values (F,F,F,T,F,T,F,T)
    def table(self) -> TruthTable:
        return TruthTable.build(self.formula)

    # how many atoms the formula has
    # example: F1 gives 3, F7 gives 6
    def atom_count(self) -> int:
        return len(self.table().atom_names)

    # how many rows of the table are true
    # example: F2 gives 1 of 16, F3 gives 15 of 16, the two poles of the catalog
    def true_rows(self) -> int:
        return self.table().true_rows()


# the seven formulas, name -> entry
# every one covers at least one selection criterion
CATALOG: dict[str, CatalogEntry] = {
    "F1": CatalogEntry("F1", "(a | b) & c"),
    "F2": CatalogEntry("F2", "a & b & c & d"),
    "F3": CatalogEntry("F3", "a | b | c | d"),
    "F4": CatalogEntry("F4", "(a & b) > (c | d)"),
    "F5": CatalogEntry("F5", "(a = b) = c"),
    "F6": CatalogEntry("F6", "(a & b & c) | (a & !b & c)"),
    "F7": CatalogEntry("F7", "(a | b) & (c | d) & (e | f)"),
    "F8": CatalogEntry("F8", "a | (b & c)"),
}


# looks up an entry by name, upper and lower case both work
# example: get("f1") and get("F1") give the same entry
# example: get("F9") raises KeyError and lists the valid names
def get(name: str) -> CatalogEntry:
    try:
        return CATALOG[name.upper()]
    except KeyError:
        raise KeyError(
            f"unknown formula {name!r}; expected one of {', '.join(CATALOG)}"
        ) from None


# takes either a catalog name or a formula as text
# this is what lets the command line accept both F1 and "(a|b)&c"
# example: resolve("F1") and resolve("(a|b)&c") give the same tree
# example: resolve("a&b") parses the text, a & b is not in the catalog
def resolve(text: str) -> Formula:
    if text.upper() in CATALOG:
        return CATALOG[text.upper()].formula
    return parse(text)
