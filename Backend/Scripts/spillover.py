# NOTE: Spillover analytical functions

import os
import numpy as np
import pandas as pd



# NOTE: DEV

def spillover_classification(row):
    if row['H0_rejected']:
        if row['tau1'] < row['tau2']:
            if row['cq'] < 0:
                return 'Safe-Haven'
            else:
                return 'Contagion'
        else:
            return 'Not-Assigned'

    return 'Weak-Safe-Haven'


# NOTE: PROD

def extreme_spillover_classification(row, extreme_quantiles=(0.05, 0.10, 0.90, 0.95)):
    if row['tau1'] in extreme_quantiles and row['tau2'] in extreme_quantiles:
        return 'extreme'
    return 'normal'


def spillover_classification_advanced(row, LOW=0.10, HIGH=0.90):

    tau1, tau2, cq, H0_rejected = row['tau1'], row['tau2'], row['cq'], row['H0_rejected']

    x_low   = tau1 <= LOW
    y_low   = tau2 <= LOW
    x_high  = tau1 >= HIGH
    y_high  = tau2 >= HIGH

    if not H0_rejected:
        if (x_low and y_low) or (x_low and y_high):
            return 'Weak-Safe-Haven'
        return 'Not-Assigned'

    # NOTE: retired -> nevieme dostatocne posudit ako vysoko je tau_y nad kvantilom LOW (e.g. moze to byt 0.06 ak je tau_y = 0.05)
    #if x_low and y_low and cq < 0:
    #    return 'Safe-Haven'

    if x_low and y_low and cq > 0:
        return 'Contagion'
    elif x_low and y_high and cq < 0:
        return 'Safe-Haven'

    return 'Not-Assigned'

