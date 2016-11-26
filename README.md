RateTransformer
===============
[![Build Status](https://travis-ci.org/aguinane/RateTransformer.svg?branch=develop)](https://travis-ci.org/aguinane/RateTransformer)

A tool for performing cyclic ratings of power transformers as per
AS/NZS 60076 Power transformers Part 7: Loading guide for oil-immersed power transformers.


### Installation
```
pip install ratetransformer
```

### Usage
The following will return the peak load rating:
```
from ratetransformer import Transformer
tx = Transformer(HeatRunData, ThermalChar)
tx.perform_rating(AmbWHS, AmbAgeing, LoadShape, Limits)
print(tx.MaxLoad)
```

An example of how these variables should be set can be seen in the example data provided in the tests folder.

More information is also provided in the docs folder.
