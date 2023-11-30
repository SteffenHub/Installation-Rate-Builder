from ortools.sat.python import cp_model


def read_txt_file(name_of_file_with_ending: str) -> list[str]:
    """
    Reads a txt and returns content in a list of strings
    :param name_of_file_with_ending: The file name with ending(.txt)
    :return: content of the file as a list of strings
    """
    lines = []
    with open(name_of_file_with_ending, 'r') as f:
        for line in f:
            lines.append(line.strip())
    return lines


def save_model_to_dir(model: cp_model.CpModel, name_of_file: str, number_of_variables: int,
                      number_of_decimal_places: int, all_vars: dict[str, cp_model.IntVar]):
    frequencies = []
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status is cp_model.FEASIBLE or cp_model.OPTIMAL:
        for var in range(1, number_of_variables + 1):
            frequencies.append(solver.Value(all_vars[str(var) + "_freq"]) / number_of_decimal_places)
    else:
        print("Solver found no solution. File was not saved")
        return

    with open(name_of_file, "w") as f:
        for freq in frequencies:
            f.write(f"{freq}\n")
