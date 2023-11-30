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
    for rule in cnf_int:
        for block in range(1, number_of_decimal_places + 1):
            model.AddBoolOr(
                [all_vars[str(var) + "." + str(block)] if var >= 0 else
                 all_vars[str(abs(var)) + "." + str(block)].Not() for var in rule])


def create_ebr_vars(number_of_variables: int, all_vars: dict[str, cp_model.IntVar], model: cp_model.CpModel,
                    number_of_decimal_places: int):
    for var in range(1, number_of_variables + 1):
        all_vars[str(var) + "_ebr"] = model.NewIntVar(0, number_of_decimal_places, str(var) + "_ebr")
        model.Add(all_vars[str(var) + "_ebr"] == sum(
            [all_vars[str(var) + "." + str(block)] for block in range(1, number_of_decimal_places + 1)]))


def set_zero_ebr(number_of_variables: int, model: cp_model.CpModel, all_vars: dict[str, cp_model.IntVar],
                 should_have_zero_ebr_vars: int):
    for var in range(1, number_of_variables + 1):
        help_var_zero = model.NewBoolVar(f"var_has_zero_ebr_{var}")
        model.Add(all_vars[str(var) + "_ebr"] == 0).OnlyEnforceIf(help_var_zero)
        model.Add(all_vars[str(var) + "_ebr"] > 0).OnlyEnforceIf(help_var_zero.Not())
        all_vars[f"var_has_zero_ebr_{var}"] = help_var_zero

    number_of_zero_ebr_vars = model.NewIntVar(0, number_of_variables, "number_of_zero_ebr_vars")
    model.Add(
        number_of_zero_ebr_vars == sum(
            [all_vars[f"var_has_zero_ebr_{var}"] for var in range(1, number_of_variables + 1)]))
    model.Add(number_of_zero_ebr_vars == should_have_zero_ebr_vars)


def set_one_ebr(number_of_variables: int, model: cp_model.CpModel, all_vars: dict[str, cp_model.IntVar],
                should_have_one_ebr_vars: int, number_of_decimal_places: int):
    for var in range(1, number_of_variables + 1):
        help_var_one = model.NewBoolVar(f"var_has_one_ebr_{var}")
        model.Add(all_vars[str(var) + "_ebr"] == number_of_decimal_places).OnlyEnforceIf(help_var_one)
        model.Add(all_vars[str(var) + "_ebr"] != number_of_decimal_places).OnlyEnforceIf(help_var_one.Not())
        all_vars[f"var_has_one_ebr_{var}"] = help_var_one
    number_of_one_ebr_vars = model.NewIntVar(0, number_of_variables, "number_of_one_ebr_vars")
    model.Add(
        number_of_one_ebr_vars == sum(
            [all_vars[f"var_has_one_ebr_{var}"] for var in range(1, number_of_variables + 1)]))
    model.Add(number_of_one_ebr_vars == should_have_one_ebr_vars)
