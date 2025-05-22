# NOTE: Test template for posting request to project API

import os
import sys
import json
import requests


request = {
    'source' : 'Yahoo',

    'content' : {
        'output_params' : {
            'output_dir' : 'Data/CQ/Tests/',
            'output_file' : 'api_test.csv',
            'save_file' : True
        },

        'source_params' : {
            'start' : '2021-11-01',
            'end' : '2023-01-01',
        },

        'cqgram_params' : {
            'tau1_list' : [0.05],
            'tau2_list' : [0.95],
        },

        'tickers' : {
            'S&P500' : '^GSPC',
            'Gold Futures' : 'GC=F'
        }
    }
}

resp = requests.post("http://127.0.0.1:8000/run",
                     headers={"Content-Type": "application/json"},
                     data=json.dumps(request))

print(resp.status_code, resp.json())