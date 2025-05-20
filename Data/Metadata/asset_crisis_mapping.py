import pandas as pd


# TICKERS

benchmarks = {
    'S&P500' : '^GSPC',                 # USA - S&P 500
    'EURO STOXX 50' : '^STOXX50E',      # EUROZONE
    'Nikkei 225' : '^N225',             # JAPAN
    'FTSE 100' : '^FTSE',               # UK
    'SSE Composite' : '000001.SS'       # CHINA - Shanghai Index
}

assets = {
    'Gold Futures' : 'GC=F',                # Commodities
    'Natural Gas Futures' : 'NG=F',         # Commodities
    'Crude Oil Futures' : 'CL=F',           # Commodities
    'Bitcoin' : 'BTC-USD',                  # Cryptocurrency
    'Ethereum' : 'ETH-USD',                 # Cryptocurrency
    'Platinum' : 'PL=F',                    # Commodities
    'Euro' : 'EURUSD=X',                    # Forex
    'Swiss Franc' : 'CHFUSD=X',             # Forex
    'Japanese Yen' : 'JPYUSD=X',            # Forex
    'Chinese Yuan' : 'CNYUSD=X',            # Forex
    '10-year treasury bonds' : '^TNX',      # Bonds
    'Volatility Index' : '^VIX'             # Derivatives
}

asset_mapping = benchmarks | assets

# PERIODS

period_mapping = {
    'UA' : {
        'full_period' : ('2021-11-01', '2023-01-01'),
        'phase_I' : ('2021-11-01', '2022-02-23'),
        'phase_II' : ('2022-02-24', '2022-04-01'),
        'phase_III' : ('2022-04-02', '2023-01-01')
    },
    'COVID' : {
        'full_period' : ('2019-12-31', '2022-01-01'),
        'phase_I' : ('2019-12-31', '2020-02-29'),
        'phase_II' : ('2020-03-01', '2020-12-31'),
        'phase_III' : ('2021-01-01', '2021-12-31')
    },
    'ESDC' : {
        'full_period' : ('2009-10-01', '2013-01-01'),
        'phase_I' : ('2009-10-01', '2010-03-31'),
        'phase_II' : ('2010-04-01', '2011-12-31'),
        'phase_III' : ('2012-01-01', '2013-01-01')
    },
    'GFC' : {
        'full_period' : ('2007-01-01', '2010-01-01'),
        'phase_I' : ('2007-01-01', '2008-08-31'),
        'phase_II' : ('2008-09-01', '2009-03-31'),
        'phase_III' : ('2009-04-01', '2010-01-01')
    }
}


period_mapping_df = pd.DataFrame(period_mapping).T.reset_index().melt(id_vars=['index'], 
                                                  var_name='phase', 
                                                  value_name='period_range'
                                                ).rename(columns={'index': 'period'})


period_mapping_df[['period_start', 'period_end']] = period_mapping_df['period_range'].to_list()
period_mapping_df[['period_start', 'period_end']] = period_mapping_df[['period_start', 'period_end']].map(pd.to_datetime)
