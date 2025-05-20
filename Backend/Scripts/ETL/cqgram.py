import os
import sys

sys.dont_write_bytecode = True

import requests
import datetime
import numpy as np
import pandas as pd
import CrossQuantilogram as cq
import yfinance as yf

import matplotlib.pyplot as plt
import seaborn as sns




class CQGramPipeline:
    '''
    Class for calculating and working with CQ-gram related data.

    Parameters:
        - bechmarks: assets to be tested against
        - candidates: safe-haven asset candidates
    '''

    def __init__(self, benchmarks, candidates, include_benchmarks=False, **kwargs):
        
        self.benchmarks = benchmarks
        self.candidates = candidates
        self.include_benchmarks = include_benchmarks

        self.data = {}
        self.current_output = {}

        self.normalize_significance = kwargs.get('normalize_significance', True)


    def compute_log_returns(self, X):
        X_new = X.copy()
        X_new['log_return'] = np.log(X_new['Adj Close'] / X_new['Adj Close'].shift(1))
        return X_new


    def add_timedelta(self, date, delta, return_type='str'):
        date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        new_date = date_obj + datetime.timedelta(days=delta)
        if return_type == 'str':
            return new_date.strftime('%Y-%m-%d')
        return new_date


    def fetch_data_adjusted(self, tickers=None, start=None, end=None, period='max'):

        # NOTE: audit fix -> adding (start_t-1, end_t+1)

        if start is not None:
            start = self.add_timedelta(start, delta=-1)
        if end is not None:
            end = self.add_timedelta(end, delta=1)

        if tickers is not None:
            self.data['tickers'] = {}

            for name, ticker in tickers.items():
                self.data['tickers'][name] = yf.Ticker(ticker).history(start=start, end=end, period=period, auto_adjust=False)
                self.data['tickers'][name] = self.compute_log_returns(self.data['tickers'][name])

            return self.data
        
        self.data = {}

        self.data['benchmarks'] = {}
        self.data['candidates'] = {}
        self.data['tickers'] = {}

        for name, ticker in self.benchmarks.items():
            self.data['benchmarks'][name] = yf.Ticker(ticker).history(start=start, end=end, period=period, auto_adjust=False)
            self.data['benchmarks'][name] = self.compute_log_returns(self.data['benchmarks'][name])
        
        for name, ticker in self.candidates.items():
            self.data['candidates'][name] = yf.Ticker(ticker).history(start=start, end=end, period=period, auto_adjust=False)
            self.data['candidates'][name] = self.compute_log_returns(self.data['candidates'][name])

        return self.data


    def align_series(self, X, Y, start=None, end=None):
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
    

    def Q_statistic_test(self, result):
        '''rules for q-statistic and H0 rejection -> no directional predictability'''

        rule = result.apply(lambda row: abs(row['q']) > row['qc'], axis=1)
        result['H0_rejected'] = rule
        return result
    

    def set_significance(self, result):
        result['cq'] = result['cq'].where(result['H0_rejected'], 0)
        return result
    

    def add_lag_parameter(self, result, lag):
        result['lag'] = result.index
        result['max_lag'] = lag
        return result
    

    def add_timestamp(self, result, start, end):
        result['date_start'] = start
        result['date_end'] = end
        return result


    @classmethod
    def stationarity_test(self, X, k):
        '''returns p-value of ADF stationarity test.'''
        X_copy = X.copy().dropna()
        return cq.DescriptiveStatistics(X_copy, k)['adfpv']
    

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


    def save_results(self, path, **kwargs):
        df = self.create_dataframe_from_cqgram(self.current_output)
        df.to_csv(path, **kwargs)



    # FOREX RECALC

    def compute_CQBS_FOREX(self, **kwargs):
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

            print(benchmark)

            for candidate in self.data['candidates'].keys():
                if benchmark != candidate:

                    # NOTE: quick forex computation heuristics
                    forex = ['Japanese Yen', 'Euro', 'Chinese Yuan']
                    if benchmark in forex or candidate in forex:
                        Y = self.data['candidates'][candidate]['log_return'].dropna()
                        #output = output | self.compute_pair_CQBS(X, tau1_list, Y, tau2_list, max_lag=lag, benchmark=benchmark, candidate=candidate)                         # NOTE: fix issue 1 (planning)
                        output = output | self.compute_pair_CQBS(Y, tau2_list, X, tau1_list, max_lag=lag,
                                                                benchmark=benchmark, candidate=candidate, verbose=verbose, start=start, end=end)                                                   # NOTE: requires switch (X,Y) -> (Y, X) (taus as well)

            if self.include_benchmarks:
                for benchmark2 in self.data['benchmarks'].keys():
                    if benchmark != benchmark2:

                        # NOTE: quick forex computation heuristics
                        forex = ['Japanese Yen', 'Euro', 'Chinese Yuan']
                        if benchmark in forex or benchmark2 in forex:
                            Y = self.data['benchmarks'][benchmark2]['log_return'].dropna()
                            #output = output | self.compute_pair_CQBS(X, tau1_list, Y, tau2_list, max_lag=lag, benchmark=benchmark, candidate=benchmark2)
                            output = output | self.compute_pair_CQBS(Y, tau2_list, X, tau1_list, max_lag=lag,
                                                                    benchmark=benchmark, candidate=benchmark2, verbose=verbose, start=start, end=end)

        self.current_output = output

        return output



    # ===============================
    # ROLLING WINDOW ANALYSIS - maybe 
    # NOTE: NOT USED


    def compute_rolling_CQBS(self, window=21, max_lag=1, tau1_list=None, tau2_list=None, jump=0, **kwargs):

        if tau1_list is None:
            tau1_list = []
        if tau2_list is None:
            tau2_list = []


        result_collection = []
    
        for benchmark in self.data['benchmarks'].keys():
            X = self.data['benchmarks'][benchmark]['log_return'].dropna()

            for candidate in self.data['candidates'].keys():
                if benchmark != candidate:
                    Y = self.data['candidates'][candidate]['log_return'].dropna()
                    
                    X_align, Y_align = self.align_series(X, Y, start=kwargs.get('start', None), end=kwargs.get('end', None))

                    if len(X_align) < window:
                        continue

                    for i in range(window, len(X_align) + 1):
                        # The window is [i-window, i)
                        X_window = X_align.iloc[i-window:i]
                        Y_window = Y_align.iloc[i-window:i]

                        pair_result_dict = self.compute_pair_CQBS(
                            Y_window, tau2_list,    # Y & tau2
                            X_window, tau1_list,    # X & tau1
                            max_lag=max_lag,
                            benchmark=benchmark,
                            candidate=candidate,
                            **kwargs
                        )

                        df_temp = self.create_dataframe_from_cqgram(pair_result_dict)

                        rolling_date = X_window.index[-1]
                        df_temp['rolling_date'] = rolling_date

                        result_collection.append(df_temp)

            # benchmarky included
            if self.include_benchmarks:
                for benchmark2 in self.data['benchmarks'].keys():
                    if benchmark != benchmark2:
                        Y = self.data['benchmarks'][benchmark2]['log_return'].dropna()
                        
                        X_align, Y_align = self.align_series(X, Y, start=kwargs.get('start', None), end=kwargs.get('end', None))

                        if len(X_align) < window:
                            continue

                        for i in range(window, len(X_align) + 1):
                            # The window is [i-window, i)
                            X_window = X_align.iloc[i-window:i]
                            Y_window = Y_align.iloc[i-window:i]

                            pair_result_dict = self.compute_pair_CQBS(
                                Y_window, tau2_list,    # Y & tau2
                                X_window, tau1_list,    # X & tau1
                                max_lag=max_lag,
                                benchmark=benchmark,
                                candidate=candidate,
                                **kwargs
                            )

                            df_temp = self.create_dataframe_from_cqgram(pair_result_dict)

                            rolling_date = X_window.index[-1]
                            df_temp['rolling_date'] = rolling_date

                            result_collection.append(df_temp)
        

        if result_collection:
            final_df = pd.concat(result_collection, ignore_index=True)
        else:
            final_df = pd.DataFrame()

        return final_df



