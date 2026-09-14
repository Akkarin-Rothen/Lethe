# Lethe
A propositional logic program for generating truth tables and computing variable forgetting with different semantic approaches.

## Usage

Pure Python 3.10+, no dependencies. No installation required.

All commands executed from the `Lethe/` directory:

```sh
cd Lethe
python3 -m lethe <command>
python3 -m lethe --version
```

Every command prints plain text by default. `--latex` switches to LaTeX,
`--csv` to CSV; the two exclude each other. `-o FILE` writes the output to a
file instead of printing it. These three options are shared by all commands.

## Commands

### `formulas` — display the catalog

```sh
python3 -m lethe formulas
python3 -m lethe formulas --csv
python3 -m lethe formulas --csv -o catalog.csv
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

| Option | Meaning |
|---|---|
| `--csv` | Output CSV instead of plain text |
| `-o`, `--out` | Write to this file instead of printing |

### `table` — truth table of a formula

```sh
python3 -m lethe table F1
python3 -m lethe table "(a|b)&c"
python3 -m lethe table F1 --latex
python3 -m lethe table F1 --latex -o f1.tex
python3 -m lethe table F1 --latex --caption 'Truth table of $F_1$.' --label tab:f1
python3 -m lethe table F1 --csv
```

| Option | Meaning |
|---|---|
| `--latex` | Output LaTeX instead of plain text |
| `--csv` | Output CSV instead of plain text |
| `--caption` | LaTeX caption of the table. Default names the formula. Only with `--latex` |
| `--label` | LaTeX label of the table, default `tab:truthtab`. Only with `--latex` |
| `-o`, `--out` | Write to this file instead of printing |

Outputs the formula, its atoms, number of true rows, and the full truth table.  
With `--latex`, outputs a ready-to-use `table` environment.  
With `--csv`, outputs one header line and one line per interpretation:

```
a,b,c,(a | b) & c
0,0,0,0
0,0,1,0
...
```

### `forget` — forget atoms

```sh
python3 -m lethe forget F1 -f b,c
python3 -m lethe forget F1 -f b,c -a all
python3 -m lethe forget "(a|b)&c" -f b,c -a max,th2 --latex
python3 -m lethe forget F1 -f b,c -a all --latex -o f1-forget.tex
python3 -m lethe forget F1 -f b,c --latex --label tab:f1-forget-bc
python3 -m lethe forget F1 -f b,c --latex --caption 'Forgetting $\{b,c\}$ in $F_1$.'
python3 -m lethe forget F1 -f b,c --latex --no-colour
python3 -m lethe forget F1 -f b,c --no-var-forget
python3 -m lethe forget F1 -f b,c -a all --csv
python3 -m lethe forget F1 -f b,c -a all --csv --groups -o f1-bc.csv
```

| Option | Meaning |
|---|---|
| `-f`, `--forget` | Required. Atoms to forget, e.g. `b,c` or `b c` |
| `-a`, `--aggregates` | Aggregation methods, default: `max,min,majority`. See below |
| `--latex` | Output LaTeX instead of plain text |
| `--csv` | Output CSV instead of plain text |
| `--caption` | LaTeX caption of the forgetting table. Default names the formula and the forgotten atoms. Only with `--latex` |
| `--label` | LaTeX label of the forgetting table, default `tab:truthtabforg`. Only with `--latex` |
| `--no-colour` | Do not colour the groups. The output then needs no `xcolor`. Only with `--latex` |
| `--no-var-forget` | Leave out the `VarForget` column. The summary still reports the comparison |
| `--groups` | One row per group instead of one row per interpretation. Only with `--csv` |
| `-o`, `--out` | Write to this file instead of printing |

Output: Summary, full table before forgetting, and full table after forgetting.  
In the second table, forgotten atoms retain their column, but cells are left empty.  
The aggregated value appears in the last row of each group.

With `--csv` only the table after forgetting is written, one table per file.
The table before forgetting is `table F --csv`. Unlike the text and LaTeX
output, the aggregated value stands in every row of its group, because a CSV
has no frame to show where a group ends and a reader who filters or sorts the
rows would otherwise lose it:

```
a,b,c,(a | b) & c,max,min,maj,VarForget
0,,,0,1,0,0,1
0,,,0,1,0,0,1
0,,,0,1,0,0,1
0,,,1,1,0,0,1
1,,,0,1,0,1,1
...
```

With `--csv --groups` every group is one row. `true_rows` is the number of
true rows in the group, `group_size` is `n`:

```
a,true_rows,group_size,max,min,maj,th1,th2,th3,th4,VarForget
0,1,4,1,0,0,1,0,0,0,1
1,2,4,1,0,1,1,1,0,0,1
```

## Writing to a file

`-o` writes the output to a file and prints `wrote <name>`. It works for text,
LaTeX and CSV.

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

The directory in the path must exist. `-o data/f1.tex` into a missing `data/`
exits with code 2 and `error: [Errno 2] No such file or directory`. The
program does not create directories, so a typo in the path cannot create one.

Every generated file carries the same labels, `tab:truthtab` for the table
before forgetting and `tab:truthtabforg` for the table after. Including two
such files in one document makes LaTeX warn `Label multiply defined`, and
`\ref` then points to whichever table was read last. Give each table its own
label when you generate more than one:

```sh
python3 -m lethe table F1 --latex --label tab:f1 -o f1.tex
python3 -m lethe forget F1 -f b,c --latex --label tab:f1-bc -o f1-bc.tex
python3 -m lethe forget F2 -f c,d --latex --label tab:f2-cd -o f2-cd.tex
```

In the output of `forget`, `--label` and `--caption` address the forgetting
table only. The table before forgetting keeps `tab:truthtab`. If you include it
too, edit or remove that line in the generated file, or generate it separately
with `table F --latex --label ...`.

`--caption` replaces the caption text in the same way. The text is written into
the file verbatim, so it may contain math. Quote it with single quotes so the
shell leaves `$` and `\` alone:

```sh
python3 -m lethe forget F1 -f b,c --latex --caption 'Forgetting $\{b,c\}$ in $F_1$.' -o f1-bc.tex
```

### LaTeX requirements

The forgetting table colours every group with `\rowcolor`. The document that
includes it needs `xcolor` with the `table` option:

```latex
\usepackage[table]{xcolor}
```

Plain `\usepackage{xcolor}` fails with `Undefined control sequence`. Generate
the table with `--no-colour` if you do not want to load `xcolor`; the output
then uses only `tabular`.

## Aggregates

| Name | Meaning | As threshold |
|---|---|---|
| `max` | true if at least one row is true | `th1` |
| `majority`, `maj` | true if at least half the rows are true (tie counts as true) | `th⌈n/2⌉` |
| `min` | true only if all rows are true | `thn` |
| `th<k>` | true if at least `k` rows are true | — |
| `thmaj` | the one threshold that equals `majority`, `th⌈n/2⌉` | — |
| `thresholds` | `th1` to `thn` | — |
| `all` | the three named ones plus `th1` to `thn` | — |

`n = 2^(number of forgotten atoms)` is the group size.  
`max` is the classical case and must match `VarForget`.

Names are not case-sensitive and may be combined freely, `-a all,th2` or
`-a MAX,thmaj`. A name given twice, directly or through `all`, yields one
column. The columns appear in the order the names were given. `-a ""` is an
error, a comparison needs at least one aggregate.

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
| `2` | Input error, message printed to stderr. Also a file that cannot be written |

```
$ python3 -m lethe table "a&"
error: unexpected end of formula in 'a&'


$ python3 -m lethe forget F1 -f z
error: cannot forget ['z'], the formula only has ('a', 'b', 'c')


$ python3 -m lethe forget F1 -f a,b,c
error: forgetting every atom leaves nothing to group by


$ python3 -m lethe forget F1 -f b,c -a nope
error: unknown aggregate 'nope', expected one of max, min, majority, maj, th<k>, for example th3, or all, thresholds, thmaj


$ python3 -m lethe forget F1 -f b,c -a ""
error: no aggregate given, -a needs at least one name


$ python3 -m lethe forget F1 -f b,c --latex --csv
lethe forget: error: argument --csv: not allowed with argument --latex
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
    render/csv.py    CSV output
      cli.py         The commands
```
