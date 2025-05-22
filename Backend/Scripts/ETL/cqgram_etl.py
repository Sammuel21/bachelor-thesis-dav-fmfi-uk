import os
import sys

sys.dont_write_bytecode = True

import requests
import datetime
import numpy as np
import pandas as pd
import CrossQuantilogram as cq



# Base

class DataTransformer:

    @staticmethod
    def compute_log_returns(X, column='Adj Close'):
        X_new = X.copy()
        X_new['log_return'] = np.log(X_new[column] / X_new[column].shift(1))
        return X_new
    
    @staticmethod
    def align_series(X, Y, start=None, end=None):
        '''Aligns X, Y based on common index (timeseries). (start, end) serve as subset selection.'''
        try:
            X_copy = X.copy()
            Y_copy = Y.copy()

            X_copy.index = X.index.date
            Y_copy.index = Y.index.date

            X_aligned, Y_aligned = X_copy.align(Y_copy, join='inner')

            if start is not None:

                start = datetime.datetime.strptime(start, '%Y-%m-%d').date()

                try:
                    X_aligned = X_aligned.loc[start:]
                    Y_aligned = Y_aligned.loc[start:]
                except Exception as e:
                    print(f"Error on index cutoff: {type(e)}:{e}")

            if end is not None:

                end = datetime.datetime.strptime(end, '%Y-%m-%d').date()

                try:
                    X_aligned = X_aligned.loc[:end]
                    Y_aligned = Y_aligned.loc[:end]
                except Exception as e:
                    print(f"Error on index cutoff: {type(e)}:{e}")

            return X_aligned, Y_aligned
    
        except Exception as e:
            return X, Y


# Metrics

# CQ - Main - Thesis

class CQGramPipeline(DataTransformer):

    def __init__(self, config=None):
        if config is None:
            self.config = {}
        else:
            self.config = config

        self.include_benchmarks     = self.config.get('include_benchmarks', True)
        self.normalize_significance = self.config.get('normalize_significance', True)

        self.data = {}
        self.current_output = {}


    def load_data(self, data):

        self.data['benchmarks'] = {}
        self.data['candidates'] = {}

        for group, df in data.groupby('ticker'):        
            df_copy = df.copy().sort_values(by='Date').set_index('Date')
            df_copy = self.compute_log_returns(df_copy)
            self.data['benchmarks'][group] = df_copy
            self.data['candidates'][group] = df_copy

    @staticmethod
    def Q_statistic_test(result):
        '''rules for q-statistic and H0 rejection -> no directional predictability'''

        rule = result.apply(lambda row: abs(row['q']) > row['qc'], axis=1)
        result['H0_rejected'] = rule
        return result
    
    @staticmethod
    def set_significance(result):
        result['cq'] = result['cq'].where(result['H0_rejected'], 0)
        return result
    
    @staticmethod
    def add_lag_parameter(result, lag):
        result['lag'] = result.index
        result['max_lag'] = lag
        return result
    
    @staticmethod
    def add_timestamp(result, start, end):
        result['date_start'] = str(start)
        result['date_end'] = str(end)
        return result
    

    def compute_pair_CQBS(self, X, tau1_list, Y, tau2_list, max_lag=1, **kwargs):
        '''Computes Cross-Quantilogram statistic between X, Y.
            kwargs:
                - start: time-series alignment start
                - end: time-series alignment end
                - n: number of bootstrap iterations in cqgram
        '''
    
        benchmark = kwargs.get('benchmark', None)
        candidate = kwargs.get('candidate', None)
        
        start = kwargs.get('start', None)
        end   = kwargs.get('end', None)

        verbose = kwargs.get('verbose', True)

        # TODO !!!
        test_stationarity = kwargs.get('test_stationarity', False) # -> requires alfa setting (critical value treshold, usually a = 5%)

        X_aligned, Y_aligned = self.align_series(X, Y, start=start, end=end)

        if test_stationarity:
            if not (self.stationarity_test(X_aligned, max_lag) or self.stationarity_test(Y_aligned, max_lag)):
                return {
                    (benchmark, candidate, None, None) : 'Stationary test not satisfied'
                }

        output = {}

        # NOTE: order is switched in parent function -> implementation should be correct now [not a typo/bug]

        for tau1 in tau1_list:
            for tau2 in tau2_list:

                result = cq.CQBS(X_aligned, tau1, Y_aligned, tau2, k=max_lag, verbose=verbose)
                result = self.Q_statistic_test(result)

                if self.normalize_significance:
                    result = self.set_significance(result)

                result = self.add_lag_parameter(result, lag=max_lag)
                result = self.add_timestamp(result, start=X_aligned.index[0], end=X_aligned.index[-1])

                output[(benchmark, candidate, tau1, tau2)] = result

        return output


    def compute_CQBS(self, **kwargs):
        '''
        WARNING: Percentage calculation of returns is calculated on provided period, instead of adjusting series subset fetch data correspondingly and then use.
        Computes Cross-Quantilogram statistic from provided data (expects stationary series data).
        kwargs passed to CQBS:
            - n : number of bootstrap iterations
        '''

        lag = kwargs.get('max_lag', 1)
        tau1_list = kwargs.get('tau1_list', [])
        tau2_list = kwargs.get('tau2_list', [])
        verbose = kwargs.get('verbose', True)

        # sluzi na further time-period constraint -> subset ktori chceme pocitat
        start = kwargs.get('start', None)
        end   = kwargs.get('end', None)

        output = {}

        for benchmark in self.data['benchmarks'].keys():
            X = self.data['benchmarks'][benchmark]['log_return'].dropna()

            for candidate in self.data['candidates'].keys():
                if benchmark != candidate:
                    Y = self.data['candidates'][candidate]['log_return'].dropna()
                    #output = output | self.compute_pair_CQBS(X, tau1_list, Y, tau2_list, max_lag=lag, benchmark=benchmark, candidate=candidate)                                               # NOTE: fix issue 1 (planning)
                    output = output | self.compute_pair_CQBS(Y, tau2_list, X, tau1_list, max_lag=lag,
                                                            benchmark=benchmark, candidate=candidate, verbose=verbose, start=start, end=end)                                                   # NOTE: requires switch (X,Y) -> (Y, X) (taus as well)

            if self.include_benchmarks:
                for benchmark2 in self.data['benchmarks'].keys():
                    if benchmark != benchmark2:
                        Y = self.data['benchmarks'][benchmark2]['log_return'].dropna()
                        #output = output | self.compute_pair_CQBS(X, tau1_list, Y, tau2_list, max_lag=lag, benchmark=benchmark, candidate=benchmark2)
                        output = output | self.compute_pair_CQBS(Y, tau2_list, X, tau1_list, max_lag=lag,
                                                                benchmark=benchmark, candidate=benchmark2, verbose=verbose, start=start, end=end)

        self.current_output = output

        return output


    @classmethod
    def create_dataframe_from_cqgram(self, results):
        rows = []
        for key, df_row in results.items():
            
            if isinstance(df_row, str):
                row = pd.DataFrame()
                row['index'] = key[0]
                row['asset'] = key[1]
                row['tau2'] = key[2]
                row['tau1'] = key[3]
                row['stationarity_satisfied'] = False
            else:
                row = df_row.copy()
                row['index'] = key[0]
                row['asset'] = key[1]
                row['tau2'] = key[2]
                row['tau1'] = key[3]
                row['stationarity_satisfied'] = True

            rows.append(row)
        
        return pd.concat(rows, ignore_index=True)


    def save_results(self, path=None, **kwargs):
        if path is None:
            file_dir = kwargs.pop('output_dir', './') if not None else './'
            file = kwargs.pop('output_file', 'file.csv') if not None else 'file.csv'
            path = file_dir + file

        df = self.create_dataframe_from_cqgram(self.current_output)
        df.to_csv(path, **kwargs)


    def save_results_to_db(self, **kwargs):
        # NOTE: TODO: database compatible implementation
        pass


# ---

# Other:


