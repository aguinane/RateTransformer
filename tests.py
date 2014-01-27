#!/usr/bin/env python
#----------------------------------------------------
__author__ = "A. Guinane"
__copyright__ = "Copyright 2014 A. Guinane"
__license__ = "MIT"
__version__ = "1.0.0"
#----------------------------------------------------

import unittest

from ratetransformer import relative_ageing_rate
from ratetransformer import thermal_time_constant_at_rated_load
from ratetransformer import thermal_time_constant_as_considered_load
from ratetransformer import inst_top_oil_rise_at_load
from ratetransformer import ult_top_oil_rise_at_load

class TestRateTx(unittest.TestCase):
    """
    Tests the rate transformer module against known answers
    """
    def setUp(self):
        pass

    def test_basic(self):
        self.assertEqual(1, 1)
        
    def test_ageing_rate(self):
        self.assertEqual(relative_ageing_rate(98.0), 1)
        self.assertEqual(relative_ageing_rate(98), 1.0)
        self.assertEqual(relative_ageing_rate(50), 0.00390625)
        self.assertEqual(relative_ageing_rate(120), 12.699208415745595)
        self.assertEqual(relative_ageing_rate(150), 406.3746693038589)

    def test_tauR(self):
        val = thermal_time_constant_at_rated_load(7970.7582,116140,41.6)
        self.assertEqual(val,171.30198439125195)
        
    def test_STTC(self):
        TauR, dTOr, dTOi, dTOu, n = 171.30198439125195, 41.6, 25.60, 20.23020349, 0.9
        val = thermal_time_constant_as_considered_load(TauR,dTOr,dTOi,dTOu, n)
        self.assertEqual(val,164.7699617941899)

    def test_inst_top_oil(self):
        dTOi, dTOult, t, K, R, dTOr, x, k11, Tau = 25.60, 20.23020349, 30, 0.590068739, 10.25387597, 41.6, 0.8, 0.5, 164.7699618
        val = inst_top_oil_rise_at_load(dTOi, dTOult, t, K, R, dTOr, x, k11, Tau)
        self.assertEqual(val,23.96109035675765)

    def test_ult_top_oil(self):
        K, R, dTOr, x = 0.590068739, 10.25387597, 41.6, 0.8
        val = ult_top_oil_rise_at_load(K, R, dTOr, x)
        self.assertEqual(val,20.23020347576246)
        

if __name__ == '__main__':
    unittest.main()
