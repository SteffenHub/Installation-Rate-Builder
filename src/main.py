import os
import random
from ortools.sat.python import cp_model

from Dimacs_Interface import dimacs_str_to_int_list, extract_counts_from_dimacs
from RuleBuilder import create_all_vars, add_all_rules_from_dimacs, create_ebr_vars, set_zero_ebr, set_one_ebr
from txt_interface import read_txt_file, save_model_to_dir


def find_min_max_of_var(var: cp_model.IntVar, model: cp_model.CpModel) -> list[int]:
    solver_tmp = cp_model.CpSolver()
    model.Minimize(var)
    stat = solver_tmp.Solve(model)
    if stat is cp_model.OPTIMAL:
        minimum = solver_tmp.Value(var)
    else:
        if stat is cp_model.FEASIBLE:
            raise ValueError("Nur Feasible beim Minimize")
        raise ValueError("nicht loesbar bei suche von min und max")

    model.Maximize(var)
    stat = solver_tmp.Solve(model)
    if stat is cp_model.OPTIMAL:
        maximum = solver_tmp.Value(var)
    else:
        if stat is cp_model.FEASIBLE:
            raise ValueError("Nur Feasible beim Maximize")
        raise ValueError("nicht loesbar bei suche von min und max")
    return [minimum, maximum]


def main():
    datei_name = "cnfBuilder100VarsVariance517684924774.txt"
    dimacs_file: list[str] = read_txt_file(datei_name)

    cnf_int: list[list[int]] = dimacs_str_to_int_list(dimacs_file)

    counts = extract_counts_from_dimacs(dimacs_file)
    number_of_variables: int = counts[0]
    number_of_Clauses: int = counts[1]

    number_of_decimal_places = 100

    model = cp_model.CpModel()

    # create all variables. for var 1, we create 1.1, 1.2, 1.3, ..., 1.number_of_decimal_places
    all_vars = create_all_vars(number_of_variables=number_of_variables,
                               number_of_decimal_places=number_of_decimal_places, model=model)

    # Add all rules from read rule file for each block
    add_all_rules_from_dimacs(cnf_int=cnf_int, number_of_decimal_places=number_of_decimal_places, model=model,
                              all_vars=all_vars)

    # Create the Ebr Variables
    create_ebr_vars(number_of_variables=number_of_variables, model=model, all_vars=all_vars,
                    number_of_decimal_places=number_of_decimal_places)

    should_have_zero_ebr_vars = int(0.0928 * number_of_variables)
    set_zero_ebr(number_of_variables=number_of_variables, all_vars=all_vars, model=model,
                 should_have_zero_ebr_vars=should_have_zero_ebr_vars)

    should_have_one_ebr_vars = int(0.0818 * number_of_variables)
    set_one_ebr(number_of_variables=number_of_variables, all_vars=all_vars, model=model,
                should_have_one_ebr_vars=should_have_one_ebr_vars, number_of_decimal_places=number_of_decimal_places)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        for var in range(1, number_of_variables + 1):
            print(str(var) + "_ebr: " + str(solver.Value(all_vars[str(var) + "_ebr"]) / number_of_decimal_places))
            print(solver.Value(all_vars[str(var) + "_ebr"]))
    else:
        if status == cp_model.FEASIBLE:
            raise ValueError("Nur Feasible")
        raise ValueError("nicht loesbar")

    var_list = list(range(1, number_of_variables + 1))
    while var_list:
        var = random.choice(var_list)
        var_list.remove(var)
        min_max = find_min_max_of_var(all_vars[str(var) + "_ebr"], model)
        if min_max[0] == min_max[1]:
            print(
                "minimum und maximum fuer " + str(var) + " sind gleich: " + str(min_max[0] / number_of_decimal_places))
            continue
        print("moegliche einbaurate fuer " + str(var) + ": " + str(min_max[0] / number_of_decimal_places) + " - " + str(
            min_max[1] / number_of_decimal_places))
        zufalls_ebr = random.randint(min_max[0], min_max[1])
        model.Add(all_vars[str(var) + "_ebr"] == zufalls_ebr)
        print("Ich habe: " + str(zufalls_ebr) + " gewaehlt")
        #
        # ebr_input = input("Gebe die gewünschte ebr ein: ")
        # ebr_input = float(ebr_input)
        # ebr_input = ebr_input * number_of_decimal_places
        # ebr_input = int(ebr_input)
        # model.Add(vars[str(var) + "_ebr"] == ebr_input)

    save_model_to_dir(model, f"ebr_result_{os.path.basename(datei_name)}.txt", number_of_variables,
                      number_of_decimal_places, all_vars)


main()
