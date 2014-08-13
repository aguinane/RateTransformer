RateTransformer
===============

A tool for performing cyclic ratings of power transformers as per Australian Standard 60076.

## Installation
Run:
```
python setup.py build
python setup.py install
```
## Usage
The following will return the iteration results:
```
import ratetransformer
(FinalReason, Max_Load, Max_TOtemp, Max_WHStemp, LoL, NumIter, 
       CRF) = ratetransformer.perform_rating(TxHeatRun, TxLimits, TxDetails, TxSeasonal)
```
## Process Overview
Start the model with initial oil temperature of zero.
![Screenshot](/docs/curve_0.png?raw=true "Transformer Model")

Iterate until oil temperature stabilises for given daily load shape.
![Screenshot](/docs/curve_1.png?raw=true "Transformer Model")

Increment load magnitude until one of the passed limits are breached.
![Screenshot](/docs/curve_2.png?raw=true "Transformer Model")
(In this case the winding hotspot temperature has reached 120 degrees)
