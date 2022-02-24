#!/bin/python

import xml.etree.ElementTree as ET
import warnings
import os
from pathlib import Path

# TODO add a option to have a parameter not be represented in the xml file
# Example: number of voxels:
# N_vox = int((x_max-x_min)/dx)+1
# N_vox is in [10, 20, 30, 40, 50]
# so we want to have N_vox variable but 
# but we do not have and do not want to represent N_vox in the xml file.
# Thus we need a workaround.

# Parameter class to get and set attributes in xml file
class Parameter():
	def __init__(self, param_type:type, xml_file:Path, node_structure:list, logfile:Path=None):
		self.param_type = param_type
		supported_types = [int, float, str, bool]
		if not param_type in supported_types:
			raise TypeError("Parameter type "  + str(param_type) + " currently not supported. Chose from " + " ".join(str(supported_types)))
		
		self.xml_file = xml_file
		self.logfile = logfile
		self.node_structure = node_structure
		self.node = self._locate_node_in_xml(xml_file=xml_file, node_structure=node_structure, logfile=logfile)


	def _update_tree(self):
		self.node = self._locate_node_in_xml(self.xml_file, self.node_structure)

	def _load_node_structure(self, xml_file:Path):
		'''Tests if the xml file has obvious errors and loads the tree if valid.'''
		try:
			self.tree = ET.parse(xml_file)
		except:
			raise ValueError("xml filename or file structure not valid")
		return self.tree


	def _locate_node_from_attributes(self, node_name:str, nodes_found, attributes:dict):
		'''Function returns the node in xml file given that we search by attributes.'''
		count_match_complete = 0
		count_match_partial = 0
		nodes_matching = []
		for n in nodes_found:
			if attributes.items() == n.attrib.items():
				count_match_complete += 1
				nodes_matching.append(n)
			elif attributes.items() <= n.attrib.items():
				count_match_partial += 1
				nodes_matching.append(n)
		if count_match_complete > 1:
			raise KeyError("attributes dict " + str(attributes) + " found " + str(count_match_partial) + " candidates matching. Reevaluate attributes or xml structure.")
		if count_match_partial > 1:
			warnings.warn("Supplied attributes dict only partially matching. First matching candidate was chosen Compare xml contents with parameter initialization to be sure that correct variable was selected or introduce less/more attributes to distinguish.")
		if len(nodes_matching) == 0:
			raise ValueError("node_name \"" + str(node_name) + "\" or attributes dict " + str(attributes) + "\" invalid. No matching nodes found.")
		return nodes_matching[0]


	def _getNode_entry_info(self, entry):
		'''Given an entry in the node_structure list, we extract node_name, index and attributes.
		Returns None for individual values if not present.'''
		# Test if entry is a dict. If so we need to extract the node_name, index and attributes to match
		node_name = None
		index = None
		attributes = None
		if type(entry) == dict:
			if "node" in entry.keys():
				node_name = entry["node"]
			else:
				raise KeyError("expected key \"node\" in node information dict: " + str(entry))
			if "index" in entry.keys():
				index = entry["index"]
			else:
				index = None
			if "attributes" in entry.keys():
				attributes = entry["attributes"]
			else:
				attributes = None
		# If not then simply assume that the given string is the node with index=0
		elif type(entry) == str:
			node_name = entry
			index = None
			attributes = {}
		else:
			raise ValueError("Expected node entry to be string or dict, not " + str(type(entry)))
		return node_name, index, attributes


	def _locate_node_in_xml(self, xml_file:str, node_structure:list, logfile:str=None):
		'''Locates node in xml file. The node structure can consist of a simple string 
		(will use first node matching) or a dictionary specifying index or attributes 
		if multiple nodes with identical tags are present.'''
		if logfile == None:
			logfile = open(os.devnull, "a")
		else:
			logfile = open(logfile, "a")
		print("[node-search] Locating node for parameter of type " + str(self.param_type) + " and node_structure [" + ' -> '.join([str(n) for n in node_structure]) + "]", file=logfile)
		node = self._load_node_structure(xml_file=xml_file)
		for entry in node_structure:
			node_name, index, attributes = self._getNode_entry_info(entry)

			# Now try to locate node from information obtained above
			nodes = node.findall(node_name)
			# Print to logfile if specified
			for n in nodes:
				print("[node-search] Found Tags: ", n.tag, file=logfile)
				print("[node-search] Node Name:  ", node_name, file=logfile)
				print("[node-search] Index:      ", index, file=logfile)
				print("[node-search] Attributes: ", attributes, file=logfile)
				print("[node-search] Node Attr:  ", n.attrib, file=logfile)
			# First test if we find any nodes at all
			if len(nodes) == 0:
				raise ValueError("node_name \"" + str(node_name) + "\" invalid. No matching nodes found.")
			# Check if we have a index supplied and if so use it first
			elif index != None:
				if type(index) == int and index >= 0 and index <len(nodes):
					node = nodes[index]
				elif attributes!=None:
					node = self._locate_node_from_attributes(node_name, nodes, attributes)
					warnings.warn("Index " + str(index) + " not valid. Used attributes " + str(attributes) + " to locate node!")
				else:
					raise IndexError("specified index " + str(index) + " for node " + str(node_name) + " not valid")
			elif attributes != {} and attributes != None:
				node = self._locate_node_from_attributes(node_name, nodes, attributes)
			elif len(nodes)==1:
				node = nodes[0]
			elif len(nodes) > 1:
				node = nodes[0]
				warnings.warn("No index or attribute dict supplied. Automatically chose entry 0 of " + str(len(nodes)) + " total entries.")
			print("[node-search] Selected node ", node.tag, node.attrib, file=logfile)
		print("", file=logfile)
		logfile.close()
		return node


	def set_val(self, value) -> None:
		'''Sets the value of the parameter in the xml file.'''
		if not type(value) == self.param_type:
			raise TypeError("Supplied value type does not match type definition.")
		self._update_tree()
		self.node.text = str(value)
		self.tree.write(self.xml_file)
		if self.logfile != None:
			logfile = open(self.logfile, "a")
			print("[param_set] Set parameter of type " + str(self.param_type) + " with node structure " + str(self.node_structure) + " in xml_file \"" + str(self.xml_file) + "\" to " + str(value), file=logfile)
			logfile.close()


	def get_val(self):
		'''Gets the value of the parameter in the xml file.'''
		if self.param_type != bool:
			return self.param_type(self.node.text)
		# This has to be inserted since bool("False")=True in python
		else:
			self._update_tree()
			s = self.node.text.strip(" ")
			if s == "True" or s == "true" or s == "TRUE" or s == "1":
				return True
			elif s == "False" or s == "false" or s == "FALSE" or s == "0":
				return False
			else:
				raise ValueError("could not identify if input " + str(s) + " is True of False")


	def update_file_locations(self, xml_file:Path, logfile:Path=None):
		self.xml_file = xml_file
		# if not logfile == None:
		self.logfile = logfile
		
		self._load_node_structure(xml_file)
		self.node = self._locate_node_in_xml(xml_file=xml_file, node_structure=self.node_structure, logfile=logfile)
	

	def __copy__(self):
		return Parameter(param_type=self.param_type, xml_file=self.xml_file, node_structure=self.node_structure, logfile=self.logfile)