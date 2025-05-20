# Metada to selected subset of data

import os
import sys
import pandas as pd


asset_metadata_empty = {
    '^GSPC' : None,
    '^STOXX50E' : None,
    '^N225' : None,
    '^FTSE' : None,
    'MCHI' : None,

    'GC=F' : None,
    'NG=F' : None,
    'CL=F' : None,
    'BTC-USD' : None,
    'ETH-USD' : None,
    'CHFUSD=X' : None,
    'JPY=X' : None,
    'CNY=X' : None,
    '^TNX' : None,
    '^VIX' : None
}


asset_metadata = {
    # Benchmarks (Equity Indices)
    '^GSPC': {'Geographical Region': 'USA', 'Asset Class': 'Equity Index'},
    '^STOXX50E': {'Geographical Region': 'Eurozone', 'Asset Class': 'Equity Index'},
    '^N225': {'Geographical Region': 'Japan', 'Asset Class': 'Equity Index'},
    '^FTSE': {'Geographical Region': 'UK', 'Asset Class': 'Equity Index'},
    '000001.SS': {'Geographical Region': 'China', 'Asset Class': 'Equity Index'},  # SSE Composite
    'MCHI': {'Geographical Region': 'China', 'Asset Class': 'Equity Index'},

    # Commodities
    'GC=F': {'Geographical Region': 'Global', 'Asset Class': 'Commodity'},  # Gold Futures
    'NG=F': {'Geographical Region': 'Global', 'Asset Class': 'Commodity'},  # Natural Gas Futures
    'CL=F': {'Geographical Region': 'Global', 'Asset Class': 'Commodity'},  # Crude Oil Futures
    'PL=F': {'Geographical Region': 'Global', 'Asset Class': 'Commodity'},  # Platinum

    # Cryptocurrencies
    'BTC-USD': {'Geographical Region': 'Global', 'Asset Class': 'Cryptocurrency'},
    'ETH-USD': {'Geographical Region': 'Global', 'Asset Class': 'Cryptocurrency'},

    # Forex (Currencies)
    'EUR=X': {'Geographical Region': 'Global', 'Asset Class': 'Forex'},  # Euro
    'CHFUSD=X': {'Geographical Region': 'Global', 'Asset Class': 'Forex'},  # Swiss Franc
    'JPY=X': {'Geographical Region': 'Global', 'Asset Class': 'Forex'},  # Japanese Yen
    'CNY=X': {'Geographical Region': 'Global', 'Asset Class': 'Forex'},  # Chinese Yuan

    # Bonds
    '^TNX': {'Geographical Region': 'USA', 'Asset Class': 'Bonds'},  # 10-year Treasury Bonds

    # Derivatives
    '^VIX': {'Geographical Region': 'USA', 'Asset Class': 'Derivatives'}  # Volatility Index
}


asset_metadata = {
    # Benchmarks (Equity Indices)
    '^GSPC': {
        'Geographical Region': 'USA', 
        'Asset Class': 'Equity Index', 
        'Name': 'S&P500'
    },
    '^STOXX50E': {
        'Geographical Region': 'Eurozone', 
        'Asset Class': 'Equity Index', 
        'Name': 'EURO STOXX 50'
    },
    '^N225': {
        'Geographical Region': 'Japan', 
        'Asset Class': 'Equity Index', 
        'Name': 'Nikkei 225'
    },
    '^FTSE': {
        'Geographical Region': 'UK', 
        'Asset Class': 'Equity Index', 
        'Name': 'FTSE 100'
    },
    '000001.SS': {
        'Geographical Region': 'China', 
        'Asset Class': 'Equity Index', 
        'Name': 'SSE Composite'
    },
    'MCHI': {
        'Geographical Region': 'China', 
        'Asset Class': 'Equity Index', 
        'Name': None  # No friendly name provided
    },

    # Commodities
    'GC=F': {
        'Geographical Region': 'Global', 
        'Asset Class': 'Commodity', 
        'Name': 'Gold Futures'
    },
    'NG=F': {
        'Geographical Region': 'Global', 
        'Asset Class': 'Commodity', 
        'Name': 'Natural Gas Futures'
    },
    'CL=F': {
        'Geographical Region': 'Global', 
        'Asset Class': 'Commodity', 
        'Name': 'Crude Oil Futures'
    },
    'PL=F': {
        'Geographical Region': 'Global', 
        'Asset Class': 'Commodity', 
        'Name': 'Platinum'
    },

    # Cryptocurrencies
    'BTC-USD': {
        'Geographical Region': 'Global', 
        'Asset Class': 'Cryptocurrency', 
        'Name': 'Bitcoin'
    },
    'ETH-USD': {
        'Geographical Region': 'Global', 
        'Asset Class': 'Cryptocurrency', 
        'Name': 'Ethereum'
    },

    # Forex (Currencies)
    'CHFUSD=X': {
        'Geographical Region': 'Global', 
        'Asset Class': 'Forex', 
        'Name': 'Swiss Franc'
    },

    'EURUSD=X' : {
        'Geographical Region': 'Global', 
        'Asset Class': 'Forex', 
        'Name': 'Euro'
    },

    'CNYUSD=X' : {
        'Geographical Region': 'Global', 
        'Asset Class': 'Forex', 
        'Name': 'Chinese Yuan'
    },

    'JPYUSD=X' : {
        'Geographical Region': 'Global', 
        'Asset Class': 'Forex', 
        'Name': 'Japanese Yen'
    },

    # Bonds
    '^TNX': {
        'Geographical Region': 'USA', 
        'Asset Class': 'Bonds', 
        'Name': '10-year treasury bonds'
    },

    # Derivatives
    '^VIX': {
        'Geographical Region': 'USA', 
        'Asset Class': 'Derivatives', 
        'Name': 'Volatility Index'
    }
}



asset_metadata_df = pd.DataFrame.from_dict(asset_metadata, orient='index').reset_index().rename(columns={'index': 'ticker', 'Name' : 'name'})
