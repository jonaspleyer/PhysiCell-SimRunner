#!/bin/python3

from src.SimController import Controller
from src.SamplerMethods import MonteCarlo_normal, Linear

if __name__ == "__main__":
	# Project_folder relative to main.py
	project_folder = "PhysiCellProject"
	# xml_file relative to project_folder
	xml_file = "config/PhysiCell_settings.xml"
	# binary_name should be in project_folder
	binary_name = "secretion_project"

	# Initialize the controller class
	Cont = Controller(project_folder, binary_name, xml_file, parallel_sims=3)

	# Define a method to sample parameters
	Cont.add_sampler_method("MonteCarlo_normal", MonteCarlo_normal, init_info={"N_params":4})

	# This parameter is just for information purposes and does not change
	Cont.add_variable_param(name="x_min", param_type=float, node_structure=["domain", "x_min"], info={"bound_low":-200.0, "bound_high":-20.0}, method_name="MonteCarlo_normal")

	# This parameter will be changed for different simulations by the MoncteCarlo_normal method
	Cont.add_static_param(name="x_max", param_type=float, node_structure=["domain", "x_max"])
	
	# Now an example for correlated parameters
	Cont.add_correlated_param("dx", int, ["domain", "dx"])

	# Define the function by which the parameters should be correlated
	# Note that the return statement is always a list
	def calculate_dx(x_max, x_min):
		N_voxels = 50
		dx = (x_max-x_min)/N_voxels
		return [int(round(dx,0))]

	# Now correlate the parameters via the previously defined function
	Cont.correlate_params(
		params_static=["x_max"], 
		params_variable=["x_min"], 
		params_result=["dx"], 
		correlation_func=calculate_dx
	)

	# cont.generateOutputs()
	Cont.run()