#!/bin/python3
import os
import itertools
import numpy as np
from tqdm import tqdm
import types
import shutil
import multiprocessing as mp

# Import custom modules
from src.Parameter import Parameter
from src.SamplerMethods import MonteCarlo_normal, Linear, SamplerMethod


# TODO add functionality to compare if a simulation was already run by comparing the xml config files.
# If so still write output directory but refer to that simulation instead

# TODO Copy total folder into new working subfolders and then move output to parent output summaries
# Also clear subfolder afterwards
# Make sure to only copy non-output files

class Controller():
	def __init__(self, project_folder:str, project_binary_name:str, xml_file:str, **kwargs):
		# Only read these parameters
		self._params_static = {}
		# Change and write these parameters
		self._params_variable = {}
		# Parameters obtained by correlation with others
		self._params_correlated = {}
		# How do we calculate these correlations?
		# A single entry looks like this:
		# [params_static, params_variable, params_result, correlation_func]
		# where the first three items in the list are lists of strings referencing parameters
		# and the correlation_func defines how to calculate params_result. Very similar to:
		# params_result = correlation_func(*params_static, *params_variable)
		self._correlation_info = []

		# Stores all possible Methods to sample parameters
		# These methods also store their respective parameters
		self._sampler_methods = {}

		# Where is the project and its definition xml saved
		# TODO at beginning read xml file and then never again to avoid conflicts
		# modify parameter class to then alter memory-stored xml_file contents
		self._project_folder = project_folder.strip("./ ")
		self._xml_file_name = xml_file.strip("./ ")
		self._xml_file = self._project_folder + "/" + xml_file.strip("./ ")
		# To come back after single simulations are done in the subdirs
		self._base_dir = os.getcwd()

		# Which project binary should be executed
		self._project_binary_name = project_binary_name.strip("./ ")
		self._project_binary_path = self._project_folder + "/" + project_binary_name.strip("./ ")
		
		# Store the parameters to distribute to different simulation runs
		self._all_parameter_combinations = []
		self._all_parameter_descr = []

		self._parse_args(**kwargs)


	def _parse_args(self, **kwargs):
		# How many threads should be used to concurrently run simulations
		if "parallel_sims" in kwargs.keys():
			parallel_sims = kwargs["parallel_sims"]
			if parallel_sims<=0:
				raise ValueError("parallel_sims variable needs to be positive")
			parallel_sims = kwargs["parallel_sims"]
			if type(parallel_sims) == int and parallel_sims > 0:
				self.threads = parallel_sims
			else:
				raise ValueError("parallel_sims needs to be positive integer.")
		else:
			self.threads = 1
		# The directory to put saved results
		if "save_dir" in kwargs.keys():
			self.save_dir = kwargs["save_dir"]
		else:
			self.save_dir = "./save_dir"
		
		# Stores the post simulation command and tells the controller if it needs to be executed
		self._post_sim_script_command = None


	def add_sampler_method(self, name:str, method:SamplerMethod, init_info:dict={}):
		if name in self._sampler_methods.keys():
			raise KeyError("Sampler method with name " + str(name) + " is already present.")
		elif isinstance(method, SamplerMethod):
			if init_info != {}:
				raise ValueError("init_info dict was nonempty but instance of class was given instead of class definition. Either leave init_info empty or provide SamplerClass definition in function.")
			self._sampler_methods[name] = method
		else:
			m = method(**init_info)
			self._sampler_methods[name] = m

	
	def _check_param_present(self, name:str, param_type:type, node_structure:list, info:dict=None, method_name:str=None, logfile:str=None):
		if method_name !=None and not method_name in self._sampler_methods.keys():
			raise KeyError("Please add a sampler method with the name " + str(method_name) + " before adding parameters to it.")
		if name in self._params_variable.keys() or name in self._params_static.keys() or name in self._params_correlated.keys():
			raise NameError("parameter with name " + str(name) + " was alreayd specified")


	def add_variable_param(self, name:str, param_type:type, node_structure:list, info:dict, method_name:str, logfile:str=None):
		'''Adds a parameter with given values to iterate over in simulation.'''
		param = Parameter(param_type=param_type, xml_file=self._xml_file, node_structure=node_structure, logfile=logfile)
		self._check_param_present(name, param_type, node_structure, info, method_name, logfile)
		samplerMethod = self._sampler_methods[method_name]
		samplerMethod.add_param(param_name=name, param=param, info=info)
		self._params_variable[name] = param


	def add_static_param(self, name:str, param_type:type, node_structure:list, logfile:str=None):
		'''Adds a parameter only used for information purposes and not controlled by a sampler method.'''
		param = Parameter(param_type=param_type, xml_file=self._xml_file, node_structure=node_structure, logfile=logfile)
		if not self._check_param_present(name, param_type, node_structure, info=None, logfile=logfile):
			self._params_static[name] = param
	

	def add_correlated_param(self, name:str, param_type:type, node_structure:list, logfile:str=None):
		'''Adds a parameter which will be correlated and thus obtain its value by calculation from other (stativ/variable) parameters.'''
		param = Parameter(param_type=param_type, xml_file=self._xml_file, node_structure=node_structure, logfile=logfile)
		if not self._check_param_present(name, param_type, node_structure, info=None):
			self._params_correlated[name] = param


	def correlate_params(self, params_static:list, params_variable:list, params_result:list, correlation_func:types.FunctionType):
		'''
		Adds parameters that are correlated by a function.
		params_static:		List of static parameters names [parameter_name_static_1, parameter_name_static_2, ... ] which are only read.
		params_variable: 	List of variable parameter names [parameter_name_variable_1, parameter_name_variable_2, ... ] which are controlled
		params_result:		List of parameters that are calculated and depend on params_static, params_variable via correlation_func
					Format: [Parameter_res1, Parameter_res2, ...]
		correlation_func:	Function that takes as input parameters_static and parameters_variable and outputs params_result
					correlation_func(params_static:list, params_variable:list) -> list:
		'''
		for param_name in params_static:
			if not param_name in self._params_static:
				raise KeyError("parameter needs to be defined before referencing it in correlation funciton")
		for param_name in params_variable:
			if not param_name in self._params_variable:
				raise KeyError("parameter needs to be defined before referencing it in correlation funciton")
		for param_name in params_result:
			if not param_name in self._params_correlated:
				raise KeyError("parameter needs to be defined before referencing it in correlation funciton")
		for param_name in params_result:
			for corr_info in self._correlation_info:
				if param_name in corr_info[2]:
					raise NameError("parameter " + str(param_name) + " was already correlated with variable parameters " + str(corr_info[1]) + " and static parameters " + str(corr_info[0]))
		self._test_correlation_func(params_static, params_variable, params_result, correlation_func)
		self._correlation_info.append([params_static, params_variable, params_result, correlation_func])


	def _test_correlation_func(self, params_static:list, params_variable:list, params_result:list, correlation_func:types.FunctionType):
		'''Ensures that the supplied function will output the correct format to match the specified correlated parameters.'''
		params_static_values = [self._params_static[name].get_val() for name in params_static]
		params_variable_values = [self._params_variable[name].get_val() for name in params_variable]
		params_result_types = [self._params_correlated[name].param_type for name in params_result]
		try:
			res = correlation_func(*params_static_values, *params_variable_values)
		except:
			raise KeyError("correlation function for static parameters " + str(params_static) + " and variable parameters " + str(params_variable) + " has not the correct format.")
		if not [type(r) for r in res] == params_result_types:
			raise TypeError("correlation funciton for static parameters " + str(params_static) + " and variable parameters " + str(params_variable) + " does not calculate correct parameter types" + str(params_result_types))


	def _generate_parameters(self):
		'''
		This invokes the different sampler methods and generates parameter
		configurations based on their sampling methods.
		'''
		# Stores the "range" of parameters
		# Ie: [[0.0, 0.1, ... , 0.7], [0.3,0.5],[-3,1,5]]
		# where [0.0, 0.1, ... , 0.7] corresponds to the picked
		# values for one particular parameter
		combined_parameter_values_list = []
		# Will store all generated parameter pairs
		combs = []
		# Also store description for each parameter
		descr = []
		# Iterate over sampler methods and let them choose parameters
		for s_m_name in self._sampler_methods.keys():
			values, param_names = self._sampler_methods[s_m_name].generate_combinations()
			# Append the generated parameter values to the list (and description)
			combined_parameter_values_list.append(values)
			descr.append(param_names)
		# Create the cartesian product and flatten it (see _flatten method)
		combs = list(itertools.product(*combined_parameter_values_list))
		# Store results
		self._all_parameter_combinations = [list(self._flatten(c)) for c in combs]
		self._all_parameter_descr = list(self._flatten(descr))
		self._generate_correlated_params()


	def _flatten(self, L):
		'''
		Used to flatten generated parameter pairs if multiple sampler methods are involved.
		Ie. go from [(1,2,3),((4),5), (6)] -> [1,2,3,4,5,6].
		'''
		for l in L:
			if isinstance(l, list) or isinstance(l, tuple):
				yield from self._flatten(l)
			else:
				yield l


	def _generate_correlated_params(self):
		'''
		Part of the parameter generation routine that calculates the determined
		correlated parameters and adds them to the parameter list.
		This does not increase the total amount of combinations.
		'''
		# Append the correlated parameters for every parameter combination which was sampled so far.
		for i in range(len(self._all_parameter_combinations)):
			# Those sampled entries are seperated by the methods that sampled them
			for params_static, params_variable, params_result, correlation_func in self._correlation_info:
				if not set(params_result) <= set(self._all_parameter_descr):
					self._all_parameter_descr += params_result
				res = self._eval_correlation_func(params_static, params_variable, i, correlation_func)
				self._all_parameter_combinations[i]+=res


	def _eval_correlation_func(self, params_static:list, params_variable:list, param_index:int, correlation_func) -> list:
		'''
		Used to calculate the correlation function in the process to determine
		the correlated parameters in the parameter generation routine.
		'''
		params_static_values = [self._params_static[p].get_val() for p in params_static]
		params_variable_values = [param_val for i, param_val in enumerate(self._all_parameter_combinations[param_index]) if self._all_parameter_descr[i] in params_variable]
		res = correlation_func(*params_static_values, *params_variable_values)
		return res
	

	def _create_file_folder_structure(self, param_comb:tuple, save_dir:str, xml_file_name:str, xml_file:str, project_binary_name:str, project_binary_path:str, params:list, params_variable_correlated:list, post_sim_info):
		'''
		Creates the subdirectory \"run_XXXXXXXXXX\" and \"output\", "\config\" and \"logs\"
		folders in the subdirectory and copies relevant files to the new subdirectory.
		'''
		save_subdir = save_dir + "/run_" + '{:0>10}'.format(folder_count.value)
		while os.path.isdir(save_subdir):
			folder_count.value += 1
			save_subdir = save_dir + "/run_" + '{:0>10}'.format(folder_count.value)
		
		# Create filestructure
		os.mkdir(save_subdir)
		os.mkdir(save_subdir + "/output")
		os.mkdir(save_subdir + "/config")
		os.mkdir(save_subdir + "/logs")

		# Copy relevant files
		shutil.copy(xml_file, save_subdir + "/" + xml_file_name)
		shutil.copy(project_binary_path, save_subdir + "/" + project_binary_name)
		if post_sim_info != None:
			for file_name in post_sim_info["files"]:
				shutil.copy(post_sim_info["folder"] + "/" + file_name, save_subdir + "/" + file_name)
		
		return save_subdir


	def _write_xml(self, comb:tuple, xml_file_name:str, params:list, params_variable_correlated:list):
		'''
		Write the supplied parameter combination to the xml file.
		'''
		# Update the xml file and logfile in the parameters
		for i, param in enumerate(params):
			param.update_file_locations(xml_file=xml_file_name, logfile="logs/param_logs.txt")
			# Now write params to file
			param.set_val(param.param_type(comb[i]))


	def _run_sim(self, project_binary_name:str):
		'''
		Actually run the simulation and store the output of the binary in a logfile.
		'''
		# Create the logfile
		log = open("logs/log_sim.txt", "a")
		log.close()
		# Run the simulation and store output in logfile
		os.system("./" + project_binary_name + " > logs/log_sim.txt")
		

	def add_post_sim_script(self, script_command:str, script_file_names:list, script_folder="./user_scripts"):
		'''Defines a script to be executed when having finished the simulation.
		The command to run the script can be any string executed in a terminal.
		The command is to be run as in the base folder of the PhysiCell project.
		The list of files does have to include every file necesary to run the script.
		Example:
			script_command = "python generate_plots.py"
			script_file_names = ["generate_plots.py", "plotter.py", "info_getter.py"]
		'''
		# First check that all files are actually there
		for file_name in script_file_names:
			if not os.path.isfile(script_folder + "/" + file_name):
				raise NameError("post simulation script " + self._post_sim_script_command + " could not be found.")
		# Not store information
		self._post_sim_script_command = script_command
		self._post_sim_script_files = script_file_names
		self._post_sim_script_folder = script_folder

	
	def _run_single_sim(self, task:dict):
		'''
		1. Create file structure + copy files to it
		2. Write the supplied parameter combination to the xml file.
		3. Run the simulation and store output
		(4.) If a post simulation script was specified, run it.
		'''
		# Create new subdir and change to it
		save_subdir = self._create_file_folder_structure(**task)
		os.chdir(save_subdir)
		# Now write all necessary files and run the simulation
		self._write_xml(comb=task["param_comb"], xml_file_name=task["xml_file_name"], params=task["params"], params_variable_correlated=task["params_variable_correlated"])
		self._run_sim(task["project_binary_name"])
		
		# Run the post simulation script before going back to the main folder
		if task["post_sim_info"] != None:
			os.system(task["post_sim_info"]["command"])
		# Now go back to the main folder
		os.chdir(self._base_dir)
		return 1


	def run(self, output_dir="./output/"):
		'''
		
		'''
		self._generate_parameters()
		
		# Create list with all tasks (= Parameter combinations + information)
		tasks = []
		for comb in self._all_parameter_combinations:
			qarams = []
			qarams_variable_correlated = []
			
			# Create a list with all parameters in it. We have to check if parameters are variable or correlated
			for param_name in self._all_parameter_descr:
				if param_name in self._params_variable.keys():
					param = self._params_variable[param_name]
				elif param_name in self._params_correlated.keys():
					param = self._params_correlated[param_name]
				qaram = param.__copy__()
				qarams.append(qaram)
			
			# Check if a post simulation command was supplied and if so append its information to the task dictionary.
			if self._post_sim_script_command != None:
				post_sim_info = {"command":self._post_sim_script_command, "files":self._post_sim_script_files, "folder":self._post_sim_script_folder}
			else:
				post_sim_info = None
			
			# Create a task entry with all information
			tasks.append({
				"param_comb":comb, 
				"save_dir":self.save_dir, 
				"xml_file_name":self._xml_file_name, 
				"xml_file":self._xml_file, 
				"project_binary_name":self._project_binary_name, 
				"project_binary_path":self._project_binary_path, 
				"params":qarams, 
				"params_variable_correlated":qarams_variable_correlated,
				"post_sim_info":post_sim_info
			})
		# Set the shared counter for folder name to 0
		folder_count = mp.Value('i', 0)

		# Make sure that the counter is given to all subprocesses
		def init(arg):
			global folder_count
			folder_count = arg

		# Create pool (with multiple processes)
		pool = mp.Pool(max(1,self.threads), initializer=init, initargs = (folder_count, ))

		# Execute tasks
		with pool as p:
			r = list(tqdm(p.imap(self._run_single_sim, tasks), total=len(tasks)))