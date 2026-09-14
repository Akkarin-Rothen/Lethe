from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .aggregation import Aggregate, majority, maximum, minimum
from .formulas import CATALOG, resolve as resolve_formula
from .marginalization import forget
from .parser import ParseError
from .render import csv, latex, text
from .syntax import signature
from .truth_tables import TruthTable


def _parse_atom_list(value: str) -> list[str]:
    atoms = [atom.strip() for atom in value.replace(" ", ",").split(",")]
    return [atom for atom in atoms if atom]


# the aggregates that can be named on the command line
# threshold is not in here, it needs a k and is asked for as th<k>
# maj is the column title of majority, so it is accepted as well and the names round-trip
NAMED = {
    "max": maximum,
    "min": minimum,
    "majority": majority,
    "maj": majority,
}

# the names that stand for several aggregates or for a computed k
# all        the three named ones plus th1 to th<n>
# thresholds th1 to th<n>
# thmaj      the one threshold that is the majority vote, ceil(n / 2)
GROUP_NAMES = ("all", "thresholds", "thmaj")


# the k of the threshold that equals the majority vote
# (n + 1) // 2 is ceil(n / 2) in whole numbers, a float would have to be rounded
# example: 4 gives 2, 8 gives 4, 2 gives 1, so for two rows thmaj is th1 and that is max
def _majority_k(group_size: int) -> int:
    return (group_size + 1) // 2


# reads the -a option into the two lists that forget wants
# aggregates take only a group, thresholds need their k, so they are kept apart
# names are read in lower case, so MAX and Max are max
# example: "max,min,majority" gives ([maximum, minimum, majority], [])
# example: "all" with group size 4 gives ([maximum, minimum, majority], [1, 2, 3, 4])
# example: "max,th2" gives ([maximum], [2])
# example: "thresholds" with group size 4 gives ([], [1, 2, 3, 4])
# example: "thmaj" with group size 4 gives ([], [2])
# example: "all,max" with group size 4 gives the same as "all", max is not counted twice
# example: "" raises ValueError, a comparison with nothing to compare would exit 0 otherwise
# an unknown name raises KeyError, main turns that into exit code 2
def _parse_aggregates(
    value: str, group_size: int
) -> tuple[list[Aggregate], list[int]]:
    names = []
    for name in _parse_atom_list(value):
        name = name.lower()
        if name == "all":
            names.append("max")
            names.append("min")
            names.append("majority")
            name = "thresholds"
        if name == "thresholds":
            for k in range(1, group_size + 1):
                names.append(f"th{k}")
        elif name == "thmaj":
            names.append(f"th{_majority_k(group_size)}")
        else:
            names.append(name)

    if not names:
        raise ValueError("no aggregate given, -a needs at least one name")

    # a name given twice would print the same column twice, dict.fromkeys keeps the first
    # of each and the order, a set would lose the order
    # example: "all,max" names max twice, "thmaj,thresholds" names th2 twice
    names = list(dict.fromkeys(names))

    aggregates = []
    thresholds = []
    for name in names:
        if name in NAMED:
            aggregates.append(NAMED[name])
        elif name.startswith("th") and name[2:].isdigit():
            thresholds.append(int(name[2:]))
        else:
            raise KeyError(
                f"unknown aggregate {name!r}, expected one of "
                f"{', '.join(NAMED)}, th<k>, for example th3, "
                f"or {', '.join(GROUP_NAMES)}"
            )
    return aggregates, thresholds


# the default for -a, the three named aggregates
DEFAULT_AGGREGATES = "max,min,majority"


# prints the text, or writes it to a file when -o was given
# unlike a shell redirect this never empties an existing file on an error,
# because the program only writes after everything worked
# a missing directory in the path is left to the caller, so a typo in -o cannot create folders
# example: -o out.tex writes the file and prints "wrote out.tex"
def _emit(output: str, out: str | None) -> None:
    if out is None:
        print(output)
    else:
        Path(out).write_text(output + "\n", encoding="utf-8")
        print(f"wrote {out}")


# lists the catalog, one line per formula, as text or as CSV
# example: F1 (a | b) & c  3 atoms  3 of 8 true
def command_formulas(args: argparse.Namespace) -> int:
    header = ["name", "formula", "atoms", "true rows"]
    rows = []
    for entry in CATALOG.values():
        rows.append([
            entry.name,
            entry.formula_str,
            str(entry.atom_count()),
            f"{entry.true_rows()} of {len(entry.table())}",
        ])
    if args.csv:
        _emit(csv._table(header, rows), args.out)
    else:
        _emit(text._table(header, rows), args.out)
    return 0


# prints the full truth table of one formula, as text, as LaTeX or as CSV
def command_table(args: argparse.Namespace) -> int:
    formula = resolve_formula(args.formula)
    table = TruthTable.build(formula)
    if args.latex:
        _emit(latex.truth_table(table, caption=args.caption, label=args.label), args.out)
        return 0
    if args.csv:
        _emit(csv.truth_table(table, column=str(formula)), args.out)
        return 0

    lines = [
        f"formula   {formula}",
        f"atoms     {{{', '.join(table.atom_names)}}}",
        f"true rows {table.true_rows()} of {len(table)}",
        "",
        text.truth_table(table, column=str(formula)),
    ]
    _emit("\n".join(lines), args.out)
    return 0


# forgets the given atoms and prints both tables, as text, as LaTeX or as CSV
def command_forget(args: argparse.Namespace) -> int:
    formula = resolve_formula(args.formula)
    forgotten = _parse_atom_list(args.forget)

    # "all" uses the group size before forgetting: 2 ** |Gamma|.
    # Count only atoms that occur in the formula, since forget() rejects unknown atoms anyway.
    # This also prevents typos in -f from generating a huge number of unnecessary names.
    # Example: -f b,c on (a | b) & c -> 4, but -f b,z -> 2, not 4.
    group_size = 2 ** len(set(forgotten) & set(signature(formula)))
    aggregates, thresholds = _parse_aggregates(args.aggregates, group_size)
    result = forget(formula, forgotten, aggregates, thresholds)

    # --no-var-forget hides the column, the flag says what is removed, the renderer what is shown
    show_var_forget = not args.no_var_forget

    # --groups picks the renderer with one row per group, the rest of the call stays the same
    if args.latex:
        if args.groups:
            render_after = latex.group_table
        else:
            render_after = latex.forget_table
        lines = [
            latex.truth_table(result.table),
            "",
            render_after(
                result,
                caption=args.caption,
                label=args.label,
                colour_groups=not args.no_colour,
                show_var_forget=show_var_forget,
            ),
        ]
        _emit("\n".join(lines), args.out)
        return 0

    if args.csv:
        # one file holds one table, so CSV prints only the table after forgetting
        # the table before forgetting is "table F --csv"
        if args.groups:
            output = csv.group_table(result, show_var_forget=show_var_forget)
        else:
            output = csv.forget_table(result, show_var_forget=show_var_forget)
        _emit(output, args.out)
        return 0

    if args.groups:
        render_after = text.group_table
    else:
        render_after = text.forget_table
    lines = [
        text.summary(result),
        "",
        "before forgetting:",
        text.truth_table(result.table, column=str(formula)),
        "",
        f"after forgetting {{{', '.join(result.forgotten)}}}:",
        render_after(result, show_var_forget=show_var_forget),
    ]
    _emit("\n".join(lines), args.out)
    return 0


# -- argument parsing ------------------------------------------------------


# the options every command shares: the output format and the output file
# --latex and --csv exclude each other, argparse refuses both in one call
# formulas has no LaTeX renderer, so it asks for the group without --latex
def _add_output_options(
    command: argparse.ArgumentParser, *, with_latex: bool = True
) -> None:
    formats = command.add_mutually_exclusive_group()
    if with_latex:
        formats.add_argument(
            "--latex", action="store_true", help="emit LaTeX tables instead of text"
        )
    formats.add_argument(
        "--csv", action="store_true", help="emit CSV instead of text"
    )
    command.add_argument(
        "-o", "--out", help="write to this file instead of printing"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lethe",
        description=(
            "Forget propositional variables semantically with different "
            "aggregate functions and compare the result with classical "
            "syntactic variable forgetting."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"lethe {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    formulas = subparsers.add_parser(
        "formulas", help="list the formulas chosen for the evaluation"
    )
    _add_output_options(formulas, with_latex=False)
    formulas.set_defaults(handler=command_formulas)

    table = subparsers.add_parser(
        "table", help="print the truth table of a formula"
    )
    table.add_argument(
        "formula", help="a formula in program syntax, or a catalog name like F1"
    )
    _add_output_options(table)
    table.add_argument(
        "--caption",
        help="LaTeX caption of the table, with --latex (default: names the formula)",
    )
    table.add_argument(
        "--label",
        help="LaTeX label of the table, with --latex (default: tab:truthtab)",
    )
    table.set_defaults(handler=command_table)

    forgetting = subparsers.add_parser(
        "forget", help="forget a subsignature and compare the aggregators"
    )
    forgetting.add_argument(
        "formula", help="a formula in program syntax, or a catalog name like F1"
    )
    forgetting.add_argument(
        "-f",
        "--forget",
        required=True,
        help="the atoms to forget, for example 'b,c'",
    )
    forgetting.add_argument(
        "-a",
        "--aggregates",
        default=DEFAULT_AGGREGATES,
        help=(
            "comma separated aggregates: max, min, majority (or maj), th<k>, "
            "thmaj, thresholds or all "
            f"(default: {DEFAULT_AGGREGATES})"
        ),
    )
    _add_output_options(forgetting)
    forgetting.add_argument(
        "--caption",
        help="LaTeX caption of the forgetting table, with --latex (default: names the formula and the forgotten atoms)",
    )
    forgetting.add_argument(
        "--label",
        help="LaTeX label of the forgetting table, with --latex (default: tab:truthtabforg)",
    )
    forgetting.add_argument(
        "--no-colour",
        action="store_true",
        help="do not colour the groups, with --latex (the output then needs no xcolor)",
    )
    forgetting.add_argument(
        "--no-var-forget",
        action="store_true",
        help="leave out the VarForget column",
    )
    forgetting.add_argument(
        "--groups",
        action="store_true",
        help="one row per group instead of one row per interpretation",
    )
    forgetting.set_defaults(handler=command_forget)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except KeyError as error:
        # str() of a KeyError keeps the quotes around the message, args[0] does not
        print(f"error: {error.args[0]}", file=sys.stderr)
        return 2
    except (OSError, ParseError, ValueError) as error:
        # OSError is -o into a missing directory or a file without write permission
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
