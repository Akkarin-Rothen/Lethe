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
python3 -m lethe table F1 --latex -o f1.tex
```

| Option | Meaning |
|---|---|
| `--latex` | Output LaTeX instead of plain text |
| `-o`, `--out` | Write to this file instead of printing |

Outputs the formula, its atoms, number of true rows, and the full truth table.  
With `--latex`, outputs a ready-to-use `table` environment.

### `forget` — forget atoms

```sh
python3 -m lethe forget F1 -f b,c
python3 -m lethe forget F1 -f b,c -a all
python3 -m lethe forget "(a|b)&c" -f b,c -a max,th2 --latex
python3 -m lethe forget F1 -f b,c -a all --latex -o f1-forget.tex
python3 -m lethe forget F1 -f b,c --latex --label tab:f1-forget-bc
python3 -m lethe forget F1 -f b,c --latex --caption 'Forgetting $\{b,c\}$ in $F_1$.'
```

| Option | Meaning |
|---|---|
| `-f`, `--forget` | Required. Atoms to forget, e.g. `b,c` or `b c` |
| `-a`, `--aggregates` | Aggregation methods, default: `max,min,majority` |
| `--latex` | Output LaTeX instead of plain text |
| `--caption` | LaTeX caption of the forgetting table. Default names the formula and the forgotten atoms. Only with `--latex` |
| `--label` | LaTeX label of the forgetting table, default `tab:truthtabforg`. Only with `--latex` |
| `-o`, `--out` | Write to this file instead of printing |

Output: Summary, full table before forgetting, and full table after forgetting.  
In the second table, forgotten atoms retain their column, but cells are left empty.  
The aggregated value appears in the last row of each group.

## Writing to a file

`-o` writes the output to a file and prints `wrote <name>`. It works for text
and for LaTeX.

```sh
python3 -m lethe forget F1 -f b,c -a all --latex -o f1-forget.tex
```

Include the result instead of pasting it, so it stays up to date:

```latex
\input{f1-forget}
```

`-o` is safer than a shell redirect. On an input error nothing is written and
an existing file keeps its content, while `>` empties the file before the
program even starts.

Every generated file carries the same labels, `tab:truthtab` for the table
before forgetting and `tab:truthtabforg` for the table after. Including two
such files in one document makes LaTeX warn `Label multiply defined`, and
`\ref` then points to whichever table was read last. Give each forgetting
table its own label when you generate more than one:

```sh
python3 -m lethe forget F1 -f b,c --latex --label tab:f1-bc -o f1-bc.tex
python3 -m lethe forget F2 -f c,d --latex --label tab:f2-cd -o f2-cd.tex
```

The table before forgetting keeps `tab:truthtab`. If you include it too, edit
or remove that line in the generated file.

`--caption` replaces the caption text of the forgetting table in the same way.
The text is written into the file verbatim, so it may contain math. Quote it
with single quotes so the shell leaves `$` and `\` alone:

```sh
python3 -m lethe forget F1 -f b,c --latex --caption 'Forgetting $\{b,c\}$ in $F_1$.' -o f1-bc.tex
```

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