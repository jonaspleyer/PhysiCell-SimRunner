#!/bin/python3

import unittest
import random
import string
import xml.etree.ElementTree as ET


from src.Parameter import Parameter
# from SimController import Controller, Parameter

class testGet(unittest.TestCase):
	
	def test_get_float(self):
		'''Reads different floats from test_get_float.xml with different reference formats and compares output.'''
		node_structures_and_values = [
			(["microenvironment_setup", "variable", "physical_parameter_set", "diffusion_coefficient"], float(100.0)),
			(["microenvironment_setup", "variable", "initial_condition"], float(1e-5)),
			(["microenvironment_setup", "variable", "Dirichlet_boundary_condition"], float(5.230498e+29)),
			(["microenvironment_setup", {"node":"variable", "index":1}, "physical_parameter_set", "diffusion_coefficient"], float(0.33)),
			(["microenvironment_setup", {"node":"variable", "index":1}, "physical_parameter_set", "decay_rate"], float(5123.0)),
			(["microenvironment_setup", {"node":"variable", "index":1, "attributes":{"name":"prey signal", "units":"dimensionless"}}, "initial_condition"], float(1.9999e+5)),
			(["microenvironment_setup", {"node":"variable", "attributes":{"name":"prey signal", "units":"dimensionless"}}, "Dirichlet_boundary_condition"], float(0.000001)),
			([{"node":"cell_definitions"}, {"node":"cell_definition", "index":1}, "phenotype", {"node":"cycle", "attributes":{"code":"5"}}, "phase_transition_rates", "rate"], float(0.003)),
			([{"node":"cell_definitions", "index":0}, {"node":"cell_definition", "index":1}, "phenotype", {"node":"cycle", "attributes":{"code":"5"}}, "phase_transition_rates", "rate"], float(0.003))
		]
		# TODO add more tests. Especiall tests that are supposed to fail. For example if multiple nodes are present with the same name.

		for node_structure, val in node_structures_and_values:
			param = Parameter(param_type=float, xml_file="test/xml_files/test_get_float.xml", node_structure=node_structure)
			self.assertEqual(val, param.get_val())


	def test_get_int(self):
		'''Write random int to a xml file and check if same values are retrieved.'''
		file = open("test/xml_files/test_get_int.xml", "w")
		file.write("<root>\n")
		values = []
		for i in range(100):
			r = random.randrange(0, 2147483647)
			values.append(r)
			file.write("\t<int_test_" + str(i) + ">" + str(r) + "</int_test_" + str(i) + ">\n")
		file.write("</root>\n")
		file.close()

		for i, val in enumerate(values):
			param = Parameter(param_type=int, xml_file="test/xml_files/test_get_int.xml", node_structure=["int_test_" + str(i)])
			self.assertEqual(val, param.get_val())


	def test_get_str(self):
		'''Write random string to a xml file and check if same values are retrieved.'''
		file = open("test/xml_files/test_get_str.xml", "w")
		file.write("<root>\n")
		values = []
		for i in range(100):
			r = ''.join(random.choices(string.ascii_letters + string.digits, k=i+1))
			values.append(r)
			file.write("\t<str_test_" + str(i) + ">" + r + "</str_test_" + str(i) + ">\n")
		file.write("</root>\n")
		file.close()

		for i, val in enumerate(values):
			param = Parameter(param_type=str, xml_file="test/xml_files/test_get_str.xml", node_structure=["str_test_" + str(i)])
			self.assertEqual(val, param.get_val())


	def nonotest_get_bool(self):
		'''Write True and False booleans to a xml file and check if same values are retrieved.'''
		file = open("test/xml_files/test_get_bool.xml", "w")
		file.write("<root>\n")
		
		values1 = [True, False, "true", "false", "TRUE", "FALSE", "1", "0"]
		values2 = [''.join(random.choices(string.ascii_letters + string.digits, k=j+1)) for j in range(50)]
		values2 = [v2 for v2 in values2 if v2 not in values1]

		results1 = [True, False, True, False, True, False, True, False]
		results2 = [False for j in range(len(values2))]
	
		for i, val in enumerate(values1 + values2):
			file.write("\t<bool_test_" + str(i) + ">" + str(val) + "</bool_test_" + str(i) + ">\n")
		file.write("</root>")
		file.close()

		for i, val1 in enumerate(values1):
			param = Parameter(param_type=bool, xml_file="test/xml_files/test_get_bool.xml", node_structure=["bool_test_" + str(i)])
			self.assertEqual(results1[i], param.get_val())
		
		for i, val2 in enumerate(values2):
			with self.assertRaises(ValueError):
				param = Parameter(param_type=bool, xml_file="test/xml_files/test_get_bool.xml", node_structure=["bool_test_" + str(i+len(values1))])


class testSet(unittest.TestCase):

	def test_set_float(self):
		'''Set random floats in xml file, parse xml and compare.'''
		filename = "test/xml_files/test_set_float.xml"
		file = open(filename, "w")
		file.write("<root>\n")
		values = []
		for i in range(100):
			r = random.uniform(0, 1)*10**random.uniform(-30, 30)
			values.append(r)
			file.write("\t<float_test_" + str(i) + ">" + str(r) + "</float_test_" + str(i) + ">\n")
		file.write("</root>\n")
		file.close()

		for i, val in enumerate(values):
			node_name = "float_test_" + str(i)
			param = Parameter(param_type=float, xml_file=filename, node_structure=[node_name])
			param.set_val(val)
			node_text = ET.parse(filename).find(node_name).text
			self.assertEqual(str(val), node_text)


	def test_set_int(self):
		'''Set random ints in xml file, parse xml and compare.'''
		filename = "test/xml_files/test_set_int.xml"
		file = open(filename, "w")
		file.write("<root>\n")
		values = []
		for i in range(100):
			r = random.randrange(0, 2147483647)
			values.append(r)
			file.write("\t<int_test_" + str(i) + ">" + str(r) + "</int_test_" + str(i) + ">\n")
		file.write("</root>\n")
		file.close()

		for i, val in enumerate(values):
			node_name = "int_test_" + str(i)
			param = Parameter(param_type=int, xml_file="test/xml_files/test_set_int.xml", node_structure=[node_name])
			param.set_val(val)
			node_text = ET.parse(filename).find(node_name).text
			self.assertEqual(str(val), node_text)


	def test_set_str(self):
		'''Set random strings in xml file, parse xml and compare.'''
		filename = "test/xml_files/test_set_str.xml"
		file = open(filename, "w")
		file.write("<root>\n")
		values = []
		for i in range(100):
			r = ''.join(random.choices(string.ascii_letters + string.digits, k=i+1))
			values.append(r)
			file.write("\t<str_test_" + str(i) + ">" + str(r) + "</str_test_" + str(i) + ">\n")
		file.write("</root>\n")
		file.close()

		for i, val in enumerate(values):
			node_name = "str_test_" + str(i)
			param = Parameter(param_type=str, xml_file="test/xml_files/test_set_str.xml", node_structure=[node_name])
			param.set_val(val)
			node_text = ET.parse(filename).find(node_name).text
			self.assertEqual(str(val), node_text)

			
	def test_set_bool(self):
		'''Set random bools in xml file, parse xml and compare.'''
		filename = "test/xml_files/test_set_bool.xml"
		file = open(filename, "w")
		file.write("<root>\n")
		values = [True, False]
		results = ["True", "False"]
		for i, val in enumerate(values):
			file.write("\t<bool_test_" + str(i) + ">" + str(val) + "</bool_test_" + str(i) + ">\n")
		file.write("</root>\n")
		file.close()

		for i, val in enumerate(values):
			node_name = "bool_test_" + str(i)
			param = Parameter(param_type=bool, xml_file="test/xml_files/test_set_bool.xml", node_structure=[node_name])
			param.set_val(val)
			node_text = ET.parse(filename).find(node_name).text
			self.assertEqual(str(val), node_text)


class testNodeStructure(unittest.TestCase):

	def nono_test_nodeStructure(self):
		'''Creates different xml files with random types and introduces arbitrary errors in xml file.'''
		# This generates a pretty random xml file for every type multiple times
		typs = [float, int, str, bool]
		count = 0
		for typ in typs:
			for i in range(20):
				# Contents are randomized
				N_nodes = random.randrange(1, 100)
				Depth_nodes = [random.randrange(1,10) for k in range(N_nodes)]
				filename = "test/xml_files/test_nodeStructure.xml"
				file = open(filename, "w")
				file.write("<root>\n")
				for j in range(N_nodes):
					node_structure = [''.join(random.choices(string.ascii_letters, k=random.randrange(1, 20))) for m in range(Depth_nodes[j])]
					for k, node_name in enumerate(node_structure):
						file.write("\t"*(k+1) + "<" + node_name + ">" + "\n"*(k!=len(node_structure)-1))
					value = None
					if typ == int:
						value = random.randrange(0, 2147483647)
					if typ == float:
						value = random.uniform(0, 1)*10**random.uniform(-30, 30)	
					if typ == str:
						value = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randrange(0, 100)))
					if typ == bool:
						value = random.randrange(0,1) == 1
					file.write(str(value))
					node_structure.reverse()
					for k, node_name in enumerate(node_structure):
						file.write("\t"*(len(node_structure)-k)*(k!=0) + "</" + node_name + ">" + "\n")
					node_structure.reverse()
				file.write("</root>")
				file.close()
				
				# Now pick some random characters and delete them and test if results still match
				file = open(filename, "r")
				chars = list(file.read())
				index = random.randrange(1,2*len(chars))
				
				if 0<index<len(chars):
					del chars[::index]
				file.close()
				file = open(filename, "w")
				file.write(''.join(chars))
				file.close()
				
				# See if results do match
				try:
					param = Parameter(param_type=typ, xml_file=filename, node_structure=node_structure)
					succ1 = True
				except:
					succ1 = False
				try:
					node_text = ET.parse(filename)
					succ2 = True
				except:
					succ2 = False
				self.assertEqual(succ1, succ2)

class testUpdateFileLocations(unittest.TestCase):

	def test_update_file_locations(self):
		typs = [float, int, str, bool]



if __name__ == "__main__":
	unittest.main()