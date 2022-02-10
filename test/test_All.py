#!/bin/python3

import unittest


# Import tests for SimController
from test.test_Parameter import testGet, testSet, testNodeStructure, testUpdateFileLocations
from test.test_SimController import SimController

# Test all parts in main function
if __name__ == "__main__":
    # Run unit tests for the SimController module
    suite_Parameter = unittest.TestSuite()
    suite_Parameter.addTest(testGet)
    suite_Parameter.addTest(testSet)
    suite_Parameter.addTest(testNodeStructure)
    suite_Parameter.addTest(testUpdateFileLocations)

    suite_SimController = unittest.TestSuite()
    suite_SimController.addTest(SimController)

    unittest.TextTestRunner(suite_Parameter)
    unittest.TextTestRunner(suite_SimController)