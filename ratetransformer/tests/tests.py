import unittest
from ratetransformer import rate
from ratetransformer import Transformer
import json

class TestRateTx(unittest.TestCase):
    """ Tests the rate transformer module gives the expected rating
    """

    def test_converged_values(self):
        with open('example1.json', newline='') as json_file:
            jsondata = json.load(json_file)

        HeatRunData = jsondata['HeatRun']
        ThermalChar = jsondata['Nameplate']

        tx = Transformer(HeatRunData, ThermalChar)

        TxSeasonal = jsondata['Seasonal']
        t = TxSeasonal['t']
        AmbWHS = TxSeasonal['AmbWHS']
        AmbAgeing = TxSeasonal['AmbAgeing']
        LoadShape = TxSeasonal['LoadShape']
        Limits = jsondata['Limits']

        tx.perform_rating(t, AmbWHS, AmbAgeing, LoadShape, Limits)

        self.assertEqual(tx.MaxTOTemp, 71.61)
        self.assertEqual(tx.MaxWHSTemp, 94.87)
        self.assertEqual(tx.Ageing, 24.0)
        self.assertEqual(tx.MaxLoad, 28.925)
        self.assertEqual(tx.CRF, 1.157)
        self.assertEqual(tx.RatingReason, 'Exceed allowed ageing of 24.0hrs/day')

class TestRatingFunctions(unittest.TestCase):
    """ Tests specific functions
    """

    def test_ageing_rate(self):
        self.assertEqual(rate.relative_ageing_rate(98.0), 1)
        self.assertEqual(rate.relative_ageing_rate(98), 1.0)
        self.assertAlmostEqual(rate.relative_ageing_rate(50), 0.0039, places=4)
        self.assertAlmostEqual(rate.relative_ageing_rate(120), 12.70, places=2)
        self.assertAlmostEqual(rate.relative_ageing_rate(150), 406.37, places=2)

    def test_tauR(self):
        val = rate.thermal_time_constant_at_rated_load(7970.7582, 116140, 41.6)
        self.assertAlmostEqual(val, 171.3, places=1)

    def test_STTC(self):
        TauR, dTOr, dTOi, dTOu, n = (171.30198439, 41.6, 25.60, 20.2302035, 0.9)
        val = rate.thermal_time_constant_as_considered_load(TauR, dTOr, dTOi, dTOu, n)
        self.assertAlmostEqual(val,164.77, places=2)

    def test_inst_top_oil(self):
        (dTOi, dTOult, t, K, R, dTOr, x, k11, Tau) = (25.60, 20.2302034, 30, 0.59006874, 10.253876, 41.6, 0.8, 0.5, 164.76996)
        val = rate.inst_top_oil_rise_at_load(dTOi, dTOult, t, K, R, dTOr, x, k11, Tau)
        self.assertAlmostEqual(val, 23.96, places=2)

    def test_ult_top_oil(self):
        K, R, dTOr, x = 0.590068739, 10.25387597, 41.6, 0.8
        val = rate.ult_top_oil_rise_at_load(K, R, dTOr, x)
        self.assertAlmostEqual(val, 20.23, places=2)


if __name__ == '__main__':
    unittest.main()
