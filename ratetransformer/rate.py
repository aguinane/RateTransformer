#!/usr/bin/env python
import math


def perform_rating(TxData):
    """ Perform rating on a single transformer for specified rating limits
    """

    # Load input dictionary
    Limits = TxData['Limits']
    HeatRunData = TxData['HeatRun']
    ThermalChar = TxData['Nameplate']
    TxSeasonal = TxData['Seasonal']

    # Create our output dictionary
    TxRating = {}

    # Define some intial values
    NumIter = 0
    Limit = False
    PrevPeak = 0.0001
    InputList = (TxSeasonal['t'], HeatRunData, ThermalChar, Limits, 
                TxSeasonal['AmbWHS'], TxSeasonal['AmbAgeing'], 
                TxSeasonal['LoadShape'])

    # Calculate the starting scaling
    RatedLoad = HeatRunData['RatedLoad']
    MaxLoad = max(TxSeasonal['LoadShape'])
    #Start by incrementing by double max load
    IncrementFactor = (float(RatedLoad) / float(MaxLoad)) 
    ScaleFactor = IncrementFactor * 0.5 #Start with half initial load

    if IncrementFactor < 0.5:
        IncrementFactor = 0.5 # Start at half way

    if ScaleFactor < 0.2:
        ScaleFactor = 0.2 # Start reasonably high
    
    FinalReason = 'Did not converge' # Stops errors later
    
    # Loop until scaling factor is sufficiently small
    maxIterations = 150
    for i in range(maxIterations):
        while Limit == False:
            (Limit, Reason, Max_Load, Max_TOtemp, Max_WHStemp, 
                L) = CalculateLimit(ScaleFactor, InputList)
            NumIter += 1
            ScaleFactor += IncrementFactor
            FinalReason = Reason # So its not lost
            
        # Step back to where limit wasn't reached to get optimal rating
        ScaleFactor = ScaleFactor - (2 * IncrementFactor)
        # Check scale factor isn't negative
        if ScaleFactor < 0:
            ScaleFactor = 0
        (Limit, Reason, Max_Load, Max_TOtemp, Max_WHStemp, 
            L) = CalculateLimit(ScaleFactor, InputList)    

        # Decrese the amount scaled for next iteration run
        IncrementFactor = (IncrementFactor / 2)

        # Round values to appropriate significant figures
        TxRating['MaxLoad'] = round(Max_Load, 3)
        TxRating['MaxTOTemp'] = round(Max_TOtemp, 2)
        TxRating['MaxWHSTemp'] = round(Max_WHStemp, 2)
        TxRating['Ageing'] = round(L, 3)

        # Check if converged early
        if IncrementFactor < 0.00001: # Check scaling factor is small
            if PrevPeak == Max_Load:
                break
        PrevPeak = Max_Load

    TxRating['CRF'] = round(Max_Load / HeatRunData['RatedLoad'],4)
    TxRating['Reason'] = FinalReason
    TxRating['NumIterations'] = NumIter

    return TxRating


def CalculateLimit(ScaleFactor, InputList):
    """ Scales load and checks whether limit will be breached
    """
    (t, HeatRunData, ThermalChar, Limits, AmbWHS, AmbAgeing, 
        LoadShape) = InputList
    TempLoadShape = [i * ScaleFactor for i in LoadShape]

    # Initial Temperatures as Zero
    TOinitial = 0; WHSinitial = 0

    # Iterate until starting and ending top oil temp are the same
    for i in range(25): #Stop after 25 iterations if not converged

        # Set up containers for final results
        List_TOtemp = []; List_WHStemp = []; List_V = []

        # Set starting temperatures to final in previous run
        TOprev = TOinitial; WHSprev = WHSinitial
            
        # Loop through loads values
        for index, Load in enumerate(TempLoadShape):
            # Check if load is bigger than previous
            PrevLoad = TempLoadShape[index - 1]
            if Load > PrevLoad:
                LoadIncreasing = True
            else:
                LoadIncreasing = False
        
            TOrise = calc_top_oil_rise(t, TOprev, Load, 
                HeatRunData, ThermalChar)
            TOtemp = AmbWHS + TOrise
     
            WHSrise = calc_winding_rise(t, WHSprev, Load, HeatRunData, 
                ThermalChar,LoadIncreasing)
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
   
    Limit, Reason = was_limit_reached(Limits, RatedLoad, Max_Load, 
        Max_TOtemp, Max_WHStemp, L)

    return Limit, Reason, Max_Load, Max_TOtemp, Max_WHStemp, L


def was_limit_reached(Limits, RatedLoad, Max_Load, Max_TOtemp, 
                      Max_WHStemp, LoL):
    """ Check if any limits were reached
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


def calc_winding_rise(t, StartTemp, Load, HeatRunData, 
                      ThermalChar, LoadIncreasing):
    """ Calculate the winding rise
    Input values:
    t = Time Interval (min)
    StartTemp = Initial Top Oil Rise
    Load = Load to be considered (in MVA)
    HeatRunData is a dict with test results
    ThermalChar is a dict with thermal characteristics for cooling type
    """ 

    # Determine the oil thermal time constant - rated load
    if ThermalChar['C'] == 0:
        # Use Lookup Table - AS 60077.7-2013 Table 5
        CoolingType = ThermalChar['CoolingType']
        Cooling_List = ['ODAF', 'ODAN', 'OFAN', 'OF', 'OFB']
        if any(CoolingType in s for s in Cooling_List):
            TauR = 90.0
        else:
            Cooling_List = ['ONAF', 'OB']
            if any(CoolingType in s for s in Cooling_List):
                TauR = 150.0
            else:
               TauR = 210.0 
    else:
        # Calculate Value
        TauR = thermal_time_constant_at_rated_load(ThermalChar['C'], 
            HeatRunData['P'], HeatRunData['dTOr'])
        
    # Calculate ultimate winding rise to simplify below formulas
    K = float(Load / HeatRunData['RatedLoad'])
    dWHS = HeatRunData['H'] * HeatRunData['gr'] * (K ** ThermalChar['y'])

    if LoadIncreasing == True:
        # As per AS60076.7 Eq. (5)
        f2 = (ThermalChar['k21'] * 
            (1- math.exp((-t)/(ThermalChar['k22']*ThermalChar['TauW']))) - 
            (ThermalChar['k21'] -1) * 
            (1- math.exp((-t)/(TauR/ThermalChar['k22'])))
            )
        dWHSt = StartTemp + (dWHS - StartTemp) * f2
    else:
        # As per AS60076.7 Eq. (6)
        dWHSt = dWHS + (StartTemp-dWHS) * math.exp((-t)/(ThermalChar['TauW']))

    return dWHSt


def calc_top_oil_rise(t, StartTemp, Load, HeatRunData, ThermalChar):
    """ Calculate top oil rise
    Input values:
    t = Time Interval (min)
    StartTemp = Initial Top Oil Rise
    Load = Load to be considered (in MVA)
    HeatRunData is a dict with test results
    ThermalChar is a dict with thermal characteristics for cooling type
    """
    dTOi = StartTemp
    K = Load / HeatRunData['RatedLoad']
    # Determine ultimate (steady state) temperature for given load
    dTOult = ult_top_oil_rise_at_load(K, HeatRunData['R'], 
        HeatRunData['dTOr'], ThermalChar['x'])
    # Determine the oil thermal time constant - rated load
    if ThermalChar['C'] == 0:
        # Use Lookup Table - AS 60077.7-2013 Table 5
        CoolingType = ThermalChar['CoolingType']
        Cooling_List = ['ODAF', 'ODAN', 'OFAN', 'OF', 'OFB']
        if any(CoolingType in s for s in Cooling_List):
            TauR = 90.0
        else:
            Cooling_List = ['ONAF', 'OB']
            if any(CoolingType in s for s in Cooling_List):
                TauR = 150.0
            else:
               TauR = 210.0 
    else:
        # Calculate the Tau value
        TauR = thermal_time_constant_at_rated_load(ThermalChar['C'], 
            HeatRunData['P'], HeatRunData['dTOr'])
    # Determine the oil thermal time constant - specified load
    Tau = thermal_time_constant_as_considered_load(TauR,HeatRunData['dTOr'],
        dTOi, dTOult, ThermalChar['n'] )
    # Determine instantaneous top oil temperature for given load
    dTO = inst_top_oil_rise_at_load(dTOi, dTOult, t, K, HeatRunData['R'], 
            HeatRunData['dTOr'], ThermalChar['x'], ThermalChar['k11'], Tau)
    return dTO


def ult_top_oil_rise_at_load(K, R, dTOr, x):
    """ Calculate the steady-state top oil rise for a given load
    K = Ratio of ultimate load to rated load
    R = Ratio of load lossed at rated load to no-load loss
    on top tap being studied
    x = oil exponent based on cooling method
    TOrated = Top-oil temperature at rated load (as determined by heat run)
    """
    dTO = dTOr * ((((K**2)*R) + 1) / (R+1)) ** x

    return dTO


def inst_top_oil_rise_at_load(dTOi, dTOult, t, K, R, dTOr, x, k11, Tau):
    """ Calculate the instanous top oil rise at a given time period
    """
    # As per AS60076.7 Eq. (2)
    dTO = dTOult + (dTOi - dTOult) * math.exp((-t)/(k11*Tau))

    return dTO


def thermal_time_constant_at_rated_load(C, P, dTOr):
    """ Returns the average oil time constant in minutes (for rated load)
    As per IEEE C57.91-2011
    C = Thermal capacity of oil
    P = Supplied losses (in W) at the load considered
    OilRise = The average oil temperature rise above ambient temperature
    in K at the load considered
    """
    tau = (C * dTOr * 60) / P

    return tau


def thermal_time_constant_as_considered_load(TauR, dTOr, dTOi, dTOu, n):
    """ Returns the average oil time constant in minutes (for a given load)
    As per IEEE C57.91-2011
    TauR = Thermal time constant at rated load
    dTOr = Top oil rise at rated load
    dTOi = Top oil rise initial
    dTOu = Top oil rise ultimate (at load considered)
    n = Temperature cooling exponent (From IEEE C57.91-2011 Table 4)
    """
    a = dTOu / dTOr
    b = dTOi / dTOr
    if (a-b) == 0 or n == 0:
        # Will avoid divide by zero error
        STTTC = TauR
    else:
        try:
            STTTC = TauR * (a-b)/((a**(1/n))-(b**(1/n)))
        except ZeroDivisionError:
            STTTC = TauR    # The a-b didn't catch the error
    return STTTC


def relative_ageing_rate(WHST):
    """ Calculate the relative ageing rate of the transformer for a given
    Winding Hotspot Temperature As per AS60076.7 Eq. (2)
    Applies to non-thermally upgraded paper only
    """
    try:
        V = 2 ** ((WHST-98.0)/6)
    except OverflowError:
        V = 10000000.0  # High WHST numbers cause errors
    return V
