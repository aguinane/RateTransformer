#!/usr/bin/env python
#----------------------------------------------------
__author__ = "A. Guinane"
__copyright__ = "Copyright 2014 A. Guinane"
__license__ = "MIT"
__version__ = "1.0.0"
#----------------------------------------------------

import math

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

    """
    Output should like like this:
    Reason for rating: Ageing
    Peak Load: 28.925
    Top Oil Temp: 71.61
    WHS Temp: 94.87
    CRF: 1.157
    Ageing: 24.0
    """
    

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

    FinalReason, Max_Load, Max_TOtemp, Max_WHStemp, LoL, NumIter, CRF = perform_rating(TxHeatRun, TxLimits, TxDetails, TxSeasonal)

    return FinalReason, Max_Load, Max_TOtemp, Max_WHStemp, LoL, NumIter, CRF


def perform_rating(TxHeatRun, TxLimits, TxDetails, TxSeasonal):
    """
    Perform rating on a single transformer for specified rating limits
    """

    # Do some error checking first
    try:
        if TxHeatRun['RatedLoad'] == 0 or TxHeatRun['dTOr'] == 0 or TxHeatRun['gr'] == 0 or TxHeatRun['R'] == 0:
            # Heat run record doesn't exist or isn't populated
            RecordExists = False
        else:
            # Heat run record exists - calculate optimal loading
            RecordExists = True
    except KeyError:
        #Values aren't populated
        RecordExists = False

    if RecordExists == True:
        FinalReason, Max_Load, Max_TOtemp, Max_WHStemp, LoL, NumIter = calculate_transformer_rating(TxDetails, TxLimits, TxHeatRun, TxSeasonal)
        CRF = float(Max_Load) / float(TxHeatRun['RatedLoad'])
        CRF = round(CRF, 4)
    else:       
        FinalReason = 'Nameplate - no test data'
        Max_Load = float(TxHeatRun['RatedLoad']); CRF = 1.0
        Max_TOtemp = 0.0; Max_WHStemp = 0.0; LoL = 0.0; NumIter = 0

    return FinalReason, Max_Load, Max_TOtemp, Max_WHStemp, LoL, NumIter, CRF


def calculate_transformer_rating(ThermalChar, Limits, HeatRunData, TxSeasonal):
    """
    Calulates the optimum load conditions for specified limits
    """

    #Extract Input Information
    AmbWHS = TxSeasonal['AmbWHS']
    AmbAgeing = TxSeasonal['AmbAgeing']
    t = TxSeasonal['t']
    LoadShape = TxSeasonal['LoadShape']
    
    #Define some intial values
    NumIter = 0
    Limit = False
    PrevPeak = 0.0001
    InputList = t, HeatRunData, ThermalChar, Limits, AmbWHS, AmbAgeing, LoadShape

    #Calculate the starting scaling
    RatedLoad = HeatRunData['RatedLoad']
    MaxLoad = max(LoadShape)
    IncrementFactor = (float(RatedLoad) / float(MaxLoad)) #Start by incrementing by double max load
    ScaleFactor = IncrementFactor * 0.5 #Start with initial load at half the current load profile

    if IncrementFactor < 0.5:
        IncrementFactor = 0.5 #Start at half way

    if ScaleFactor < 0.2:
        ScaleFactor = 0.2 #Start reasonably high
    
    
    FinalReason = 'Did not converge' # Stops errors later if it didn't converge
    
    #Loop until scaling factor is sufficiently small (to yield more accurate results)
    for i in range(150): #Stop after certain num of iterations if not converged
               
        #Loop until limit is reached
        while Limit == False:
            Limit, Reason, Max_Load, Max_TOtemp, Max_WHStemp, L = CalculateLimit(ScaleFactor, InputList)
            NumIter += 1
            ScaleFactor += IncrementFactor
            FinalReason = Reason #Otherwise it will be lost when we move back an iteration
            
            #Export results of iterations - for debugging
            #print str(Limit) + ' - ' + str(Max_Load) + ' - ' + Reason
        
        #Step back to where limit wasn't reached to get optimal rating
        ScaleFactor = ScaleFactor - (2 * IncrementFactor)
        #Check scale factor isn't negative
        if ScaleFactor < 0:
            ScaleFactor = 0
        Limit, Reason, Max_Load, Max_TOtemp, Max_WHStemp, L = CalculateLimit(ScaleFactor, InputList)    

        #Decrese the amount scaled for next iteration run
        IncrementFactor = (IncrementFactor / 2)

        #Round values to appropriate significant figures
        Max_Load = round(Max_Load, 3)
        Max_TOtemp = round(Max_TOtemp, 2)
        Max_WHStemp = round(Max_WHStemp, 2)
        LoL = round(L, 3)

        #Check if converged early
        if IncrementFactor < 0.00001: #Check scaling factor is sufficiently small
            if PrevPeak == Max_Load:  #Check results of iteration hasn't changed
                #print 'Coverged after ' + str(i)
                break # Exit loop
        PrevPeak = Max_Load
    

    return FinalReason, Max_Load, Max_TOtemp, Max_WHStemp, LoL, NumIter


def CalculateLimit(ScaleFactor, InputList):
    """
    Scales load and checks whether limit will be breached
    """
    t, HeatRunData, ThermalChar, Limits, AmbWHS, AmbAgeing, LoadShape = InputList
    TempLoadShape = [i * ScaleFactor for i in LoadShape]

    #Initial Temperatures as Zero
    TOinitial = 0             
    WHSinitial = 0

    #Iterate until starting and ending top oil temp are the same
    for i in range(25): #Stop after 25 iterations if not converged

        #Set up containers for final results
        List_TOtemp = []; List_WHStemp = []; List_V = []

        #Set starting temperatures to final in previous run
        TOprev = TOinitial
        WHSprev = WHSinitial
            
        # Loop through loads values
        for index, Load in enumerate(TempLoadShape):
            # Check if load is bigger than previous
            PrevLoad = TempLoadShape[index - 1]
            if Load > PrevLoad:
                LoadIncreasing = True
            else:
                LoadIncreasing = False
        
            TOrise = calc_top_oil_rise(t, TOprev, Load, HeatRunData, ThermalChar)
            TOtemp = AmbWHS + TOrise
     
            WHSrise = calc_winding_rise(t, WHSprev, Load, HeatRunData, ThermalChar,LoadIncreasing)
            WHStemp = AmbWHS + TOrise + WHSrise
            WHSageing = AmbAgeing + TOrise + WHSrise
            V = relative_ageing_rate(WHSageing)

            List_TOtemp.append(TOtemp)
            List_WHStemp.append(WHStemp)
            List_V.append(V)
            
            # Set final temps as starting temperature for next in loop
            TOprev = TOrise
            WHSprev = WHSrise
            
        # Check if converged early
        if TOinitial == TOrise:
            break # Exit loop
        
        # Set ending temperatures to initial 
        TOinitial = TOrise
        WHSinitial = WHSrise

    # Calculate the maximum and total values
    RatedLoad = HeatRunData['RatedLoad']
    Max_Load = max(TempLoadShape)
    Max_TOtemp = max(List_TOtemp)
    Max_WHStemp = max(List_WHStemp)

    L = 0 
    for V in List_V:
        L += (V * t)  # Sum loss of life in minutes for each interval
    L = L / 60        # Calculate loss of life in hours
   
    Limit, Reason = was_limit_reached(Limits, RatedLoad, Max_Load, Max_TOtemp, Max_WHStemp, L)

    return Limit, Reason, Max_Load, Max_TOtemp, Max_WHStemp, L

def was_limit_reached(Limits, RatedLoad, Max_Load, Max_TOtemp, Max_WHStemp, LoL):
    """
    Check if any limits were reached
    """
    
    Limit = False
    Reason = 'Limit not reached'
    LoadPu = (Max_Load / RatedLoad)
    
    if LoadPu >= Limits['MaxLoadPU']:
        Limit = True
        try:
            Reason = Limits['MaxLoadPU_Reason']
        except KeyError:
            Reason = '1.5 pu'

    if LoL >= Limits['LoL']:
        Limit = True
        try:
            Reason = Limits['LoL_Reason']
        except KeyError:
            Reason = 'Loss of Life'
            
    if Max_TOtemp >= Limits['TopOil']:
        Limit = True
        try:
            Reason = Limits['TopOil_Reason']
        except KeyError:
            Reason = 'Top Oil Temp'

    if Max_WHStemp >= Limits['HotSpot']:
        Limit = True
        try:
            Reason = Limits['HotSpot_Reason']
        except KeyError:
            Reason = 'WHS Temp'

    return Limit, Reason

def calc_winding_rise(t, StartTemp, Load, HeatRunData, ThermalChar, LoadIncreasing):
    """
    Calculate the winding rise
    Input values:
    t = Time Interval (min)
    StartTemp = Initial Top Oil Rise
    Load = Load to be considered (in MVA)
    HeatRunData is a dictionary containing test results
    ThermalChar is a dictionary containting thermal characteristics for cooling type
    """

    # Set up variables
    RatedLoad = HeatRunData['RatedLoad']
    K = Load / RatedLoad
    gr = HeatRunData['gr']
    H = HeatRunData['H']
    y = ThermalChar['y']

    TauW = ThermalChar['TauW']
    k11 = ThermalChar['k11']
    k21 = ThermalChar['k21']
    k22 = ThermalChar['k22']

    # Determine the oil thermal time constant - rated load
    C = ThermalChar['C']
    P = HeatRunData['P']
    dTOr = HeatRunData['dTOr']
    if C == 0:
        # Use Lookup Table - AS 60077.7-2013 Table 5
        CoolingType = ThermalChar['CoolingType']
        Cooling_List = ['ODAF','ODAN','OFAN','OF','OFB']
        if any(CoolingType in s for s in Cooling_List):
            TauR = 90.0
        else:
            Cooling_List = ['ONAF','OB']
            if any(CoolingType in s for s in Cooling_List):
                TauR = 150.0
            else:
               TauR = 210.0 
    else:
        # Calculate Value
        TauR = thermal_time_constant_at_rated_load(C,P,dTOr)
        
    # Calculate ultimate winding rise to simplify below formulas
    dWHS = H * gr * (K ** y)

    if LoadIncreasing == True:
        #As per AS60076.7 Eq. (5)
        f2 = k21 * (1- math.exp((-t)/(k22*TauW))) - (k21 -1) * (1- math.exp((-t)/(TauR/k22)))
        dWHSt = StartTemp + (dWHS - StartTemp) * f2
    else:
        #As per AS60076.7 Eq. (6)
        dWHSt = dWHS + (StartTemp-dWHS) * math.exp((-t)/(TauW))

    #print 'dWHS: ' + str(dWHS) + ' vs instdWHS: ' + str(dWHSt)
    return dWHSt
    
def calc_top_oil_rise(t, StartTemp, Load, HeatRunData, ThermalChar):
    """
    Calculate top oil rise
    Input values:
    t = Time Interval (min)
    StartTemp = Initial Top Oil Rise
    Load = Load to be considered (in MVA)
    HeatRunData is a dictionary containing test results
    ThermalChar is a dictionary containting thermal characteristics for cooling type
    """

    #Set up variables
    dTOi = StartTemp
    
    dTOr = HeatRunData['dTOr']
    RatedLoad = HeatRunData['RatedLoad']
    P = HeatRunData['P']
    R = HeatRunData['R']
    
    x = ThermalChar['x']
    C = ThermalChar['C']
    n = ThermalChar['n']           
    k11 = ThermalChar['k11']

    K = Load / RatedLoad
    
    #Determine ultimate (steady state) temperature for given load
    dTOult = ult_top_oil_rise_at_load(K, R, dTOr, x)

    #Determine the oil thermal time constant - rated load
    if C == 0:
        #Use Lookup Table - AS 60077.7-2013 Table 5
        CoolingType = ThermalChar['CoolingType']
        Cooling_List = ['ODAF','ODAN','OFAN','OF','OFB']
        if any(CoolingType in s for s in Cooling_List):
            TauR = 90.0
        else:
            Cooling_List = ['ONAF','OB']
            if any(CoolingType in s for s in Cooling_List):
                TauR = 150.0
            else:
               TauR = 210.0 
    else:
        #Calculate Value
        TauR = thermal_time_constant_at_rated_load(C,P,dTOr)

    #Determine the oil thermal time constant - specified load
    Tau = thermal_time_constant_as_considered_load(TauR,dTOr,dTOi,dTOult, n)
   
    #Determine instantaneous top oil temperature for given load
    dTO = inst_top_oil_rise_at_load(dTOi, dTOult, t, K, R, dTOr, x, k11, Tau)
      
    return dTO

def ult_top_oil_rise_at_load(K, R, dTOr, x):
    """
    Calculate the steady-state top oil rise for a given load
    K = Ratio of ultimate load to rated load
    R = Ratio of load lossed at rated load to no-load loss on top tap being studied
    x = oil exponent based on cooling method
    TOrated = Top-oil temperature at rated load (as determined by heat run)
    """
    dTO = dTOr * ((((K**2)*R) + 1) / (R+1)) ** x

    return dTO



def inst_top_oil_rise_at_load(dTOi, dTOult, t, K, R, dTOr, x, k11, Tau):
    """
    Calculate the instanous top oil rise at a given time period
    """
    #As per AS60076.7 Eq. (2)
    dTO = dTOult + (dTOi - dTOult) * math.exp((-t)/(k11*Tau))

    return dTO

def thermal_time_constant_at_rated_load(C,P,dTOr):
    """
    Returns the average oil time constant in minutes (for rated load)
    C = Thermal capacity of oil
    P = Supplied losses (in W) at the load considered
    OilRise = The average oil temperature rise above ambient temperature in K at the load considered
    """
                                  
    #As per IEEE C57.91-2011
    tau = (C * dTOr * 60) / P

    return tau

def thermal_time_constant_as_considered_load(TauR,dTOr,dTOi,dTOu, n):
    """
    Returns the average oil time constant in minutes (for a given load)
    TauR = Thermal time constant at rated load
    dTOr = Top oil rise at rated load
    dTOi = Top oil rise initial
    dTOu = Top oil rise ultimate (at load considered)
    n = Temperature cooling exponent (From IEEE C57.91-2011 Table 4)
    """
                                  
    #As per IEEE C57.91-2011
    a = dTOu / dTOr
    b = dTOi / dTOr
    
    if (a-b) == 0:
        #Calculation is for rated load
        #Will cause divide by zero error
        STTTC = TauR
    elif n == 0:
        STTTC = TauR
    else:
        try:
            STTTC = TauR * (a-b)/((a**(1/n))-(b**(1/n)))
        except ZeroDivisionError:
            STTTC = TauR #The a-b didn't catch the error
   
    return STTTC
                            

def relative_ageing_rate(WHST):
    """
    Calculate the relative ageing rate of the transformer for a given
    Winding Hotspot Temperature
    """

    #As per AS60076.7 Eq. (2)
    try:
        V = 2 ** ((WHST-98.0)/6)  #Applies to non-thermally upgraded paper only
    except OverflowError:
        V = 10000000.0            #High WHST numbers cause errors
        
    return V

if __name__ == '__main__':
    main()

