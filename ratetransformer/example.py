#!/usr/bin/env python3
#----------------------------------------------------

from __future__ import print_function
import math
import rate
import json

def main():
    """
    This code is run if this module is called independently 
    and is intended as a demo
    Normally this module should be used by calling the perform_rating() 
    function with transformer details passed to function
    """
    
    # Example 1
    fPath = 'example1.json'
    with open(fPath, newline='') as json_file:
        json_data = json.load(json_file)
    TxRating = rate.perform_rating(json_data)

    print('Results of calculation for Example 1:')
    print('# of Iterations: ', TxRating['NumIterations'])
    print('Reason for rating: ', TxRating['Reason'])
    print('Peak Load: ', TxRating['MaxLoad'])
    print('Top Oil Temp: ', TxRating['MaxTOTemp'])
    print('WHS Temp: ', TxRating['MaxWHSTemp'])
    print('CRF: ', TxRating['CRF'])
    print('Ageing: ', TxRating['Ageing'])
    
    # Example 2
    fPath = 'example2.json'
    with open(fPath, newline='') as json_file:
        json_data = json.load(json_file)
    TxRating = rate.perform_rating(json_data)

    print('Results of calculation for Example 2:')
    print('# of Iterations: ', TxRating['NumIterations'])
    print('Reason for rating: ', TxRating['Reason'])
    print('Peak Load: ', TxRating['MaxLoad'])
    print('Top Oil Temp: ', TxRating['MaxTOTemp'])
    print('WHS Temp: ', TxRating['MaxWHSTemp'])
    print('CRF: ', TxRating['CRF'])
    print('Ageing: ', TxRating['Ageing'])    



if __name__ == '__main__':
    main()
