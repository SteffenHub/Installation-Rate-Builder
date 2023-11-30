def dimacs_str_to_int_list(dimacs_lines: list[str]) -> list[list[int]]:
    result = []
    for line in dimacs_lines:
        # skip comments and meta data
        if line.startswith('c') or line.startswith('p'):
            continue
        # convert row into int list
        clause = list(map(int, line.strip().split()))
        # remove 0 from line end
        if clause[-1] == 0:
            clause = clause[:-1]
        result.append(clause)
    return result


def extract_counts_from_dimacs(dimacs_lines: list[str]) -> tuple[int, int]:
    for line in dimacs_lines:
        if line.startswith('p cnf'):
            _, _, num_vars, num_clauses = line.split()
            return int(num_vars), int(num_clauses)
    raise ValueError("No matching 'p cnf' line found.")
