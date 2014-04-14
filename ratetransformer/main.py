#!/usr/bin/env python
#----------------------------------------------------

import math
import rate

def main():
    """
    This code is run if this module is called independantly and is intended as a demo
    Normally this module should be used by calling the perform_rating() function with transformer details passed to function
    """
    
    FinalReason, Max_Load, Max_TOtemp, Max_WHStemp, LoL, NumIter, CRF = example_calculation()

    print 'Results of example transformer calculation....'
    print '-' * 20
    print '# of Iterations: ' + str(NumIter)
    print 'Reason for rating: ' + FinalReason
    print 'Peak Load: ' + str(Max_Load)
    print 'Top Oil Temp: ' + str(Max_TOtemp)
    print 'WHS Temp: ' + str(Max_WHStemp)
    print 'CRF: ' + str(CRF)
    print 'Ageing: ' + str(LoL)

    
def example_calculation():
    """
    Provides some dummy data to demonstrate how to call the rating function
    """

    TxLimits = {}
    TxLimits['MaxLoadPU'] = 1.5                 # Max load above nameplate rating
    TxLimits['MaxLoadPU_Reason'] = '1.5pu'
    TxLimits['HotSpot'] = 120.0                 # Maximum Winding Hotspot Temperature
    TxLimits['HotSpot_Reason'] = 'WHS Temp'
    TxLimits['TopOil'] = 105.0                  # Maximum Top Oil Temperature
    TxLimits['TopOil_Reason'] = 'Top Oil Temp'
    TxLimits['LoL'] = 24.0                      # Maximum ageing (hrs/day)
    TxLimits['LoL_Reason'] = 'Ageing'

    TxHeatRun = {}
    TxHeatRun['TestId'] = '1'                   # Record number of heat run test
    TxHeatRun['Cooling'] = 'ONAN'               # Transformer cooling method
    TxHeatRun['RatedLoad'] = 25.0               # HV Nameplate Rating
    TxHeatRun['dTOr'] = 35.4                    # Top Oil Rise
    TxHeatRun['gr'] = 14.8                      # HV Winding Gradient
    TxHeatRun['H'] = 1.3                        # Winding Hotspot Factor
    TxHeatRun['P'] = 202220.0                   # Total Loss (W)
    TxHeatRun['R'] = 23.305                     # Load / No-Load Ratio

    TxDetails = {}
    TxDetails['CoolingType'] = 'ONAN'           # Transformer cooling method
    TxDetails['n'] = 0.8                        # Oil exponent as per IEEE C57.91-2011 Table 4
    TxDetails['x'] = 1.0                        # Oil exponent as per AS 60077.7-2013 Table 5
    TxDetails['y'] = 1.3                        # Winding exponent as per AS 60077.7-2013 Table 5
    TxDetails['k11'] = 0.5                      # Constant as per AS 60077.7-2013 Table 5
    TxDetails['k21'] = 2.0                      # Constant as per AS 60077.7-2013 Table 5
    TxDetails['k22'] = 2.0                      # Constant as per AS 60077.7-2013 Table 5
    TxDetails['TauW'] = 7.0                     # Winding Time Constant as per AS 60077.7-2013 Table 5
    TxDetails['TauO'] = 90.0                    # Oil Time Constant as per AS 60077.7-2013 Table 5
    TxDetails['C'] = 10507.3                    # Thermal capacity of transformer (used to calculate more accurate oil time constant)

    TxSeasonal = {}
    TxSeasonal['t'] = 30.0                      # Time interval (mins)
    TxSeasonal['LoadShape'] = [1.0] * 48        # List of load at each interval (eg. 24 hours with flat profile)
    TxSeasonal['AmbWHS'] = 24.72                # The monthly average temperature of the hottest month is used for the maximum hot-spot temp. calculation
    TxSeasonal['AmbAgeing'] = 27.85             # The yearly weighted ambient temperature is used for thermal ageing calculation

    FinalReason, Max_Load, Max_TOtemp, Max_WHStemp, LoL, NumIter, CRF = rate.perform_rating(
        TxHeatRun, TxLimits, TxDetails, TxSeasonal)

    return FinalReason, Max_Load, Max_TOtemp, Max_WHStemp, LoL, NumIter, CRF

if __name__ == '__main__':
    main()

