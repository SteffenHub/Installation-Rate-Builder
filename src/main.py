import os
import random
from copy import deepcopy
from typing import Union

from ortools.sat.python import cp_model

from rule_builder import create_all_vars, add_all_rules_from_dimacs, create_freq_of_vars, get_sum_zero_freq, \
    get_sum_one_freq


def get_value_of(var: cp_model.IntVar, model: cp_model.CpModel) -> Union[None, int]:
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
        if stat is cp_model.INFEASIBLE:
            return None


def find_min_max_of_var(var: cp_model.IntVar, model: cp_model.CpModel) -> list[int]:
    model.Minimize(var)
    minimum = get_value_of(var, model)

    model.Maximize(var)
    maximum = get_value_of(var, model)
    return [minimum, maximum]


def handle_should_have_zero_one_freq(model: cp_model, number_of_variables: int, all_vars: dict[str, cp_model.IntVar],
                                     number_of_decimal_places: int):
    # first try input values in a copied model
    model_c = deepcopy(model)
    zero_freq = int(input("how many variables should have frequency 100.0%\n"))  # should have 0% frequency
    one_freq = int(input("how many variables should have frequency 0.0%\n"))  # should have 100% frequency

    # Add sum of all variables with frequency 100%/0% equals should_have value
    model_c.Add(get_sum_zero_freq(number_of_variables, model_c, all_vars) == zero_freq)
    model_c.Add(get_sum_one_freq(number_of_variables, model_c, all_vars, number_of_decimal_places) == one_freq)

    # tell the user what his mistake was
    if cp_model.CpSolver().Solve(model_c) not in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
        print(f"There's no solution with 0.0: {zero_freq} and 1.0: {one_freq}\n"
              f"I'm searching for possible values. This could take about a minute...")
        # first copy model and add should have value for 0% frequency, then look up min max value for 100% frequency
        model_zero_vars = deepcopy(model)
        model_zero_vars.Add(get_sum_zero_freq(number_of_variables, model_zero_vars, all_vars) == zero_freq)
        range_one_freq = find_min_max_of_var(
            get_sum_one_freq(number_of_variables, model_zero_vars, all_vars, number_of_decimal_places), model_zero_vars)
        if None in range_one_freq:
            print(f"0.0: {zero_freq} is not solvable")
        else:
            print(f"If you chose 0.0: {zero_freq}, than 1.0 is in range: {range_one_freq[0]}-{range_one_freq[1]}  "
                  f"values in this interval could also be non-selectable")

        # copy model and add should have value for 100% frequency, then look up min max value for 0% frequency
        model_one_vars = deepcopy(model)
        model_one_vars.Add(
            get_sum_one_freq(number_of_variables, model_one_vars, all_vars, number_of_decimal_places) == one_freq)
        range_zero_freq = find_min_max_of_var(get_sum_zero_freq(number_of_variables, model_one_vars, all_vars),
                                              model_one_vars)
        if None in range_zero_freq:
            print(f"1.0: {one_freq} is not solvable")
        else:
            print(f"If you chose 1.0: {one_freq}, than 0.0 is in range: {range_zero_freq[0]}-{range_zero_freq[1]}  "
                  f"Values in this interval could also be non-selectable")
        handle_should_have_zero_one_freq(model, number_of_variables, all_vars, number_of_decimal_places)
    else:  # If should_have values are consistent -> add them to model
        model.Add(get_sum_zero_freq(number_of_variables, model, all_vars) == zero_freq)
        model.Add(get_sum_one_freq(number_of_variables, model, all_vars, number_of_decimal_places) == one_freq)


def main():
    file_name = "cnfBuilder100VarsVariance517684924774.txt"
    dimacs_file: list[str] = [line.strip() for line in open(file_name)]

    cnf_int: list[list[int]] = [list(map(int, line.strip().split()))[:-1] for line in dimacs_file if
                                not (line.startswith('c') or line.startswith('p'))]

    number_of_variables: int = next(
        int(num_vars) for line in dimacs_file if line.startswith('p cnf') for _, _, num_vars, _ in [line.split()])

    number_of_decimal_places = 100

    model = cp_model.CpModel()

    # create all variables. for var 1, we create 1.1, 1.2, 1.3, ..., 1.number_of_decimal_places
    all_vars = create_all_vars(number_of_variables=number_of_variables,
                               number_of_decimal_places=number_of_decimal_places, model=model)

    # Add all rules from read rule file for each block
    add_all_rules_from_dimacs(cnf_int=cnf_int, number_of_decimal_places=number_of_decimal_places, model=model,
                              all_vars=all_vars)
    if cp_model.CpSolver().Solve(model) not in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
        print("Dimacs file is not solvable")
        return

    # Create the frequencies for all variables
    create_freq_of_vars(number_of_variables=number_of_variables, model=model, all_vars=all_vars,
                        number_of_decimal_places=number_of_decimal_places)

    handle_should_have_zero_one_freq(model, number_of_variables, all_vars, number_of_decimal_places)

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
        print(f"still missing {len(var_list)} variables")
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
