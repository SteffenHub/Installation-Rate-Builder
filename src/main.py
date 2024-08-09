import os
import random
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Union

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import CpSolverSolutionCallback

from rule_builder import create_all_vars, add_all_rules_from_dimacs, create_freq_of_vars, get_sum_zero_freq, \
    get_sum_one_freq


def save_choice(file_path: Path, used_random_code: str = None, var: str = None, frequency: int = None, time_till_now=None):
    with file_path.open("a") as file:
        if used_random_code is not None:
            file.write(f"used random code : {used_random_code}\n")
        if time_till_now is not None:
            file.write(f"needed time : {time_till_now}\n")
        if frequency is not None:
            file.write(f"{var} : {frequency}\n")


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
            # TODO Do not return None but raise an error
            return None


def find_min_max_of_var(var: cp_model.IntVar, model: cp_model.CpModel) -> list[int]:
    print(f"look up minimum for variable {var.Name()}...")
    model.Minimize(var)
    minimum = get_value_of(var, model)

    print(f"look up maximum for variable {var.Name()}...")
    model.Maximize(var)
    maximum = get_value_of(var, model)
    return [minimum, maximum]


def handle_should_have_zero_one_freq(model: cp_model, number_of_variables: int, all_vars: dict[str, cp_model.IntVar],
                                     number_of_decimal_places: int) -> (int, int):
    # first try input values in a copied model
    model_c = deepcopy(model)
    # TODO print range you can choose from
    zero_freq = int(input("how many variables should have frequency 0.0%\n"))  # should have 0% frequency
    one_freq = int(input("how many variables should have frequency 100.0%\n"))  # should have 100% frequency

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
    print("")
    return zero_freq, one_freq


def ask_and_get_cnf_file() -> (str, int, list[list[int]]):
    file_name = input("Which cnf file should be used? \n insert filepath: ")

    dimacs_file: list[str] = [line.strip() for line in open(file_name)]
    print("found file:")
    [print(line) for line in dimacs_file]
    print("")

    cnf_int: list[list[int]] = [list(map(int, line.strip().split()))[:-1] for line in dimacs_file if
                                not (line.startswith('c') or line.startswith('p'))]

    number_of_variables: int = next(
        int(num_vars) for line in dimacs_file if line.startswith('p cnf') for _, _, num_vars, _ in [line.split()])
    return file_name, number_of_variables, cnf_int


def ask_and_get_seed() -> int:
    try:
        seed = input(
            "Insert seed for the random generator. example: 12345. Type None if a random seed should be used: ")
        if seed != "None":
            seed = int(seed)
        else:
            seed = random.randrange(sys.maxsize)
        return seed
    except Exception as e:
        print(e)
        print("Unknown input! Try again")
        return ask_and_get_seed()


class CustomSolutionPrinterFindOneSolution(CpSolverSolutionCallback):
    def __init__(self):
        CpSolverSolutionCallback.__init__(self)
        self.solution_count = 0

    def on_solution_callback(self) -> None:
        self.solution_count += 1
        if self.solution_count >= 1:
            self.StopSearch()


def is_feasible(model: cp_model.CpModel) -> bool:
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    return status in [cp_model.OPTIMAL, cp_model.FEASIBLE]


def main():
    file_name, number_of_variables, cnf_int = ask_and_get_cnf_file()

    seed = ask_and_get_seed()
    print(f"Use {seed} as seed \n")
    random.seed(seed)

    print("How many decimal places should take into account?")
    print("10 means 10% steps: 0.2 = 20%")
    print("100 means 1% steps: 0.12 = 12%")
    print("1000 means 0,1% steps: 0.342 = 34,2%")
    print("More decimal places takes more time: ")
    found = False
    while not found:
        try:
            number_of_decimal_places = int(input("How many decimal places should take into account?"))
            found = True
        except Exception as e:
            print("Unknown input! Try again")
    print("")

    model = cp_model.CpModel()

    # create all variables. for var 1, we create 1.1, 1.2, 1.3, ..., 1.number_of_decimal_places
    all_vars = create_all_vars(number_of_variables=number_of_variables,
                               number_of_decimal_places=number_of_decimal_places, model=model)

    # Add all rules from read rule file for each block
    add_all_rules_from_dimacs(cnf_int=cnf_int, number_of_decimal_places=number_of_decimal_places, model=model,
                              all_vars=all_vars)
    if cp_model.CpSolver().Solve(model) not in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
        raise ValueError("Dimacs file is not solvable")

    # Create the frequencies for all variables
    create_freq_of_vars(number_of_variables=number_of_variables, model=model, all_vars=all_vars,
                        number_of_decimal_places=number_of_decimal_places)

    zero_freq, one_freq = handle_should_have_zero_one_freq(model, number_of_variables, all_vars,
                                                           number_of_decimal_places)

    print("searching for a possible solution...")
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        for var in range(1, number_of_variables + 1):
            print(str(var) + "_freq: " + str(solver.Value(all_vars[str(var) + "_freq"]) / number_of_decimal_places))
    else:
        if status == cp_model.FEASIBLE:
            raise ValueError("Only Feasible")
        raise ValueError("not solvable")

    print("\nThis was one possible solution. Now we generate the frequencies with the random generator\n")

    var_list = list(range(1, number_of_variables + 1))
    file_name_only = file_name.rsplit('/', 1)[-1].split('.')[0]
    path_log_file = Path(
        f'log_files/log_choice_file_{file_name_only}_{one_freq}_{zero_freq}_{number_of_decimal_places}_{seed}.txt')
    path_log_file.parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(os.fspath(path_log_file)):
        print("Found log file with results!")
        content = path_log_file.read_text().splitlines()

        # check if last line is a used random code line
        if content[len(content)-1].startswith("used random code"):
            del content[len(content)-1]
            with path_log_file.open('w') as file:
                file.writelines('\n'.join(content))
                file.write("\n")
        content = path_log_file.read_text().splitlines()

        time_previous = 0
        used_random_times = 0
        for line in content:
            if (line.startswith("used cnf")
                    or line.startswith("100%")
                    or line.startswith("0%")
                    or line.startswith("used decimal places")
                    or line.startswith("used seed")):
                continue
            elif line.startswith("needed time"):
                time_previous = float(line.split(" : ")[1].split(" ")[0])
            elif line.startswith("used random code"):
                used_random_times = eval(line.split(" : ")[1])
            else:
                choice = line.split(" : ")
                model.Add(all_vars[choice[0] + "_freq"] == int(choice[1]))
                var_list.remove(int(choice[0]))
                print(f"Added frequency for var {choice[0]} = {choice[1]}")

    else:
        with path_log_file.open("a") as file:
            file.write(f"used cnf : {file_name}\n")
            file.write(f"100% vars : {one_freq}\n")
            file.write(f"0% vars : {zero_freq}\n")
            file.write(f"used decimal places : {number_of_decimal_places}\n")
            file.write(f"used seed : {seed}\n")
        time_previous = 0
        used_random_times = 0

    print("Before we start to set random frequencies for the variables, you can set some vars manually")
    while True:
        # TODO prevent wrong user input for example choose from range 0.3 - 0.5 but user choose 0.7
        print("")
        try:
            print("Type stop if you don't want to set variables anymore")
            input_var = input("Which variable you want to set: ")
            if input_var == "stop":
                print("Stopped manual set")
                break
            min_max = find_min_max_of_var(all_vars[input_var + "_freq"], model)
        except Exception as e:
            print("Unknown input! Try again")
            continue
        if min_max[0] == min_max[1]:
            print("minimum and maximum for " + input_var + " are equal: " + str(min_max[0] / number_of_decimal_places))
            save_choice(file_path=path_log_file, var=input_var, frequency=min_max[0], time_till_now=0, used_random_code=None)
            var_list.remove(int(input_var))
            continue
        print("possible frequency for " + input_var + ": " + str(min_max[0] / number_of_decimal_places) + " - " + str(
            min_max[1] / number_of_decimal_places))
        print("Which frequency should this variable have?")
        print("If you choose 10 for number of decimal places use 3 for 30% or 7 for 70%")
        print("If you choose 100 for number of decimal places use 30 for 30% or 73 for 73%")
        print("If you choose 1000 for number of decimal places use 300 for 30% or 732 for 73,2%")
        try:
            freq_for_input_var = input("Type in the frequency this variable should have: ")
            correct_input = input(
                f"frequency for {input_var} will be set to {int(freq_for_input_var) / number_of_decimal_places}. Is this correct? [True, False]")
        except Exception as e:
            print("Unknown input! Try again")
            continue
        if correct_input == "False":
            print("Try again")
            continue
        elif correct_input == "True":
            print(f"I will set frequency for {input_var} to {int(freq_for_input_var) / number_of_decimal_places}")
        else:
            print("Unknown input! Use True or False. Try again")
            continue
        model.Add(all_vars[input_var + "_freq"] == int(freq_for_input_var))
        save_choice(file_path=path_log_file, var=input_var, frequency=min_max[0], time_till_now=0, used_random_code=None)
        var_list.remove(int(input_var))
    print("start timer")
    start_time = time.time()
    start_time = start_time - time_previous

    while var_list:
        var = random.choice(var_list)
        used_random_times += 1
        save_choice(file_path=path_log_file, used_random_code=f"random.choice({var_list})")
        var_list.remove(var)
        min_max = find_min_max_of_var(all_vars[str(var) + "_freq"], model)
        if min_max[0] == min_max[1]:
            print("minimum and maximum for " + str(var) + " are equal: " + str(min_max[0] / number_of_decimal_places))
            print(f"still missing {len(var_list)} variables")
            save_choice(file_path=path_log_file, var=var, frequency=min_max[0], time_till_now=time.time() - start_time, used_random_code=None)
            continue
        print("possible frequency for " + str(var) + ": " + str(min_max[0] / number_of_decimal_places) + " - " + str(
            min_max[1] / number_of_decimal_places))

        found_feasible_frequency = False
        tried_frequencies = []
        while not found_feasible_frequency:
            random_frequency = random.randint(min_max[0], min_max[1])
            used_random_times += 1
            if random_frequency in tried_frequencies:
                continue
            print("I've chosen: " + str(random_frequency))
            # TODO use copy procedure from ortools instead of deepcopy model_copy.CopyFrom(model)
            # TODO to use copy needs to copy all variables or the needed ones
            # TODO model_copy.GetIntVarFromProtoIndex(variable.Index())
            model_copy = deepcopy(model)
            model_copy.Add(all_vars[str(var) + "_freq"] == random_frequency)
            if not is_feasible(model_copy):
                print(f"Model is not feasible with {random_frequency}! Try another frequency")
                tried_frequencies.append(random_frequency)
            else:
                found_feasible_frequency = True
                save_choice(file_path=path_log_file, var=var, frequency=random_frequency, time_till_now=time.time() - start_time, used_random_code=f"random.randint({min_max[0]}, {min_max[1]})")
                model.Add(all_vars[str(var) + "_freq"] == random_frequency)
        print(f"still missing {len(var_list)} variables")

    # save result to file
    solver = cp_model.CpSolver()
    if (solver.Solve(model)) in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
        lines = []
        lines.append(f"c used cnf: {file_name}")
        lines.append(f"c 100% vars: {one_freq}")
        lines.append(f"c 0% vars: {zero_freq}")
        lines.append(f"c used decimal places: {number_of_decimal_places}")
        lines.append(f"c used seed: {seed}")
        lines.append(f"c needed time: {time.time() - start_time} seconds")
        [lines.append(f"{solver.Value(all_vars[str(var) + '_freq']) / number_of_decimal_places}") for var in
         range(1, number_of_variables + 1)]
        filename = f"freq_result_{os.path.basename(file_name)}"
        open(filename, 'w').write('\n'.join(lines))
        print(f"Saved result as freq_result_{os.path.basename(file_name)}")
    else:
        print("Solver found no solution. File was not saved")


if __name__ == "__main__":
    main()
