import logging
import math


class Transformer:
    """ A Power Transformer object
    """

    def __init__(self, HeatRunData, ThermalChar):
        """ Set up the transformer characteristics
        """
        self.HeatRunData = HeatRunData
        self.ThermalChar = ThermalChar

        self.RatedLoad = HeatRunData['RatedLoad']
        self.CoolingMode = HeatRunData['CoolingMode']
        self.P = HeatRunData['P']  # Supplied Losses
        self.dTOr = HeatRunData['dTOr']  # Top oil temp
        self.gr = HeatRunData['gr']  # Winding gradient
        self.R = HeatRunData['R']  # Loss ratio
        try:
            self.H = HeatRunData['H']  # Hot spot factor
        except KeyError:
            self.H = 1.3

        try:
            self.x = ThermalChar['x']  # Oil Exponent
        except KeyError:
            self.x = recommended_oil_exponent(self.CoolingMode)
        try:
            self.y = ThermalChar['y']  # Winding Exponent
        except KeyError:
            self.y = recommended_winding_exponent(self.CoolingMode)

        try:
            self.C = ThermalChar['C']  # Thermal Capacity
        except KeyError:
            try:
                mass_assembly = ThermalChar['mass_assembly']
                mass_tank = ThermalChar['mass_tank']
                vol_oil = ThermalChar['vol_oil']
                self.C = thermal_capacity(vol_oil, mass_assembly, mass_tank, self.CoolingMode)
            except KeyError:
                self.C = None

        try:
            self.k11 = ThermalChar['k11']
            self.k21 = ThermalChar['k21']
            self.k22 = ThermalChar['k22']
        except KeyError:
            self.k11, self.k21, self.k22 = recommended_thermal_constants(self.CoolingMode)

        try:
            self.TauW = ThermalChar['TauW']  # Winding Time Constant
        except:
            self.TauW = recommended_winding_time_constant(self.CoolingMode)

        self.n = recommended_oil_time_constant(self.CoolingMode)

    def calc_winding_rise(self, t, StartTemp, Load, LoadIncreasing):
        """ Calculate the winding rise
        Input values:
        t = Time Interval (min)
        StartTemp = Initial Top Oil Rise
        Load = Load to be considered (in MVA)
        HeatRunData is a dict with test results
        ThermalChar is a dict with thermal characteristics for cooling mode
        """

        ThermalChar = self.ThermalChar
        TauR = determine_oil_thermal_time_constant(self.CoolingMode, self.C, self.P, self.dTOr)

        # Calculate ultimate winding rise to simplify below formulas
        K = float(Load / self.RatedLoad)
        dWHS = self.H * self.gr * (K ** self.y)

        if LoadIncreasing == True:
            # As per AS60076.7 Eq. (5)
            f2 = (self.k21 *
                (1 - math.exp((-t) / (self.k22 * self.TauW))) -
                (self.k21 - 1) *
                (1 - math.exp((-t) / (TauR / self.k22)))
                )
            dWHSt = StartTemp + (dWHS - StartTemp) * f2
        else:
            # As per AS60076.7 Eq. (6)
            dWHSt = dWHS + (StartTemp - dWHS) * \
                math.exp((-t) / (self.TauW))

        return dWHSt


    def calc_top_oil_rise(self, t, StartTemp, Load):
        """ Calculate top oil rise
        Input values:
        t = Time Interval (min)
        StartTemp = Initial Top Oil Rise
        Load = Load to be considered (in MVA)
        HeatRunData is a dict with test results
        ThermalChar is a dict with thermal characteristics for cooling type
        """
        ThermalChar = self.ThermalChar
        dTOi = StartTemp
        K = Load / self.RatedLoad
        # Determine ultimate (steady state) temperature for given load
        dTOult = ult_top_oil_rise_at_load(K, self.R,
                                        self.dTOr, self.x)

        TauR = determine_oil_thermal_time_constant(self.CoolingMode, self.C, self.P, self.dTOr)

        # Determine the oil thermal time constant - specified load
        Tau = thermal_time_constant_as_considered_load(TauR, self.dTOr,
                                                    dTOi, dTOult, self.n)
        # Determine instantaneous top oil temperature for given load
        dTO = inst_top_oil_rise_at_load(dTOi, dTOult, t, self.k11, Tau)
        return dTO


    def perform_rating(self, AmbWHS=25.0, AmbAgeing=27.0, LoadShape=[], Limits={}):
        """ Perform rating on a single transformer for specified rating limits

            AmbWHS      The monthly average temperature of the hottest month [°C]
            AmbAgeing   The yearly weighted ambient temperature [°C]
            LoadShape   The cyclic load curve to be considered (in MVA)
            Limits      Current and temperature limits
        """
        self.AmbWHS = AmbWHS
        self.AmbAgeing = AmbAgeing

        self.LoadShape = LoadShape
        self.t = 30.0  # Time Interval (min)

        if self.LoadShape == []:
            self.LoadShape = [1.0] * 48

        # Get limits to determine rating for (if provided)
        # Set default limits as per AS60076.7 Table 4
        try:
            self.MaxLoadLimit = Limits['MaxLoadPU']
        except KeyError:
            self.MaxLoadLimit = 1.5
        try:
            self.TopOilLimit = Limits['TopOil']
        except KeyError:
            self.TopOilLimit = 105
        try:
            self.WHSLimit = Limits['HotSpot']
        except KeyError:
            self.WHSLimit = 120
        try:
            self.LoLLimit = Limits['LoL']
        except KeyError:
            self.LoLLimit = 24

        # Define some initial values
        NumIter = 0
        Limit = False
        PrevPeak = 0.0001

        # Calculate the starting scaling
        if self.LoadShape:
            MaxLoad = max(self.LoadShape)
        else:
            MaxLoad = self.RatedLoad

        # Start by incrementing by double max load
        IncrementFactor = (float(self.RatedLoad) / float(MaxLoad))
        ScaleFactor = IncrementFactor * 0.5  # Start with half initial load

        if IncrementFactor < 0.5:
            IncrementFactor = 0.5  # Start at half way

        if ScaleFactor < 0.2:
            ScaleFactor = 0.2  # Start reasonably high

        self.RatingReason = 'Did not converge'  # Stops errors later

        # Loop until scaling factor is sufficiently small
        maxIterations = 150
        for i in range(maxIterations):
            while Limit == False:
                (Limit, Max_Load, Max_TOtemp, Max_WHStemp,
                    L) = self.CalculateLimit(ScaleFactor, self.t, self.HeatRunData, self.ThermalChar,
                                             Limits, self.AmbWHS, self.AmbAgeing, self.LoadShape)
                NumIter += 1
                ScaleFactor += IncrementFactor

            # Step back to where limit wasn't reached to get optimal rating
            ScaleFactor = ScaleFactor - (2 * IncrementFactor)
            # Check scale factor isn't negative
            if ScaleFactor < 0:
                ScaleFactor = 0
            (Limit, Max_Load, Max_TOtemp, Max_WHStemp,
                L) = self.CalculateLimit(ScaleFactor, self.t, self.HeatRunData, self.ThermalChar,
                                         Limits, self.AmbWHS, self.AmbAgeing, self.LoadShape)

            # Decrese the amount scaled for next iteration run
            IncrementFactor = (IncrementFactor / 2)

            # Round values to appropriate significant figures
            self.MaxLoad = round(Max_Load, 3)
            self.MaxTOTemp = round(Max_TOtemp, 2)
            self.MaxWHSTemp = round(Max_WHStemp, 2)
            self.Ageing = round(L, 3)

            # Check if converged early
            if IncrementFactor < 0.00001:  # Check scaling factor is small
                if PrevPeak == Max_Load:
                    break
            PrevPeak = Max_Load

        self.CRF = round(self.MaxLoad / self.RatedLoad, 4)
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
        for i in range(25):  # Stop after 25 iterations if not converged

            # Set up containers for final results
            List_TOtemp = []
            List_WHStemp = []
            List_V = []

            # Set starting temperatures to final in previous run
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

                TOrise = self.calc_top_oil_rise(t, TOprev, Load)
                TOtemp = AmbWHS + TOrise

                WHSrise = self.calc_winding_rise(t, WHSprev, Load, LoadIncreasing)
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
                break  # Exit loop

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


def ult_top_oil_rise_at_load(K, R, dTOr, x):
    """ Calculate the steady-state top oil rise for a given load
    K = Ratio of ultimate load to rated load
    R = Ratio of load lossed at rated load to no-load loss
    on top tap being studied
    x = oil exponent based on cooling method
    TOrated = Top-oil temperature at rated load (as determined by heat run)
    """
    dTO = dTOr * ((((K**2) * R) + 1) / (R + 1)) ** x

    return dTO


def inst_top_oil_rise_at_load(dTOi, dTOult, t, k11, Tau):
    """ Calculate the instanous top oil rise at a given time period
    """
    # As per AS60076.7 Eq. (2)
    dTO = dTOult + (dTOi - dTOult) * math.exp((-t) / (k11 * Tau))

    return dTO


def determine_oil_thermal_time_constant(CoolingMode, C, P, dTOr):
    """ Determine the oil thermal time constant - rated load
    """
    if C is None or C == 0:
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
    if (a - b) == 0 or n == 0:
        # Will avoid divide by zero error
        STTTC = TauR
    else:
        try:
            STTTC = TauR * (a - b) / ((a**(1 / n)) - (b**(1 / n)))
        except ZeroDivisionError:
            STTTC = TauR    # The a-b didn't catch the error
    return STTTC


def relative_ageing_rate(WHST):
    """ Calculate the relative ageing rate of the transformer for a given
    Winding Hotspot Temperature As per AS60076.7 Eq. (2)
    Applies to non-thermally upgraded paper only
    """
    try:
        V = 2 ** ((WHST - 98.0) / 6)
    except OverflowError:
        V = 10000000.0  # High WHST numbers cause errors
    return V


def thermal_capacity(oil_volume, mass_core, mass_tank, cooling_mode):
    """ Calculate the thermal capacity of transformer oil
        As per AS60076.7 Eq. (A.4 and A.5)
    """
    if oil_volume == 0 or mass_core == 0 or mass_tank == 0:
        C = 0  # Data not available
    else:
        mass_oil = 0.87825 * oil_volume  # Mass of oil in kilograms
        Cooling_List = ['ONAN', 'ON', 'ONAF', 'OB']
        if any(cooling_mode in s for s in Cooling_List):
            C = 0.132 * mass_core + 0.0882 * mass_tank + 0.400 * mass_oil
        else:
            C = 0.132 * (mass_core + mass_tank) + 0.580 * mass_oil
    return C


def recommended_thermal_constants(cooling_mode):
    """ Get recommended oil exponent as per AS 60076.7-2013 Table 5
    """
    # Constants - As per AS 60076.7-2013 Table 5
    Cooling_List = ['ONAN', 'ONAF', 'ON', 'OB']
    if any(cooling_mode in s for s in Cooling_List):
        k11 = 0.5
        k21 = 2.0
        k22 = 2.0
    else:
        Cooling_List = ['OFAN', 'OF', 'OFB']
        if any(cooling_mode in s for s in Cooling_List):
            k11 = 1.0
            k21 = 1.3
            k22 = 1.0
        else:
            k11 = 1.0
            k21 = 1.0
            k22 = 1.0
    return k11, k21, k22


def recommended_winding_time_constant(cooling_mode):
    """ Get recommended time constant TauW as per AS 60076.7-2013 Table 5
    """
    Cooling_List = ['ONAN', 'ON']
    if any(cooling_mode in s for s in Cooling_List):
        TauW = 10.0
    else:
        TauW = 7.0
    return TauW


def recommended_oil_time_constant(cooling_mode):
    """ Get recommended oil tau constant as per IEEE C57.91-2011 Table 4
    """
    Cooling_List = ['ONAN', 'ON']
    if any(cooling_mode in s for s in Cooling_List):
        n = 0.8
    else:
        Cooling_List = ['ONAF', 'OB', 'OFAN', 'OF', 'OFB']
        if any(cooling_mode in s for s in Cooling_List):
            n = 0.9
        else:
            n = 1.0
    return n


def recommended_oil_exponent(cooling_mode):
    """ Get recommended oil exponent as per AS 60076.7-2013 Table 5
    """
    Cooling_List = ['ONAN', 'ON', 'ONAF', 'OB']
    if any(cooling_mode in s for s in Cooling_List):
        x = 0.8
    else:
        x = 1.0
    return x


def recommended_winding_exponent(cooling_mode):
    """ Get recommended oil exponent as per AS 60076.7-2013 Table 5
    """
    Cooling_List = ['ONAN', 'ONAF', 'ON', 'OB', 'OFAN', 'OF', 'OFB']
    if any(cooling_mode in s for s in Cooling_List):
        y = 1.3
    else:
        y = 2.0
    return y
