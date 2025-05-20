import os
import sys

sys.dont_write_bytecode = True

import requests
import pickle
import datetime
import numpy as np
import pandas as pd
import CrossQuantilogram as cq
import yfinance as yf

import matplotlib.pyplot as plt
import seaborn as sns

from Scripts.PROD.data import map_period_timestamps, map_metadata
from Scripts.PROD.constants import *
from Configs.asset_metadata import asset_metadata_df
from Configs.asset_crissis_mapping import *

# ===============================
# ANALYTICS



class AnalyticsPipeline:

    def __init__(self, asset_mapping=None, period_mapping=None):
        if asset_mapping is None:
            self.asset_mapping = {}
        else:
            self.asset_mapping = asset_mapping
        if period_mapping is None:
            self.period_mapping = {}
        else:
            self.period_mapping = period_mapping

        self.asset_period_data = {}

        self.descriptive_data = None
        self.cq_result_data   = None


    def save_to_file(self, file_path, file_name):
        with open(f'{file_path}/{file_name}', 'wb') as f:
            pickle.dump(self.asset_period_data, f)

    def load_from_file(self, file_path, file_name):
        try:
            with open(f'{file_path}/{file_name}', 'rb') as f:
                self.asset_period_data = pickle.load(f)
        except:
            self.asset_period_data = pd.read_csv(file_path + file_name)

    def load_data(self):
        for period, data in self.period_mapping.items():
            self.asset_period_data[period] = {}
            
            for phase, dates in data.items():
                self.asset_period_data[period][phase] = {}
                start, end = dates
                
                for asset, ticker in self.asset_mapping.items():
                    ticker_data = self.fetch_data_adjusted(ticker=ticker, start=start, end=end)
                    ticker_data['asset_name'] = asset
                    self.asset_period_data[period][phase][asset] = ticker_data

        return self.asset_period_data


    def add_timedelta(self, date, delta, return_type='str'):
        date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        new_date = date_obj + datetime.timedelta(days=delta)
        if return_type == 'str':
            return new_date.strftime('%Y-%m-%d')
        return new_date

    def compute_log_returns(self, X):
        X_new = X.copy()
        X_new['log_return'] = np.log(X_new['Adj Close'] / X_new['Adj Close'].shift(1))
        return X_new

    def fetch_data_adjusted(self, ticker, start=None, end=None, period='max'):
        if start is not None:
            start = self.add_timedelta(start, delta=-1)
        if end is not None:
            end = self.add_timedelta(end, delta=1)
        
        output = yf.Ticker(ticker).history(start=start, end=end, period=period, auto_adjust=False)
        output = self.compute_log_returns(output)
        output = output.dropna(subset='log_return')

        return output

    # ======================
    # Descriptive statistics

    def compute_asset_descriptive_statistics(self):
        result = []
        for period, phase_data in self.asset_period_data.items():
            for phase, asset_data in phase_data.items():
                for asset, data in asset_data.items():
                    row = data['log_return'].describe().to_frame().T
                    row['period'] = period
                    row['phase'] = phase
                    row['asset'] = asset
                    result.append(row)

        self.descriptive_data = pd.concat(result, ignore_index=True)

        return self.descriptive_data
    
    
    def compute_mean_volatility_analysis(self):
        result2 = map_period_timestamps(self.descriptive_data, period_mapping_df)

        table = result2.query("phase == 'full_period'").pivot(
            columns=['phase','period', 'period_start', 'period_end'], 
            index='asset', 
            values=['mean', 'std', 'min', 'max']
        ).sort_index(axis=1, level=[0, 3], ascending=True)

        # default subset pre data viz
        res = table[['mean', 'std']]

        output = res.loc[res['std'].mean(axis=1, skipna=False).sort_values(ascending=False).index].map(lambda x: f'{x*100:.2f}')

        return output

    

    # ===
    # Asset Cross-Quantilogram descriptives

    def load_cq_data(self, data):
        self.cq_result_data = data


    def compute_asset_period_cq_means(self, phase='full_period', taux=0.05, tauy=0.95):
        
        subset = self.cq_result_data.query(f'phase == "{phase}" and H0_rejected and tau1 in ({taux},) and tau2 in ({taux, tauy})')

        pivoted = subset.groupby(['name_candidate', 'period', 'tau1', 'tau2'], as_index=False)['cq'].mean().pivot(
            index=['name_candidate'],
            columns=['period', 'tau1', 'tau2'],
            values='cq',
        ).round(3).fillna('')

        period_order = ['GFC','ESDC','COVID','UA']
        tau2_order   = [0.05, 0.95]

        pivoted = pivoted.reindex(
            columns=pd.MultiIndex.from_product(
                [period_order, [taux], tau2_order],
                names=['period','tau1','tau2']
            ),
            fill_value=''
        )

        return pivoted


    


    
    # ======================
    # Network analysis
    # NOTE: separate file



