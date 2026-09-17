from itertools import combinations

FORMULAS = {
    "F1": ("abc", r"(a \lor b) \land c"),
    "F2": ("abcd", r"a \land b \land c \land d"),
    "F3": ("abcd", r"a \lor b \lor c \lor d"),
    "F4": ("abcd", r"(a \land b) \rightarrow (c \lor d)"),
    "F5": ("abc", r"(a \leftrightarrow b) \leftrightarrow c"),
    "F6": ("abc", r"(a \land b \land c) \lor (a \land \lnot b \land c)"),
    "F7": ("abcdef", r"(a \lor b) \land (c \lor d) \land (e \lor f)"),
}


def subsets(atoms):
    for size in len(atoms):
        for combo in combinations(atoms, size):
            yield "".join(combo)


def text_commands():
    for name, (atoms, _) in FORMULAS.items():
        yield f"python3 -m lethe table {name} -o data_text/{name}_table.txt"
        for sub in subsets(atoms):
            forget = ",".join(sub)
            yield f"python3 -m lethe forget {name} -f {forget} -a all -o data_text/{name}_{sub}.txt"
            yield f"python3 -m lethe forget {name} -f {forget} -a all --groups -o data_text/{name}_{sub}_groups.txt"


def csv_commands():
    for name, (atoms, _) in FORMULAS.items():
        yield f"python3 -m lethe table {name} --csv -o data_csv/{name}_table.csv"
        for sub in subsets(atoms):
            forget = ",".join(sub)
            yield f"python3 -m lethe forget {name} -f {forget} -a all --csv -o data_csv/{name}_{sub}.csv"
            yield f"python3 -m lethe forget {name} -f {forget} -a all --csv --groups -o data_csv/{name}_{sub}_groups.csv"


def latex_commands():
    for name, (atoms, latex) in FORMULAS.items():
        number = name[1:]
        yield f"python3 -m lethe table {name} --latex -o data_latex/{name}_table.tex"
        for sub in subsets(atoms):
            forget = ",".join(sub)
            gamma = ", ".join(sub)
            formula = f"$F_{{{number}}} = {latex}$"
            caption = f"'Lethe: Forgetting $\\{{{gamma}\\}}$ in {formula}.'"
            caption_groups = f"'Lethe: Groups after forgetting $\\{{{gamma}\\}}$ in {formula}.'"
            yield f"python3 -m lethe forget {name} -f {forget} -a all --latex --caption {caption} --label tab:lethe-{name}-{sub} -o data_latex/{name}_{sub}.tex"
            yield f"python3 -m lethe forget {name} -f {forget} -a all --latex --groups --caption {caption_groups} --label tab:lethe-{name}-{sub}-groups -o data_latex/{name}_{sub}_groups.tex"


def write(path, commands):
    with open(path, "w") as file:
        for command in commands:
            file.write(command + "\n")


write("commands_text.txt", text_commands())
write("commands_csv.txt", csv_commands())
write("commands_latex.txt", latex_commands())
