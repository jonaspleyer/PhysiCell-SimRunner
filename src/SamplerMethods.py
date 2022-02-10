#!/bin/python

from abc import ABC, abstractmethod
from src.Parameter import Parameter
import numpy as np
import itertools
import random
import warnings


class SamplerMethod(ABC):
    def __init__(self):
        self.mandatory_param_info_keys = []
        self.mandatory_sampler_keys = []
        self.param_infos = []

    @abstractmethod
    def add_param(self, param_name:str, param:Parameter, info:dict):
        pass

    @abstractmethod
    def _test_input(self, param:Parameter, info:dict):
        pass

    @abstractmethod
    def generate_combinations(self) -> tuple[list, list]:
        pass


class MonteCarlo_normal(SamplerMethod):
    def __init__(self, N_params):
        self.mandatory_param_info_keys = ["bound_low", "bound_high"]
        self.param_infos = []
        self.N_params = N_params
        self.allowed_types = [int, float]
    

    def add_param(self, param_name:str, param:Parameter, info:dict):
        self._test_input(param, info)
        self.param_infos.append((param_name, param, info))
    

    def _test_input(self, param:Parameter, info:dict):
        if param.param_type == bool:
            raise TypeError("This sampler method does not support sampling booleans")
        if param.param_type not in self.allowed_types:
            raise TypeError("Parameter type " + str(param.param_type) + " currently not supported by this filter. Choose from " + ' '.join(self.allowed_types))
        for key in self.mandatory_param_info_keys:
            if not key in info.keys():
                raise KeyError
        if info["bound_low"] >= info["bound_high"]:
            raise ValueError("bound_high should be higher than bound_low")
    

    def generate_combinations(self):
        param_values = []
        param_names = []
        for i in range(self.N_params):
            param_comb = []
            for param_name, param, info in self.param_infos:
                if param.param_type == int:
                    param_comb.append(random.randint(info["bound_low"], info["bound_high"]))
                elif param.param_type == float:
                    param_comb.append(random.uniform(info["bound_low"], info["bound_high"]))
                else:
                    raise TypeError("type of parameter does not match types supported by the MonteCarlo sampler")
                if param_name not in param_names:
                    param_names.append(param_name)
            param_values.append(param_comb)
        return param_values, param_names


class Linear(SamplerMethod):
    def __init__(self):
        self.mandatory_param_info_keys = ["bound_low", "bound_high", "increment"]
        self.param_infos = []
    

    def add_param(self, param_name:str, param:Parameter, info:dict):
        self._test_input(param_name, param, info)
        self.param_infos.append((param_name, param, info))


    def _test_input(self, param_name:str, param:Parameter, info:dict):
        if param.param_type == bool:
            raise TypeError("This sampler method does not support sampling booleans")
        for key in self.mandatory_param_info_keys:
            if not key in info.keys():
                raise KeyError("Expected key " + str(key) + " in info dict.")
            if type(info[key]) != param.param_type:
                raise TypeError("Expected " + str(key) + " to be of type " + str(param.param_type) + " and not " + str(type(info[key])))
        if info["bound_low"] >= info["bound_high"]:
            raise ValueError("bound_high should be higher than bound_low")
        if info["increment"] > info["bound_high"] - info["bound_low"]:
            warnings.warn("increment of parameter " + str(param_name) + " was chosen to be larger than total range!")

    
    def generate_combinations(self):
        param_ranges = []
        param_names = []
        for param_name, param, info in self.param_infos:
            # TODO this is just a workaround to include upper limits of np.arange.
            # Defenitely need to find a better way!
            param_ranges.append(np.arange(info["bound_low"], info["bound_high"]+info["increment"]/1e+20, info["increment"]))
            param_names.append(param_name)
        return list(itertools.product(*param_ranges)), param_names
    

class Explicit(SamplerMethod):
    def __init__(self):
        self.mandatory_param_info_keys = ["values"]