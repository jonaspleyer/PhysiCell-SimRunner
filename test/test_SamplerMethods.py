#!/bin/python

import unittest

from src.SamplerMethods import MonteCarlo_normal, Linear, Explicit

class testSamplerMethods(unittest.TestCase):

    def __init__(self):
        self.sampler_methods = [MonteCarlo_normal, Linear, Explicit]

    def test_add_param(self):
        pass

    def test_input_control(self):
        pass

    def test_generate_combinations(self):
        pass