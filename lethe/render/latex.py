# latex.py prints truth tables as LaTeX, ready to paste into a document.
# it computes nothing, it only formats.
# the output needs tabular and \rowcolor from xcolor with the table option.

# For error-free use of annotations
from __future__ import annotations

from ..aggregation import column_title
from ..marginalization import ForgetResult
from ..truth_tables import TruthTable

# one colour per group, used in turn and starting again at the front
# example: two groups give gray!40 and blue!40
GROUP_COLOURS = ("gray!40", "blue!40", "red!40", "green!40", "yellow!40")

EMPTY = ""


# one truth value as a single character
# example: True gives "1", False gives "0"
def _cell(value: bool) -> str:
    if value:
        return "1"
    else:
        return "0"


# a whole row as cells
# example: (F, T, T) gives ["0", "1", "1"]
def _cells(values) -> list[str]:
    cells = []
    for value in values:
        cells.append(_cell(value))
    return cells


# only the last row of a group gets the value, the others stay empty
# example: True with last=True gives "1", with last=False gives ""
def _only_last(value: bool, last: bool) -> str:
    if last:
        return _cell(value)
    else:
        return EMPTY


# wraps text in \textbf
# example: "a" gives \textbf{a}
# {{ and }} in the f-string are one brace each
def _bold(text: str) -> str:
    return rf"\textbf{{{text}}}"


# the column specification, a vertical line between every pair of columns
# the atoms, the formula column and the extra columns all get the same "c|"
# example: 3 atoms and 2 extra columns give |c|c|c|c|c|c|
def _column_spec(atom_count: int, extra: int) -> str:
    return "|" + "c|" * (atom_count + 1 + extra)


# joins the cells and closes the row
# example: ["0", "1"] gives "0 & 1 \\ \hline"
def _row(cells: list[str], prefix: str = EMPTY) -> str:
    return prefix + " & ".join(cells) + r" \\ \hline"


# builds the frame around the header and the rows
# rows are finished strings here, LaTeX does the aligning itself
def _document(
    header: list[str],
    rows: list[str],
    *,
    column_spec: str,
    caption: str,
    label: str,
) -> str:
    lines = [
        r"\begin{table}[!tb]",
        r"    \centering",
        rf"    \begin{{tabular}}{{{column_spec}}}",
        r"        \hline",
        "        " + _row(header),
    ]
    for row in rows:
        lines.append("        " + row)
    lines.append(r"    \end{tabular}")
    lines.append(rf"    \caption{{{caption}}}")
    lines.append(rf"    \label{{{label}}}")
    lines.append(r"\end{table}")
    return "\n".join(lines)


# the full truth table of one formula
# example: (a | b) & c gives the spec |c|c|c|c| and eight rows
def truth_table(
    table: TruthTable,
    *,
    caption: str | None = None,
    label: str = "tab:truthtab",
) -> str:
    header = []
    for atom in table.atom_names:
        header.append(_bold(atom))
    header.append(_bold("A"))

    rows = []
    for row, value in zip(table.rows, table.values):
        cells = _cells(row)
        cells.append(_cell(value))
        rows.append(_row(cells))

    # to_latex, not str, so it reads (a \lor b) \land c
    if caption is None:
        caption = f"Truth table for ${table.formula.to_latex()}$."

    return _document(
        header,
        rows,
        column_spec=_column_spec(len(table.atom_names), 0),
        caption=caption,
        label=label,
    )


# the grouped truth table after forgetting
# the forgotten atoms keep their column, only the cells are emptied
# an aggregated value belongs to the whole group, so it stands in the last row
# every group gets its own colour, unless colour_groups is False
# example: forgetting b and c from (a | b) & c gives the spec |c|c|c|c|c|c|c|
def forget_table(
    result: ForgetResult,
    *,
    caption: str | None = None,
    label: str | None = None,
    colour_groups: bool = True,
    show_var_forget: bool = True,
) -> str:
    # True for a kept atom, False for a forgotten one
    # example: ('a','b','c') with kept ('a',) gives [True, False, False]
    keep = []
    header = []

    for atom in result.atom_names:
        keep.append(atom in result.kept)
        header.append(_bold(atom))

    header.append(_bold("A"))

    # only the short name, not $\mathrm{ModMg}_{...}$
    # the column holds one digit, the long title would be ten times as wide
    # the caption says which operation the table shows
    for name in result.column_names():
        header.append(_bold(column_title(name)))
    if show_var_forget:
        header.append(_bold("VarForget"))

    rows = []
    for position, group in enumerate(result.groups):
        # % wraps around when there are more groups than colours
        colour = GROUP_COLOURS[position % len(GROUP_COLOURS)]
        if colour_groups:
            prefix = rf"\rowcolor{{{colour}}} "
        else:
            prefix = EMPTY

        for index, row in enumerate(group.rows):
            last = index == group.size() - 1

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

            rows.append(_row(cells, prefix))

    extra = len(result.column_names())
    if show_var_forget:
        extra = extra + 1

    if caption is None:
        forgotten = ", ".join(result.forgotten)
        formula = result.formula.to_latex()
        caption = (
            rf"Forgetting $\{{{forgotten}\}}$ in $A = {formula}$."
        )
    # None means "not chosen by the caller", so the default label lives only here
    if label is None:
        label = "tab:truthtabforg"

    return _document(
        header,
        rows,
        column_spec=_column_spec(len(result.atom_names), extra),
        caption=caption,
        label=label,
    )
