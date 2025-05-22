# pipeline file
import os
import sys
import dotenv

dotenv.load_dotenv()
sys.dont_write_bytecode = True
PATH = os.getenv('PROJECT_PATH')
sys.path.append(PATH)

from Backend.Scripts.ETL.source_etl import *
from Backend.Scripts.ETL.data_source import *
from Backend.Scripts.ETL.cqgram_etl import *


def run_cq_pipeline(request):

    source_mapping = {
        'Yahoo' : Yahoo,
        'Polygon' : None,
        'EODHD' : None
    }

    source = source_mapping[request['source']](request['content']['tickers'])
    data = source.fetch_adjusted_data(**request['content']['source_params'])
    
    # NOTE: CQ pipeline

    cqgram = CQGramPipeline()
    cqgram.load_data(data)

    result = cqgram.compute_CQBS(**request['content']['cqgram_params'])

    # file writting

    output_params = request["content"].get("output_params", {})

    if output_params.pop('save_file', False):
        cqgram.save_results(**output_params)

    # ---

    try:
        response = {
            'status' : 'ok',
            'echo' : 'Run succesful.',
            'result' : serialise_result(result)
        }
    except Exception as e:
        response = {
            'status' : 'fail',
            'echo' : f'Run failed at exception: {e}'
        }

    return response


# Helper

def serialise_result(result: dict) -> dict:
    serialised = {}
    for key, value in result.items():
        key_str = "|".join(map(str, key))           
        if isinstance(value, str):                  
            serialised[key_str] = value
        else:                                  
            serialised[key_str] = value.to_dict("records")
    return serialised



