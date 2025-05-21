# NOTE: Integration

import os
import sys

sys.dont_write_bytecode = True

import datetime
import numpy as np
import pandas as pd
import yfinance as yf



class Integration:

    def __init__(self, source_mapping, config=None):
        if config is None:
            self.config = {}
        else:
            self.config = config

        self.source_mapping = source_mapping


    def data_source_integration(self, **kwargs):
        combined = []

        for name, source in self.source_mapping.items():
            pass

        return pd.concat(combined, ignore_index=True)
