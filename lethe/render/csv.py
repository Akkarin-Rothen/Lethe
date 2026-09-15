# csv.py writes truth tables as CSV, for spreadsheets and for the evaluation.
# it computes nothing, it only formats.
# the file is named csv.py inside the package, the standard library module is also called csv
# "import csv" below still gets the standard library, because a plain import never looks
# inside the current package, only "from . import csv" would

# For error-free use of annotations
from __future__ import annotations

import csv
import io

from ..aggregation import column_title
from ..marginalization import ForgetResult
from ..truth_tables import TruthTable

TRUE = "1"
FALSE = "0"
EMPTY = ""


# one truth value as a single character
# example: True gives "1", False gives "0"
def _cell(value: bool) -> str:
    if value:
        return TRUE
    else:
        return FALSE


# a whole row of truth values as cells
# example: (F, T, T) gives ["0", "1", "1"]
def _cells(values) -> list[str]:
    cells = []
    for value in values:
        cells.append(_cell(value))
    return cells


# joins header and rows into CSV text
# the csv module does the quoting, so a formula with a comma would still be one cell
# lineterminator is "\n", the default "\r\n" would show up as ^M in a text editor on macOS and Linux
# the trailing newline is cut, _emit adds it back, the same as for text and LaTeX
# example: ["a", "A"] with one row ["0", "1"] gives "a,A\n0,1"
def _table(header: list[str], rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue().rstrip("\n")


# the full truth table of one formula, one row per interpretation
# column is the title of the last column, the formula itself by default
# example: (a | b) & c gives the header a,b,c,(a | b) & c and eight rows
def truth_table(table: TruthTable, *, column: str | None = None) -> str:
    if column is None:
        label = str(table.formula)
    else:
        label = column

    header = list(table.atom_names)
    header.append(label)

    rows = []
    for row, value in zip(table.rows, table.values):
        cells = _cells(row)
        cells.append(_cell(value))
        rows.append(cells)
    return _table(header, rows)


# the grouped table after forgetting, one row per interpretation
# the forgotten atoms keep their column, their cells stay empty, as in text and LaTeX
# the aggregated values stand in every row of the group, not only in the last one
# a CSV has no frame and no colour, so a reader who filters or sorts the rows
# would lose the group value if it stood in one row only
# example: forgetting b and c from (a | b) & c gives 8 rows, the max column is 1 in all of them
def forget_table(result: ForgetResult, *, show_var_forget: bool = True) -> str:
    # True for every atom that is kept, False for every forgotten one
    # example: atom_names ('a','b','c') with kept ('a',) gives [True, False, False]
    keep = []
    header = []
    for atom in result.atom_names:
        keep.append(atom in result.kept)
        header.append(atom)

    header.append(str(result.formula))
    for name in result.column_names():
        header.append(column_title(name))
    if show_var_forget:
        header.append("VarForget")

    rows = []
    for position, group in enumerate(result.groups):
        for index, row in enumerate(group.rows):
            cells = []
            for bit, shown in zip(row, keep):
                if shown:
                    cells.append(_cell(bit))
                else:
                    cells.append(EMPTY)
            cells.append(_cell(group.values[index]))

            for name in result.column_names():
                cells.append(_cell(result.values_of(name)[position]))

            if show_var_forget:
                cells.append(_cell(result.var_forget_values[position]))

            rows.append(cells)
    return _table(header, rows)


# one row per group instead of one row per interpretation
# this is the table the aggregates are computed from: the kept atoms name the group,
# example: forgetting b and c from (a | b) & c gives two rows
#   a,true_rows,group_size,max,min,maj,VarForget
#   0,1,4,1,0,0,1
#   1,2,4,1,0,1,1
def group_table(result: ForgetResult, *, show_var_forget: bool = True) -> str:
    header = list(result.kept)
    header.append("true_rows")
    header.append("group_size")
    for name in result.column_names():
        header.append(column_title(name))
    if show_var_forget:
        header.append("VarForget")

    rows = []
    for position, group in enumerate(result.groups):
        cells = _cells(group.key)
        cells.append(str(group.true_count()))
        cells.append(str(group.size()))

        for name in result.column_names():
            cells.append(_cell(result.values_of(name)[position]))

        if show_var_forget:
            cells.append(_cell(result.var_forget_values[position]))

        rows.append(cells)
    return _table(header, rows)
