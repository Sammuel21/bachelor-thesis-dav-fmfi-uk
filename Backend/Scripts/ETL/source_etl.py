# NOTE: abstract source integraton objects

import os
import sys

sys.dont_write_bytecode = True

import datetime
import numpy as np
import pandas as pd
import yfinance as yf


# Base

class Source:

    def __init__(self, tickers=None):
        if tickers is None:
            self.tickers = {}
        else:
            self.tickers = {}

    def fetch(self, ticker, **kwargs):
        return pd.DataFrame()
    
    def fetch_adjusted_data(self, ticker, **kwargs):
        pass

# ---


# Sources:

# Yahoo

class Yahoo(Source):

    def __init__(self, ticker_mapping):
        self.ticker_mapping = ticker_mapping
        self.data = None

    def add_timedelta(self, date, delta, return_type='str'):
        date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        new_date = date_obj + datetime.timedelta(days=delta)
        if return_type == 'str':
            return new_date.strftime('%Y-%m-%d')
        return new_date


    def fetch(self, ticker, start=None, end=None, period='max'):
        if start is not None:
            start = self.add_timedelta(start, delta=-1)
        if end is not None:
            end = self.add_timedelta(end, delta=1) 

        try:
            return yf.Ticker(ticker).history(start=start, end=end, period=period, auto_adjust=False)
        except:
            raise ValueError(f'Error during fetching Yahoo --> ticker: {ticker}; params = ({start, end})')


    def fetch_adjusted_data(self, start=None, end=None, period='max'):
        self.data = pd.DataFrame()

        result = []
        for name, ticker in self.ticker_mapping.items():
            ticker_data = self.fetch(ticker, start, end, period).reset_index()
            ticker_data['ticker'] = name
            ticker_data['start'] = str(start)
            ticker_data['end'] = str(end)
            result.append(ticker_data)
        
        result = pd.concat(result, ignore_index=True)
        self.data = result
        
        return result


# ---

# NADSTAVBA:

# ---
