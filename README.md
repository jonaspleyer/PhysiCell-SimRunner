# PhysiCell-SimRunner
Short python program to explore parameter space for individually created Simulations.
Works by modifying the PhysiCell_settings.xml file, running the simulation and storing results.

# Features
* Explore Parameterspace by different sampling methods
 * Linearly
 * Monte-Carlo (normally distributed)
 * (see planned Features)
* Correlate Parameters via functions
* Parallel implementation allows running multiple simulations simultanously

# Planned Features
- [ ] Define variable parameters which are not represented in xml file but correlate with others (eg. number of voxels)
- [ ] Option to run post-simulation scripts to already analyze generated data
- [ ] Gauss sampling
- [ ] Binomial sampling
- [ ] Latin-Hypercube sampling
- [ ] Start/Stop/Continue Parameter Space exploration
- [ ] Write more tests and switch from flaky get/set tests for Parameter class to more solid ones.

# Limitations
* Only xml file configuration possible. Program should be written with necessary abstraction.

# Usage
1. Clone the repository via 

	`git clone https://github.com/jonaspleyer/PhysiCell-SimRunner`
2. Change folder to the cloned repository 

	`cd PhysiCell-SimRunner`
3. Now either copy or link and existing PhysiCell project folder to the Project folder.
	* Make sure that the binary file is in the project folder (ie: "PhysiCell-Project/compiled\_binary\_name")
	* Locate the xml config file ("config/PhysiCell\_settings.xml") and check that all parameters which are not planned to be modified by this script are entered correctly.
4. Rewrite main.py to include all paramters and correlations which should be explored.
	First define the project_folder, xml_file and binary_name
	```python
	# Project_folder relative to main.py
	project_folder = "PhysiCellProject"
	# xml_file relative to project_folder
	xml_file = "config/PhysiCell_settings.xml"
	# binary_name should be in project_folder
	binary_name = "project"
	# Initialize the controller class
	Cont = Controller(project_folder, binary_name, xml_file, parallel_sims=3)
	```
	The corresponding folder structure should look like this:
	```console
	├── main.py
	├── PhysiCellProject
	│   ├── binary_name
	│   └── config
	│       └── PhysiCell_settings.xml
	├── save_dir
	├── src
	├── test
	└── ...
	```
	Next, in `main.py` define which method should be used to sample parameters.
	```python
	Cont.add_sampler_method("MonteCarlo_normal", MonteCarlo_normal, init_info={"N_params":4})
	```
	Add parameters that are variable or static.
	```python
	Cont.add_variable_param(name="x_min", param_type=float, node_structure=["domain", "x_min"], info={"bound_low":-200.0, "bound_high":-20.0}, method_name="MonteCarlo_normal")
	Cont.add_static_param(name="x_max", param_type=float, node_structure=["domain", "x_max"])
	```
	If desired add corrlated parameters and correlated them via a function. Note that the order of parameters in the function and in the `Cont.correlate_params` statement needs to match. Also the type of the output needs to match the type specified when creating the parameters.
	```python
	Cont.add_correlated_param("dx", int, ["domain", "dx"])
	
	def calculate_dx(x_max, x_min):
		N_voxels = 50
		dx = (x_max-x_min)/N_voxels
		return [int(round(dx,0))]
	
	Cont.correlate_params(
		params_static=["x_max"], 
		params_variable=["x_min"], 
		params_result=["dx"], 
		correlation_func=calculate_dx
	)
	```
	Finally run the simulations.
	```python
	Cont.run()
	```
5. Now either start the program by running one of the following commands
	```console
	make
	python main.py
	```

# Links and Contact
[Website](https://www.fdm.uni-freiburg.de/Members/spatsysbio/Members/JonasPleyer)
[Mail](mailto:jonas.pleyer@fdm.uni-freiburg.de)
