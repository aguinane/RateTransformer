# Required Inputs

The following inputs are required to calculate the cyclic rating.

## Thermal Characteristics

| Attribute | Example | Units | Desc |
|---        |---      |---    |--- |
| cooling_mode | ONAN | -  | Cooling method in use |
| rated_load  | 25 | MVA  | Nameplate rating |
| dTOr | 35.4 | °C | Top-oil temperature rise in steady state at rated losses |
| gr | 14.8  | °C | Average-winding-to-average-oil (in tank) temp gradient at rated current |
| P  | 20,220 | W    | Supplied Losses (Max Copper Loss + Max Iron Loss) |
| R  | 23  | -    | Ratio of load losses at rated current to no-load losses (Copper / Iron) |

The following values can be specified, or will be assumed based on the cooling mode if not provided.

| Cooling Mode      |  | ONAN, ON  | ONAF, OB  | OFAN, OF, OFB  | ODAN  | ODAF |
|---                |---    |---   |---  |---   |---   |---   |
|Winding Hotspot    | H     | 1.3  | 1.3 | 1.3  | 1.3  | 1.3  |
|Oil Exponent       | x     | 0.8  | 0.8 | 1.0  | 1.0  | 1.0  |
|Winding Exponent   | y     | 1.3  | 1.3 | 1.3  | 2.0  | 2.0  |
|Constant           | k11   | 0.5  | 0.5 | 1.0  | 1.0  | 1.0  |
|Constant           | k21   | 2.0  | 2.0 | 1.3  | 1.0  | 1.0  |
|Constant           | k22   | 2.0  | 2.0 | 1.0  | 1.0  | 1.0  |
|Oil Time Constant  | tauO  | 210  | 150 | 90   | 90   | 90   |
|Winding Time Constant|tauW | 10   | 7   | 7    | 7    | 7    |

Alternatively, tauO can be calculated if the following values are provided.

| Attribute | Example | Units | Desc |
|---        |---      |---    |--- |
| mass_assembly | 19,000| kg  | The mass of core and coil assembly |
| mass_tank | 10,000| kg  | The mass of tanks and fittings |
| mass_oil | calculated |   | The mass of oil in litres (~87.8% volume) |
| vol_oil | 14,000| L  | The volume of oil in litres |


The tauO calculation also requires the following IEEE constant:
| Cooling Mode      |  | ONAN, ON  | ONAF, OB, OFAN, OF, OFB  | ODAN,  ODAF |
|---                |---    |---   |---     |---   |
|Oil Constant | n     | 0.8  | 0.9   | 1.0   |


## Seasonal Characteristics
| Attribute | Example | Units | Desc |
|---        |---      |---    |--- |
|ambient_ageing  | 27.8   | °C    |The yearly weighted ambient temperature  |
|ambient_WHS     | 24.7   | °C    | The monthly average temperature of the hottest month |
|load_shape | [9, 9, 12, etc.] | MVA list | Typical day load profile in 30min intervals |

## Limits

You may specify whatever limit you would like to rate against.
If not specifedm the normal cylcic loading limits from the standard will be used.

| Attribute | Units | Desc | default |
|---        |---      |---    |--- |
| MaxLoadPU | pu |   Maximum nameplate loading [pu] | 1.5
| HotSpot | °C |  Maximum winding hot spot temperature [°C] | 120
| TopOil |°C |   Maximum top oil temperature [°C] | 105
| LoL | hours / day | Ageing (loss-of-life) limit | 24 (normal)  |
