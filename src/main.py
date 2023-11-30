import os
import random
from ortools.sat.python import cp_model

from Dimacs_Interface import dimacs_str_to_int_list, extract_counts_from_dimacs
from RuleBuilder import create_all_vars, add_all_rules_from_dimacs, create_freq_of_vars, set_zero_freq, set_one_freq


def get_value_of(var: cp_model.IntVar, model: cp_model.CpModel) -> int:
    solver_tmp = cp_model.CpSolver()
    stat = solver_tmp.Solve(model)
    if stat is cp_model.OPTIMAL:
        return solver_tmp.Value(var)
    else:
        if stat is cp_model.FEASIBLE:
            raise ValueError("Only Feasible")
        if stat is cp_model.UNKNOWN:
            raise ValueError("Unknown")
        if stat is cp_model.MODEL_INVALID:
            raise ValueError("Invalid model")
        raise ValueError("Unknown Error")


def find_min_max_of_var(var: cp_model.IntVar, model: cp_model.CpModel) -> list[int]:
    model.Minimize(var)
    minimum = get_value_of(var, model)

    model.Maximize(var)
    maximum = get_value_of(var, model)
    return [minimum, maximum]


def main():
    file_name = "cnfBuilder100VarsVariance517684924774.txt"
    dimacs_file: list[str] = [line.strip() for line in open(file_name)]

    cnf_int: list[list[int]] = dimacs_str_to_int_list(dimacs_file)

    counts = extract_counts_from_dimacs(dimacs_file)
    number_of_variables: int = counts[0]

    number_of_decimal_places = 100

    model = cp_model.CpModel()

    # create all variables. for var 1, we create 1.1, 1.2, 1.3, ..., 1.number_of_decimal_places
    all_vars = create_all_vars(number_of_variables=number_of_variables,
                               number_of_decimal_places=number_of_decimal_places, model=model)

    # Add all rules from read rule file for each block
    add_all_rules_from_dimacs(cnf_int=cnf_int, number_of_decimal_places=number_of_decimal_places, model=model,
                              all_vars=all_vars)

    # Create the frequencies for all variables
    create_freq_of_vars(number_of_variables=number_of_variables, model=model, all_vars=all_vars,
                        number_of_decimal_places=number_of_decimal_places)

    should_have_zero_freq_vars = int(0.0928 * number_of_variables)
    set_zero_freq(number_of_variables=number_of_variables, all_vars=all_vars, model=model,
                  should_have_zero_freq_vars=should_have_zero_freq_vars)

    should_have_one_freq_vars = int(0.0818 * number_of_variables)
    set_one_freq(number_of_variables=number_of_variables, all_vars=all_vars, model=model,
                 should_have_one_freq_vars=should_have_one_freq_vars, number_of_decimal_places=number_of_decimal_places)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        for var in range(1, number_of_variables + 1):
            print(str(var) + "_freq: " + str(solver.Value(all_vars[str(var) + "_freq"]) / number_of_decimal_places))
    else:
        if status == cp_model.FEASIBLE:
            raise ValueError("Only Feasible")
        raise ValueError("not solvable")

    print("\nThis was one possible solution.\n")

    var_list = list(range(1, number_of_variables + 1))
    while var_list:
        var = random.choice(var_list)
        var_list.remove(var)
        min_max = find_min_max_of_var(all_vars[str(var) + "_freq"], model)
        if min_max[0] == min_max[1]:
            print(
                "minimum and maximum for " + str(var) + " are equal: " + str(min_max[0] / number_of_decimal_places))
            continue
        print("possible frequency for " + str(var) + ": " + str(min_max[0] / number_of_decimal_places) + " - " + str(
            min_max[1] / number_of_decimal_places))
        random_frequency = random.randint(min_max[0], min_max[1])
        model.Add(all_vars[str(var) + "_freq"] == random_frequency)
        print("I've chosen: " + str(random_frequency))
        #
        # ebr_input = input("Enter the desired frequency: ")
        # ebr_input = float(ebr_input)
        # ebr_input = ebr_input * number_of_decimal_places
        # ebr_input = int(ebr_input)
        # model.Add(vars[str(var) + "_freq"] == ebr_input)

    # save result to file
    solver = cp_model.CpSolver()
    if (solver.Solve(model)) in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
        lines = [f"{solver.Value(all_vars[str(var) + '_freq']) / number_of_decimal_places}"
                 for var in range(1, number_of_variables + 1)]
        open(f"freq_result_{os.path.basename(file_name)}", 'w').write('\n'.join(lines))
    else:
        print("Solver found no solution. File was not saved")


main()
