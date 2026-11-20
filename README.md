# Lethe
A propositional logic program for generating truth tables and computing variable forgetting with different semantic approaches.

## Usage

Pure Python 3.10+, no dependencies. No installation required.
Run all commands from the `Lethe/` directory:

```sh
cd Lethe
python3 -m lethe <command>
python3 -m lethe --version
```

Output is plain text by default. Shared options:

| Option | Meaning |
|---|---|
| `--csv` | Output CSV |
| `--latex` | Output LaTeX (`table` and `forget` only), excludes `--csv` |
| `-o`, `--out` | Write to this file instead of printing |

## Commands

### `formulas` — display the catalog F1 to F7

```sh
python3 -m lethe formulas
python3 -m lethe formulas --csv -o catalog.csv
```

### `table` — truth table of a formula

```sh
python3 -m lethe table F1
python3 -m lethe table "(a|b)&c"
python3 -m lethe table F1 --latex --caption 'Truth table of $F_1$.' --label tab:f1
python3 -m lethe table F1 --csv
```

The argument is a catalog name (`F1` to `F7`) or a formula.

| Option | Meaning |
|---|---|
| `--caption` | LaTeX caption. Default names the formula |
| `--label` | LaTeX label, default `tab:truthtab` |

### `forget` — forget atoms

```sh
python3 -m lethe forget F1 -f b,c
python3 -m lethe forget F1 -f b,c -a all
python3 -m lethe forget F1 -f b,c -a max,th2 --latex -o f1-bc.tex
python3 -m lethe forget F1 -f b,c --csv --groups
```

| Option | Meaning |
|---|---|
| `-f`, `--forget` | Required. Atoms to forget, e.g. `b,c` |
| `-a`, `--aggregates` | Aggregates to compare, default `max,min,majority`. See below |
| `--groups` | One row per group instead of one row per interpretation |
| `--no-var-forget` | Leave out the `VarForget` column |
| `--caption` | LaTeX caption of the table after forgetting |
| `--label` | LaTeX label of the table after forgetting, default `tab:truthtabforg` (`tab:groupsforg` with `--groups`) |
| `--no-colour` | LaTeX without colours, so no `xcolor` is needed |

The coloured LaTeX output needs `\usepackage[table]{xcolor}` in the document.

## Aggregates

| Name | Meaning |
|---|---|
| `max` | true if at least one row is true (classical forgetting, equals `VarForget`) |
| `majority`, `maj` | true if at least half the rows are true |
| `min` | true only if all rows are true |
| `th<k>` | true if at least `k` rows are true, `1 ≤ k ≤ n` |
| `thmaj` | the threshold that equals `majority` |
| `thresholds` | `th1` to `thn` |
| `all` | `max`, `min`, `maj` and `th1` to `thn` |

`n = 2^(number of forgotten atoms)` is the group size. Names may be combined,
e.g. `-a all,th2`.

## Formula Syntax

| Character | Meaning | Unicode also accepted |
|---|---|---|
| `!` | Negation | `¬` |
| `&` | Conjunction | `∧` |
| `\|` | Disjunction | `∨` |
| `>` | Implication | `→` |
| `=` | Equivalence | `↔` |
| `1`, `0` | True, False | `⊤`, `⊥` |

Precedence, from highest to lowest: `!`, `&`, `|`, `>`, `=`.
`>` is right-associative; all others are left-associative.

An atom is one letter, optionally followed by digits: `a`, `b`, `p1`.

**Quote every formula that contains operators or parentheses**, e.g.
`'(a|b)&c'`, otherwise the shell interprets them.

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | All good |
| `2` | Input error, message printed to stderr |
