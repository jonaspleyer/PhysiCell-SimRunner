#!/bin/python3

from src.SimController import Controller
from src.SamplerMethods import MonteCarlo_normal, Linear

def calculate_cell_number(x_min, x_max, y_min, y_max, z_min, z_max, dx, dy, dz, use_2D, space_seperation):
	'''Returns the number of cells in dependence on other parameters'''
	# Calculate number of voxels in x, y and z direction
	N_x = (x_max - x_min)/dx
	N_y = (y_max - y_min)/dy
	N_z = (z_max - z_min)/dz
	dim = (2 if use_2D == True else 3)
	N_tot = N_x*N_y*(1 if use_2D == True else N_z)
	N_cells = N_tot*(1-space_seperation)**dim
	return [int(round(N_cells,0))]


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
	Cont.add_sampler_method("Linear_method", Linear)
	Cont.add_sampler_method("MonteCarlo_normal", MonteCarlo_normal, init_info={"N_params":4})

	# First define some individual parameters
	Cont.add_variable_param(name="speed", param_type=float, node_structure=["cell_definitions", "cell_definition", "phenotype", "motility", "speed"], info={"bound_low":0.0, "bound_high":2.0}, method_name="MonteCarlo_normal")
	Cont.add_variable_param(name="pers_time", param_type=float, node_structure=["cell_definitions", "cell_definition", "phenotype", "motility", "persistence_time"], info={"bound_low":0.0, "bound_high":2.0}, method_name="MonteCarlo_normal")

	# Now an example for correlated parameters
	# These are just for information purposes and are not controlled actually
	Cont.add_static_param(name="x_min", param_type=float, node_structure=["domain", "x_min"])
	Cont.add_static_param(name="x_max", param_type=float, node_structure=["domain", "x_max"])
	Cont.add_static_param(name="y_min", param_type=float, node_structure=["domain", "y_min"])
	Cont.add_static_param(name="y_max", param_type=float, node_structure=["domain", "y_max"])
	Cont.add_static_param(name="z_min", param_type=float, node_structure=["domain", "z_min"])
	Cont.add_static_param(name="z_max", param_type=float, node_structure=["domain", "z_max"])
	Cont.add_static_param(name="dx", param_type=float, node_structure=["domain", "dx"])
	Cont.add_static_param(name="dy", param_type=float, node_structure=["domain", "dy"])
	Cont.add_static_param(name="dz", param_type=float, node_structure=["domain", "dz"])
	Cont.add_static_param(name="use_2D", param_type=bool, node_structure=["domain", "use_2D"])

	# This parameter is actually chosen
	Cont.add_variable_param(name="space_seperation", param_type=float, node_structure=["user_parameters", "space_seperation"], info={"bound_low":0.0, "bound_high":0.8, "increment":0.2}, method_name="Linear_method")
	
	# This parameter then depends on all other parameters given before
	Cont.add_correlated_param("number_of_cells", int, ["user_parameters", "number_of_cells"])

	# Now correlate the parameters via the previously defined function
	Cont.correlate_params(
		params_static=["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "dx", "dy", "dz", "use_2D"], 
		params_variable=["space_seperation"], 
		params_result=["number_of_cells"], 
		correlation_func=calculate_cell_number
	)

	# cont.generateOutputs()
	Cont.run()