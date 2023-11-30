
def dimacs_str_to_int_list(dimacs_lines: list[str]) -> list[list[int]]:
    result = []
    for line in dimacs_lines:
        # Kommentarzeilen und Meta-Daten überspringen
        if line.startswith('c') or line.startswith('p'):
            continue

        # Klauselzeile in eine Liste von Integern umwandeln
        clause = list(map(int, line.strip().split()))

        # Die 0 am Ende der Zeile entfernen
        if clause[-1] == 0:
            clause = clause[:-1]

        result.append(clause)
    return result


def extract_counts_from_dimacs(dimacs_lines: list[str]) -> tuple[int, int]:
    for line in dimacs_lines:
        if line.startswith('p cnf'):
            _, _, num_vars, num_clauses = line.split()
            return int(num_vars), int(num_clauses)
    raise ValueError("Keine passende 'p cnf' Zeile gefunden.")