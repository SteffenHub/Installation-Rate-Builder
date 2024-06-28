# Installation Rate Builder

The installation rate builder can generate consistent installation rates with a CNF as a data basis.

The Google OR-Tools CP-Solver ([Homepage](https://developers.google.com/optimization), [Repository](https://github.com/google/or-tools)) was used to find valid models of the CNF.

Input CNF's can be found in the data directory. The CNF's are generated with [CNF-Generator](https://github.com/SteffenHub/CNF-Generator).  
The output installation rates of the CNF files can be found in the output directory

## What is an Installation Rate?

Installation rates refer to the frequency or percentage with which specific configurable options of a product are selected by users.
These rates provide insight into user preferences and can help in optimizing product offerings, inventory management, and marketing strategies.

For instance, consider a configurable product like a smartphone that comes with various options such as different storage capacities,
colors, and RAM capacities. Installation rates would describe how often each of these options is chosen by users. For example:
- 1: 64 GB storage: 40%
- 2: 128 GB storage: 35%
- 3: 256 GB storage: 25%
- 4: Black color: 100%
- 5: 8GB RAM: 60%
- 6: 16GB RAM: 40%

These percentages indicate the popularity of each configuration option among users.

Behind these installation rates, there is a Conjunctive Normal Form (CNF) representation.
The individual choice options, such as storage capacities, form a family, which is represented as XOR in the CNF.
For example a Family of 1, 2 and 3, the storage configuration forms a family with rule:
> (1 XOR 2 XOR 3)  

In the conjunctive normal form, this is written as:
> ((1 ∨ 2 ∨ 3) ∧ (!1 ∨ !2) ∧ (!1 ∨ !3) ∧ (!2 ∨ !3))
 
For the Phone example the CNF can look like:
> p cnf 6 8  
> c Family for storage  
> 1 2 3 0  
> -1 -2 0  
> -1 -3 0  
> -2 -3 0  
> c Family for color  
> 4 0  
> c Family for accessories  
> 5 6 0  
> -5 -6 0  
> c 64GB Storage is not available with 16 GB RAM(1 -> !6)  
> -1 -6 0

Syntax hints:  
p cnf number_of_variables number_of_rules  
A line beginning with c introduces a comment

In this simple example the installation rate builder have to consider at least the rules:
- The sum of installation rates of a family is 100%
- The installation rate of 5(8GB RAM) is greater or equals 1(64 GB Storage)

The installation rate builder can assist you creating consistent installation rates or create random consistent assignments.


## How to Use

After run the Program you get into a Dialog:

> Which cnf file should be used?  
>  insert filepath:
> > ../data/Phone_example.cnf
> 
> found file:  
> p cnf 6 8  
> c Family for storage  
> 1 2 3 0  
> -1 -2 0  
> -1 -3 0  
> -2 -3 0  
> c Family for color  
> 4 0  
> c Family for accessories  
> 5 6 0  
> -5 -6 0  
> c 64GB Storage is not available with 16 GB RAM(1 -> !6)  
> -1 -6 0  
>
> Insert seed for the random generator. example: 12345. Type None if a random seed should be used:
> > None
> 
> Use 8467335337672211825 as seed 
> 
> How many decimal places should take into account?  
> 10 means 10% steps: 0.2 = 20%  
> 100 means 1% steps: 0.12 = 12%  
> 1000 means 0,1% steps: 0.342 = 34,2%  
> More decimal places takes more time:  
> How many decimal places should take into account?  
> > 10
> 
> how many variables should have frequency 0.0%
> > 0 
> 
> how many variables should have frequency 100.0%
> > 1
> 
> searching for a possible solution...  
> 1_freq: 0.2  
> 2_freq: 0.5  
> 3_freq: 0.3  
> 4_freq: 1.0  
> 5_freq: 0.3  
> 6_freq: 0.7  
>
> This was one possible solution. Now we generate the frequencies with the random generator
>
> Before we start to set random frequencies for the variables, you can set some vars manually
>
> Type stop if you don't want to set variables anymore
> Which variable you want to set: 
> > 1
> 
> look up minimum for variable...  
> look up maximum for variable...  
> possible frequency for 1: 0.1 - 0.8  
> Which frequency should this variable have?  
> If you choose 10 for number of decimal places use 3 for 30% or 7 for 70%  
> If you choose 100 for number of decimal places use 30 for 30% or 73 for 73%  
> If you choose 1000 for number of decimal places use 300 for 30% or 732 for 73,2%  
> Type in the frequency this variable should have:   
> > 4
> 
> frequency for 1 will be set to 0.4. Is this correct? [True, False]
> > True
> 
> I will set frequency for 1 to 0.4
>
> Type stop if you don't want to set variables anymore
> Which variable you want to set: 
> > stop
> 
> Stopped manual set  
> start timer  
> look up minimum for variable...  
> look up maximum for variable...  
> possible frequency for 3: 0.1 - 0.5  
> I've chosen: 4  
> still missing 4 variables  
> look up minimum for variable...  
> look up maximum for variable...  
> minimum and maximum for 4 are equal: 1.0  
> look up minimum for variable...  
> look up maximum for variable...  
> possible frequency for 6: 0.1 - 0.6  
> I've chosen: 3  
> still missing 2 variables  
> look up minimum for variable...  
> look up maximum for variable...  
> minimum and maximum for 2 are equal: 0.2  
> look up minimum for variable...  
> look up maximum for variable...  
> minimum and maximum for 5 are equal: 0.7  
> Saved result as freq_result_Phone_example.cnf  
 
The result file after the Dialog and calculation:
> c used cnf: ../data/Phone_example.cnf  
> c 100% vars: 1  
> c 0% vars: 0  
> c used decimal places: 10  
> c used seed: 8467335337672211825  
> c needed time: 0.17912697792053223 seconds  
> 0.4  
> 0.2  
> 0.4  
> 1.0  
> 0.7  
> 0.3  

The input cnf file can be found in the data directory and the result file in the output directory.  
When setting variable 1, you may have noticed that the minimum frequency is 10% and the maximum 80%, but
could be 0% to 100%.  
We set that 0 variables should have an installation rate of 0%.
Therefore, the maximum installation rate we can set for variable 1 is 80%, because the variables 2 and 3 are in the same 
family and can't be 0%.
And that the variable 1 cannot be 0% is because we set that no variable can have 0%.
We have set that we move in 10% steps. 
If you want smaller steps, such as 1% steps, then answer the question of 'How many decimal places should take into account?' with 100.
# Run the Code

To run the Code you have to install google ortools
```sh
pip install ortools
```
Alternatively, you can install the package with
```sh
pip install -r requirements.txt
```
