# NOTE: JSON API request template:
# Processed by cqgram to create cq data

request = {
    'source' : 'Yahoo',

    'content' : {
        'output_params' : {
            'output_dir' : None,
            'output_file' : None,
            'save_file' : True
        },

        'source_params' : {
            'start' : None,
            'end' : None,
        },

        'cqgram_params' : {
            'tau1_list' : [],
            'tau2_list' : [],
        },

        'tickers' : {
            # NOTE:
            # pass key, value pairs of assets, tickers HERE
            # manual or replaced with generated JSON
        }
    }
}


# NOTE: list of supported data sources (built-in):

# Yahoo:    YES
# Polygon:  NO                 
# EODH:     NO