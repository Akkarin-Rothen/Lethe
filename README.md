# Lethe
A propositional logic program for generating truth tables and computing variable forgetting with different semantic approaches.

## Usage

Pure Python 3.10+, no dependencies. No installation required.

All commands executed from the `Lethe/` directory:

```sh
cd Lethe
python3 -m lethe <command>
```

## Commands

### `formulas` — display the catalog

```sh
python3 -m lethe formulas
```

```
+------+-----------------------------+-------+-----------+
| name |           formula           | atoms | true rows |
+------+-----------------------------+-------+-----------+
|  F1  |         (a | b) & c         |   3   |   3 of 8  |
|  F2  |        a & b & c & d        |   4   |  1 of 16  |
|  F3  |        a | b | c | d        |   4   |  15 of 16 |
|  F4  |      (a & b) > (c | d)      |   4   |  15 of 16 |
|  F5  |         (a = b) = c         |   3   |   4 of 8  |
|  F6  |  (a & b & c) | (a & !b & c) |   3   |   2 of 8  |
|  F7  | (a | b) & (c | d) & (e | f) |   6   |  27 of 64 |
+------+-----------------------------+-------+-----------+
```

### `table` — truth table of a formula

```sh
python3 -m lethe table F1
python3 -m lethe table "(a|b)&c"
python3 -m lethe table F1 --latex
```

Outputs the formula, its atoms, number of true rows, and the full truth table.  
With `--latex`, outputs a ready-to-use `table` environment.

### `forget` — forget atoms

```sh
python3 -m lethe forget F1 -f b,c
python3 -m lethe forget F1 -f b,c -a all
python3 -m lethe forget "(a|b)&c" -f b,c -a max,th2 --latex
```

| Option | Meaning |
|---|---|
| `-f`, `--forget` | Required. Atoms to forget, e.g. `b,c` or `b c` |
| `-a`, `--aggregates` | Aggregation methods, default: `max,min,majority` |
| `--latex` | Output LaTeX instead of plain text |

Output: Summary, full table before forgetting, and full table after forgetting.  
In the second table, forgotten atoms retain their column, but cells are left empty.  
The aggregated value appears in the last row of each group.

## Aggregates

| Name | Meaning | As threshold |
|---|---|---|
| `max` | true if at least one row is true | `th1` |
| `majority` | true if at least half the rows are true (tie counts as true) | `th⌈n/2⌉` |
| `min` | true only if all rows are true | `thn` |
| `th<k>` | true if at least `k` rows are true | — |
| `all` | the three named ones plus `th1` to `thn` | — |

`n = 2^(number of forgotten atoms)` is the group size.  
`max` is the classical case and must match `VarForget`.

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

**Formulas containing `&` or `|` must be enclosed in quotes**, otherwise the shell will parse them incorrectly.  
Catalog names like `F1` do not need quotes.

Atoms are letters, optionally followed by digits: `a`, `b`, `p1`.

## Errors and Exit Codes

| Code | Meaning |
|---|---|
| `0` | All good |
| `2` | Input error, message printed to stderr |

```
$ python3 -m lethe table "a&"
error: unexpected end of formula in 'a&'


$ python3 -m lethe forget F1 -f z
error: cannot forget ['z'], the formula only has ('a', 'b', 'c')


$ python3 -m lethe forget F1 -f a,b,c
error: forgetting every atom leaves nothing to group by


$ python3 -m lethe forget F1 -f b,c -a nope
error: unknown aggregate 'nope', expected one of max, min, majority or th<k>, for example th3
```

A name not in the catalog is parsed as a formula. Thus, `table F9` produces a table with atom `F9`, no error.

## Structure

No module imports a later one.

```
syntax.py            Formula tree, evaluation, output
  parser.py          Text → Tree
  truth_tables.py    Full truth table
  forgetting.py      VarForget, syntactic
aggregation.py       max, min, majority, Th_k
  marginalization.py Group formation, aggregation, comparison with VarForget
  formulas.py        The catalog F1..F7
    render/text.py   Text output
    render/latex.py  LaTeX output
      cli.py         The commands
```