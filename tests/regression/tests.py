# Tests for "hikecalc"
#
# EXAMPLES: (do after activating venv, in sandbox/hikecalc/)
#  python -m unittest tests.regression.tests
#
#  python -m unittest -v tests.regression.tests      # VERBOSE
#
##############################################################################
# Python library
from contextlib import contextmanager
import unittest
from unittest import skip
import datetime
import os
import logging
import sys
# External Packages
# Local Packages

class HCTest(unittest.TestCase):

    maxDiff = None  # to see full values in DIFF on assert failure
    # assert_equal.__self__.maxDiff = None


    @classmethod
    def setUpClass(cls):
        DATA='~/sandbox/hikecalc/data/catalina.dat'

    @classmethod
    def tearDownClass(cls):
        pass

    def test_hc_0(self):
        pass
