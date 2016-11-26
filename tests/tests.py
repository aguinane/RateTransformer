import unittest
from ratetransformer import rate
from ratetransformer import Transformer
import yaml


class TestRateTx(unittest.TestCase):
    """ Tests the rate transformer module gives the expected rating
    """

    def test_converged_values(self):
        """ Test the calculated rating for an example
        """
        examples = ['tests/example1.yaml']
        for example in examples:
            with open(example, newline='') as example_file:
                data = yaml.load(example_file)

            HeatRunData = data['HeatRun']
            ThermalChar = data['Thermal']

            tx = Transformer(HeatRunData, ThermalChar)

            AmbWHS = data['AmbWHS']
            AmbAgeing = data['AmbAgeing']
            LoadShape = data['LoadShape']
            Limits = data['Limits']

            tx.perform_rating(AmbWHS, AmbAgeing, LoadShape, Limits)

            Results = data['ExpectedResults']
            self.assertEqual(tx.MaxTOTemp, Results['MaxTOTemp'])
            self.assertEqual(tx.MaxWHSTemp, Results['MaxWHSTemp'])
            self.assertEqual(tx.Ageing, Results['Ageing'])
            self.assertEqual(tx.MaxLoad, Results['MaxLoad'])
            self.assertEqual(tx.CRF, Results['CRF'])
            self.assertEqual(tx.RatingReason, Results['RatingReason'])


class TestRatingFunctions(unittest.TestCase):
    """ Tests specific functions
    """

    def test_ageing_rate(self):
        self.assertAlmostEqual(rate.relative_ageing_rate(80), 0.125, places=3)
        self.assertAlmostEqual(rate.relative_ageing_rate(98), 1.0, places=1)
        self.assertAlmostEqual(rate.relative_ageing_rate(110), 4.0, places=1)
        self.assertAlmostEqual(rate.relative_ageing_rate(128), 32.0, places=1)
        self.assertAlmostEqual(rate.relative_ageing_rate(140), 128.0, places=1)

    def test_tauR(self):
        val = rate.thermal_time_constant_at_rated_load(7970.7582, 116140, 41.6)
        self.assertAlmostEqual(val, 171.3, places=1)

    def test_STTC(self):
        TauR, dTOr, dTOi, dTOu, n = (
            171.30198439, 41.6, 25.60, 20.2302035, 0.9)
        val = rate.thermal_time_constant_as_considered_load(
            TauR, dTOr, dTOi, dTOu, n)
        self.assertAlmostEqual(val, 164.77, places=2)

    def test_inst_top_oil(self):
        (dTOi, dTOult, t, k11, Tau) = (25.60, 20.2302034, 30, 0.5, 164.76996)
        val = rate.inst_top_oil_rise_at_load(dTOi, dTOult, t, k11, Tau)
        self.assertAlmostEqual(val, 23.96, places=2)

    def test_ult_top_oil(self):
        K, R, dTOr, x = 0.590068739, 10.25387597, 41.6, 0.8
        val = rate.ult_top_oil_rise_at_load(K, R, dTOr, x)
        self.assertAlmostEqual(val, 20.23, places=2)

    def test_thermal_capacity(self):
        C = rate.thermal_capacity(
            oil_volume=14000, mass_core=19325, mass_tank=10000, cooling_mode='ODAN')
        self.assertAlmostEqual(C, 11002, places=0)


class TestRecommendedCharacteristic(unittest.TestCase):
    """ Tests recommended characteristics match cooling method
    """

    def test_oil_constant(self):
        n = rate.recommended_oil_time_constant(cooling_mode='ONAN')
        self.assertEqual(n, 0.8)
        n = rate.recommended_oil_time_constant(cooling_mode='ONAF')
        self.assertEqual(n, 0.9)

    def test_oil_exponent(self):
        x = rate.recommended_oil_exponent(cooling_mode='ONAN')
        self.assertEqual(x, 0.8)
        x = rate.recommended_oil_exponent(cooling_mode='ODAF')
        self.assertEqual(x, 1.0)

    def test_winding_time_constant(self):
        TauW = rate.recommended_winding_time_constant(cooling_mode='ON')
        self.assertEqual(TauW, 10)
        TauW = rate.recommended_winding_time_constant(cooling_mode='ODAF')
        self.assertEqual(TauW, 7)

    def test_thermal_constants(self):
        k11, k21, k22 = rate.recommended_thermal_constants(cooling_mode='ONAN')
        self.assertEqual((k11, k21, k22), (0.5, 2.0, 2.0))
        k11, k21, k22 = rate.recommended_thermal_constants(cooling_mode='OF')
        self.assertEqual((k11, k21, k22), (1.0, 1.3, 1.0))


if __name__ == '__main__':
    unittest.main()
