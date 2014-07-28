#!/usr/bin/env python
#----------------------------------------------------

import unittest
import rate
from example import example_calculation

class TestRateTx(unittest.TestCase):
    """
    Tests the rate transformer module against known answers
    """
    def setUp(self):
        pass


    def test_basic(self):
        self.assertEqual(1, 1)


    def test_ageing_rate(self):
        self.assertEqual(rate.relative_ageing_rate(98.0), 1)
        self.assertEqual(rate.relative_ageing_rate(98), 1.0)
        self.assertAlmostEqual(rate.relative_ageing_rate(50), 0.00390625)
        self.assertAlmostEqual(rate.relative_ageing_rate(120), 12.69920841)
        self.assertAlmostEqual(rate.relative_ageing_rate(150), 406.37466930)


    def test_tauR(self):
        val = rate.thermal_time_constant_at_rated_load(7970.7582, 
            116140, 41.6)
        self.assertAlmostEqual(val, 171.30198439)

      
    def test_STTC(self):
        TauR, dTOr, dTOi, dTOu, n = (171.30198439, 41.6, 
            25.60, 20.2302035, 0.9)
        val = rate.thermal_time_constant_as_considered_load(TauR,
            dTOr, dTOi, dTOu, n)
        self.assertAlmostEqual(val,164.76996179)


    def test_inst_top_oil(self):
        (dTOi, dTOult, t, K, R, dTOr, x, k11, Tau) = (25.60, 
            20.2302034, 30, 0.59006874, 10.253876, 41.6, 0.8, 0.5, 164.76996)
        val = rate.inst_top_oil_rise_at_load(dTOi, 
            dTOult, t, K, R, dTOr, x, k11, Tau)
        self.assertAlmostEqual(val, 23.96109035)


    def test_ult_top_oil(self):
        K, R, dTOr, x = 0.590068739, 10.25387597, 41.6, 0.8
        val = rate.ult_top_oil_rise_at_load(K, R, dTOr, x)
        self.assertAlmostEqual(val, 20.23020347)


    def test_converged_values(self):
        (FinalReason, Max_Load, Max_TOtemp, Max_WHStemp, LoL, NumIter, 
            CRF) = example_calculation()
        self.assertEqual(Max_TOtemp, 71.61)
        self.assertEqual(Max_WHStemp, 94.87)
        self.assertEqual(LoL, 24.0)
        self.assertEqual(Max_Load, 28.925)
        self.assertEqual(CRF, 1.157)

if __name__ == '__main__':
    unittest.main()
