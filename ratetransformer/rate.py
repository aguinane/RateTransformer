import math


class Transformer:
    """ A Power Transformer object
    """
    def __init__(self, HeatRunData, ThermalChar):
        self.HeatRunData = HeatRunData
        self.RatedLoad = HeatRunData['RatedLoad']
        self.ThermalChar = ThermalChar

    def perform_rating(self, AmbWHS, AmbAgeing, LoadShape, Limits):
        """ Perform rating on a single transformer for specified rating limits
        """

        self.AmbWHS = AmbWHS
        self.AmbAgeing = AmbAgeing
        self.LoadShape = LoadShape # Load to be considered (in MVA)
        self.t = 30.0  # Time Interval(min)

        self.MaxLoadLimit = Limits['MaxLoadPU']
        self.TopOilLimit = Limits['TopOil']
        self.WHSLimit = Limits['HotSpot']
        self.LoLLimit = Limits['LoL']

        # Define some initial values
        NumIter = 0
        Limit = False
        PrevPeak = 0.0001

        # Calculate the starting scaling
        RatedLoad = self.HeatRunData['RatedLoad']
        MaxLoad = max(self.LoadShape)
        # Start by incrementing by double max load
        IncrementFactor = (float(RatedLoad) / float(MaxLoad))
        ScaleFactor = IncrementFactor * 0.5 #Start with half initial load

        if IncrementFactor < 0.5:
            IncrementFactor = 0.5 # Start at half way

        if ScaleFactor < 0.2:
            ScaleFactor = 0.2 # Start reasonably high

        self.RatingReason = 'Did not converge' # Stops errors later

        # Loop until scaling factor is sufficiently small
        maxIterations = 150
        for i in range(maxIterations):
            while Limit == False:
                (Limit, Max_Load, Max_TOtemp, Max_WHStemp,
                    L) = self.CalculateLimit(ScaleFactor, self.t, self.HeatRunData, self.ThermalChar,
                    Limits, AmbWHS, AmbAgeing, LoadShape)
                NumIter += 1
                ScaleFactor += IncrementFactor

            # Step back to where limit wasn't reached to get optimal rating
            ScaleFactor = ScaleFactor - (2 * IncrementFactor)
            # Check scale factor isn't negative
            if ScaleFactor < 0:
                ScaleFactor = 0
            (Limit, Max_Load, Max_TOtemp, Max_WHStemp,
                L) = self.CalculateLimit(ScaleFactor, self.t, self.HeatRunData, self.ThermalChar,
                    Limits, AmbWHS, AmbAgeing, LoadShape)

            # Decrese the amount scaled for next iteration run
            IncrementFactor = (IncrementFactor / 2)

            # Round values to appropriate significant figures
            self.MaxLoad = round(Max_Load, 3)
            self.MaxTOTemp = round(Max_TOtemp, 2)
            self.MaxWHSTemp = round(Max_WHStemp, 2)
            self.Ageing = round(L, 3)

            # Check if converged early
            if IncrementFactor < 0.00001: # Check scaling factor is small
                if PrevPeak == Max_Load:
                    break
            PrevPeak = Max_Load

        self.CRF = round(self.MaxLoad / self.HeatRunData['RatedLoad'],4)
        self.NumIterations = NumIter

    def CalculateLimit(self, ScaleFactor, t, HeatRunData, ThermalChar,
                    Limits, AmbWHS, AmbAgeing, LoadShape):
        """ Scales load and checks whether limit will be breached
        """
        TempLoadShape = [i * ScaleFactor for i in LoadShape]

        # Initial Temperatures as Zero
        TOinitial = 0
        WHSinitial = 0

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
        Max_Load = max(TempLoadShape)
        Max_TOtemp = max(List_TOtemp)
        Max_WHStemp = max(List_WHStemp)

        LoL = calulate_loss_of_life(List_V, t)

        Limit = self.was_limit_reached(Max_Load, Max_TOtemp, Max_WHStemp, LoL)

        return Limit, Max_Load, Max_TOtemp, Max_WHStemp, LoL

    def was_limit_reached(self, Max_Load, Max_TOtemp, Max_WHStemp, LoL):
        """ Determine if any of the specified limits were reached
        """

        LoadPu = (Max_Load / self.RatedLoad)
        if LoadPu >= self.MaxLoadLimit:
            self.RatingReason = 'CRF'
            return True
        elif Max_TOtemp >= self.TopOilLimit:
            self.RatingReason = 'TO'
            return True
        elif Max_WHStemp >= self.WHSLimit:
            self.RatingReason = 'WHS'
            return True
        elif LoL >= self.LoLLimit:
            self.RatingReason = 'Age'
            return True
        else:
            return False


def calulate_loss_of_life(List_V, t):
    """ For list of V values, calculate loss of life in hours
    t = Time Interval (min)
    """
    L = 0
    for V in List_V:
        L += (V * t)  # Sum loss of life in minutes for each interval
    LoL = L / 60  # Calculate loss of life in hours
    return LoL


def calc_winding_rise(t, StartTemp, Load, HeatRunData, 
                      ThermalChar, LoadIncreasing):
    """ Calculate the winding rise
    Input values:
    t = Time Interval (min)
    StartTemp = Initial Top Oil Rise
    Load = Load to be considered (in MVA)
    HeatRunData is a dict with test results
    ThermalChar is a dict with thermal characteristics for cooling mode
    """ 

    CoolingMode = ThermalChar['CoolingMode']
    C = ThermalChar['C']
    P = HeatRunData['P']
    dTOr = HeatRunData['dTOr']
    TauR = determine_oil_thermal_time_constant(CoolingMode, C, P, dTOr)

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

    CoolingMode = ThermalChar['CoolingMode']
    C = ThermalChar['C']
    P = HeatRunData['P']
    dTOr = HeatRunData['dTOr']
    TauR = determine_oil_thermal_time_constant(CoolingMode, C, P, dTOr)

    # Determine the oil thermal time constant - specified load
    Tau = thermal_time_constant_as_considered_load(TauR,HeatRunData['dTOr'],
        dTOi, dTOult, ThermalChar['n'] )
    # Determine instantaneous top oil temperature for given load
    dTO = inst_top_oil_rise_at_load(dTOi, dTOult, t, ThermalChar['k11'], Tau)
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


def inst_top_oil_rise_at_load(dTOi, dTOult, t, k11, Tau):
    """ Calculate the instanous top oil rise at a given time period
    """
    # As per AS60076.7 Eq. (2)
    dTO = dTOult + (dTOi - dTOult) * math.exp((-t)/(k11*Tau))

    return dTO


def determine_oil_thermal_time_constant(CoolingMode, C, P, dTOr):
    """ Determine the oil thermal time constant - rated load
    """
    if C == 0:
        # Use Lookup Table - AS 60077.7-2013 Table 5
        if any(CoolingMode in s for s in ['ODAF', 'ODAN', 'OFAN', 'OF', 'OFB']):
            TauR = 90.0
        else:
            if any(CoolingMode in s for s in ['ONAF', 'OB']):
                TauR = 150.0
            else:
               TauR = 210.0
    else:
        # Calculate the Tau value
        TauR = thermal_time_constant_at_rated_load(C, P, dTOr)
    return TauR


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
