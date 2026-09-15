# text.py renders truth tables as plain text for the terminal.
# the module has no logic of its own, everything it prints is already computed.

# For error-free use of annotations
from __future__ import annotations

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


# a cell that is only filled in the last row of a group, else it stays empty
# example: True with last=True gives "1", with last=False gives ""
def _only_last(value: bool, last: bool) -> str:
    if last:
        return _cell(value)
    else:
        return EMPTY


# the width of every column, the widest of header and all cells
# example: header ["a", "(a | b) & c"] with one row gives [1, 11]
def _widths(header: list[str], rows: list[list[str]]) -> list[int]:
    widths = []
    for column in header:
        widths.append(len(column))
    for row in rows:
        for index, cell in enumerate(row):
            if len(cell) > widths[index]:
                widths[index] = len(cell)
    return widths


# one row of the table, every cell centred in its column
# example: ["0", "1"] with widths [1, 3] gives "| 0 |  1  |"
def _line(cells: list[str], widths: list[int]) -> str:
    padded = []
    for cell, width in zip(cells, widths):
        padded.append(cell.center(width))
    return "| " + " | ".join(padded) + " |"


# the horizontal rule above, below and under the header
# example: widths [1, 3] give "+---+-----+"
def _rule(widths: list[int]) -> str:
    parts = []
    for width in widths:
        parts.append("-" * (width + 2))
    return "+" + "+".join(parts) + "+"


# builds the whole frame from a header and the rows
# notes is one text per data row, written to the right of the frame
# an empty text or no notes at all leaves the line as it is
def _table(
    header: list[str],
    rows: list[list[str]],
    notes: list[str] | None = None,
) -> str:
    widths = _widths(header, rows)
    rule = _rule(widths)

    output = [rule, _line(header, widths), rule]
    for index, row in enumerate(rows):
        line = _line(row, widths)
        if notes is not None and notes[index]:
            line = line + "   " + notes[index]
        output.append(line)
    output.append(rule)
    return "\n".join(output)


# the full truth table of one formula, one row per interpretation
# column is the caption of the last column, the formula itself by default
# example: (a | b) & c gives 8 rows with the columns a, b, c and the formula
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


# the grouped table after forgetting
# the result is not a smaller table but the old one with blanked columns
# the forgotten atoms keep their place, their cells stay empty
# an aggregated value belongs to a whole group, so it is printed once, in the last row
# example: forgetting b and c from (a | b) & c gives 8 rows and two filled rows
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
    notes = []
    for position, group in enumerate(result.groups):
        # the note goes beside the first two rows of the group, as in the thesis
        # example: "group a=0" and "1 of 4 rows true"
        pairs = []
        for atom, bit in zip(result.kept, group.key):
            pairs.append(f"{atom}={_cell(bit)}")
        group_notes = ["group " + ", ".join(pairs),
                       f"{group.true_count()} of {group.size()} rows true"]

        for index, row in enumerate(group.rows):
            last = index == group.size() - 1
            if index < len(group_notes):
                notes.append(group_notes[index])
            else:
                notes.append(EMPTY)

            cells = []
            for bit, shown in zip(row, keep):
                if shown:
                    cells.append(_cell(bit))
                else:
                    cells.append(EMPTY)
            cells.append(_cell(group.values[index]))

            for name in result.column_names():
                value = result.values_of(name)[position]
                cells.append(_only_last(value, last))

            if show_var_forget:
                cells.append(_only_last(result.var_forget_values[position], last))

            rows.append(cells)
    return _table(header, rows, notes)


# one row per group instead of one row per interpretation
# then one column per aggregate; no notes, the row already is the group
# example: forgetting b and c from (a | b) & c gives two rows
#   a | true_rows | group_size | max | min | maj | VarForget
#   0 |     1     |     4      |  1  |  0  |  0  |     1
#   1 |     2     |     4      |  1  |  0  |  1  |     1
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


# a short report on one forgetting run, one fact per line
# example: it names the formula, the atoms, the group size and which aggregate agrees
def summary(result: ForgetResult) -> str:
    lines = [
        f"formula        {result.formula}",
        f"atoms          {{{', '.join(result.atom_names)}}}",
        f"forgotten      {{{', '.join(result.forgotten)}}}",
        f"kept           {{{', '.join(result.kept)}}}",
        f"group size     {result.group_size()}",
        f"VarForget      {result.var_forget_formula}",
    ]
    for name in result.column_names():
        if result.agrees_with_var_forget(name):
            verdict = "agrees with"
        else:
            verdict = "differs from"
        lines.append(f"  {column_title(name):<10} {verdict} VarForget")
    return "\n".join(lines)
