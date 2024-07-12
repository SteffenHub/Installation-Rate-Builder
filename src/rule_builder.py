from ortools.sat.python import cp_model


def create_all_vars(number_of_variables: int, number_of_decimal_places: int, model: cp_model.CpModel) -> \
        dict[str, cp_model.IntVar]:
    all_vars = {}
    for var in range(1, number_of_variables + 1):
        for block in range(1, number_of_decimal_places + 1):
            all_vars[str(var) + "." + str(block)] = model.NewBoolVar(str(var) + "." + str(block))
    return all_vars


def add_all_rules_from_dimacs(cnf_int: list[list[int]], number_of_decimal_places: int, model: cp_model.CpModel,
                              all_vars: dict[str, cp_model.IntVar]):
    # TODO If KeyError print it might be because the line p cnf n i in the cnf file is wrong
    for rule in cnf_int:
        for block in range(1, number_of_decimal_places + 1):
            model.AddBoolOr(
                [all_vars[str(var) + "." + str(block)] if var >= 0 else
                 all_vars[str(abs(var)) + "." + str(block)].Not() for var in rule])


def create_freq_of_vars(number_of_variables: int, all_vars: dict[str, cp_model.IntVar], model: cp_model.CpModel,
                        number_of_decimal_places: int):
    for var in range(1, number_of_variables + 1):
        all_vars[str(var) + "_freq"] = model.NewIntVar(0, number_of_decimal_places, str(var) + "_freq")
        model.Add(all_vars[str(var) + "_freq"] == sum(
            [all_vars[str(var) + "." + str(block)] for block in range(1, number_of_decimal_places + 1)]))


def get_sum_zero_freq(number_of_variables: int, model: cp_model.CpModel,
                      all_vars: dict[str, cp_model.IntVar]) -> cp_model.IntVar:
    for var in range(1, number_of_variables + 1):
        help_var_zero = model.NewBoolVar(f"var_has_zero_freq_{var}")
        model.Add(all_vars[str(var) + "_freq"] == 0).OnlyEnforceIf(help_var_zero)
        model.Add(all_vars[str(var) + "_freq"] > 0).OnlyEnforceIf(help_var_zero.Not())
        all_vars[f"var_has_zero_freq_{var}"] = help_var_zero

    number_of_zero_freq_vars = model.NewIntVar(0, number_of_variables, "number_of_zero_freq_vars")
    model.Add(
        number_of_zero_freq_vars == sum(
            [all_vars[f"var_has_zero_freq_{var}"] for var in range(1, number_of_variables + 1)]))
    return number_of_zero_freq_vars


def get_sum_one_freq(number_of_variables: int, model: cp_model.CpModel, all_vars: dict[str, cp_model.IntVar],
                     number_of_decimal_places: int) -> cp_model.IntVar:
    for var in range(1, number_of_variables + 1):
        help_var_one = model.NewBoolVar(f"var_has_one_freq_{var}")
        model.Add(all_vars[str(var) + "_freq"] == number_of_decimal_places).OnlyEnforceIf(help_var_one)
        model.Add(all_vars[str(var) + "_freq"] != number_of_decimal_places).OnlyEnforceIf(help_var_one.Not())
        all_vars[f"var_has_one_freq_{var}"] = help_var_one
    number_of_one_freq_vars = model.NewIntVar(0, number_of_variables, "number_of_one_freq_vars")
    model.Add(
        number_of_one_freq_vars == sum(
            [all_vars[f"var_has_one_freq_{var}"] for var in range(1, number_of_variables + 1)]))
    return number_of_one_freq_vars
