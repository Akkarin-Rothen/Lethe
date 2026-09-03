from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .aggregation import Aggregate, majority, maximum, minimum
from .formulas import CATALOG, resolve as resolve_formula
from .marginalization import forget
from .parser import ParseError
from .render import latex, text
from .truth_tables import TruthTable


def _parse_atom_list(value: str) -> list[str]:
    atoms = [atom.strip() for atom in value.replace(" ", ",").split(",")]
    return [atom for atom in atoms if atom]


# the aggregates that can be named on the command line
# threshold is not in here, it needs a k and is asked for as th<k>
NAMED = {
    "max": maximum,
    "min": minimum,
    "majority": majority,
}


# reads the -a option into the two lists that forget wants
# aggregates take only a group, thresholds need their k, so they are kept apart
# "all" means the three named ones plus every threshold from 1 to the group size
# example: "max,min,majority" gives ([maximum, minimum, majority], [])
# example: "all" with group size 4 gives ([maximum, minimum, majority], [1, 2, 3, 4])
# example: "max,th2" gives ([maximum], [2])
# an unknown name raises KeyError, main turns that into exit code 2
def _parse_aggregates(
    value: str, group_size: int
) -> tuple[list[Aggregate], list[int]]:
    names = _parse_atom_list(value)

    if names == ["all"]:
        names = ["max", "min", "majority"]
        for k in range(1, group_size + 1):
            names.append(f"th{k}")

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
                f"{', '.join(NAMED)} or th<k>, for example th3"
            )
    return aggregates, thresholds


# the default for -a, the three named aggregates
DEFAULT_AGGREGATES = "max,min,majority"


# prints the text, or writes it to a file when -o was given
# unlike a shell redirect this never empties an existing file on an error,
# because the program only writes after everything worked
# example: -o out.tex writes the file and prints "wrote out.tex"
def _emit(output: str, out: str | None) -> None:
    if out is None:
        print(output)
    else:
        Path(out).write_text(output + "\n", encoding="utf-8")
        print(f"wrote {out}")


# lists the catalog, one line per formula
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
    print(text._table(header, rows))
    return 0


# prints the full truth table of one formula, as text or as LaTeX
def command_table(args: argparse.Namespace) -> int:
    formula = resolve_formula(args.formula)
    table = TruthTable.build(formula)
    if args.latex:
        _emit(latex.truth_table(table), args.out)
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


# forgets the given atoms and prints both tables, as text or as LaTeX
def command_forget(args: argparse.Namespace) -> int:
    formula = resolve_formula(args.formula)
    forgotten = _parse_atom_list(args.forget)

    # the group size is needed before forgetting, so that "all" knows how many
    # thresholds there are
    group_size = 2 ** len(set(forgotten))
    aggregates, thresholds = _parse_aggregates(args.aggregates, group_size)
    result = forget(formula, forgotten, aggregates, thresholds)

    if args.latex:
        lines = [latex.truth_table(result.table), "", latex.forget_table(result)]
        _emit("\n".join(lines), args.out)
        return 0

    lines = [
        text.summary(result),
        "",
        "before forgetting:",
        text.truth_table(result.table, column=str(formula)),
        "",
        f"after forgetting {{{', '.join(result.forgotten)}}}:",
        text.forget_table(result),
    ]
    _emit("\n".join(lines), args.out)
    return 0


# -- argument parsing ------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lethe",
        description=(
            "Forget propositional variables semantically with different "
            "aggregate functions and compare the result with classical "
            "syntactic variable forgetting."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    formulas = subparsers.add_parser(
        "formulas", help="list the formulas chosen for the evaluation"
    )
    formulas.set_defaults(handler=command_formulas)

    table = subparsers.add_parser(
        "table", help="print the truth table of a formula"
    )
    table.add_argument(
        "formula", help="a formula in program syntax, or a catalog name like F1"
    )
    table.add_argument(
        "--latex", action="store_true", help="emit a LaTeX table instead of text"
    )
    table.add_argument(
        "-o", "--out", help="write to this file instead of printing"
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
            "comma separated aggregates: max, min, majority, th<k> or 'all' "
            f"(default: {DEFAULT_AGGREGATES})"
        ),
    )
    forgetting.add_argument(
        "--latex", action="store_true", help="emit LaTeX tables instead of text"
    )
    forgetting.add_argument(
        "-o", "--out", help="write to this file instead of printing"
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
    except (ParseError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())