# NOTE: Methods for handling & loading data
# NOTE: used for loading data & metadata mapping

import os
import numpy as np
import pandas as pd




def select_period(data, period):
    return data.query(f"period == '{period}'")


def select_phase(data, phase='full_period'):
    return data.query(f"phase == '{phase}'")


def map_metadata(data, metadata=None):
    if metadata is None:
        return data

    #df_1 = pd.merge(data, metadata, left_on='index', right_on='name')
    # df_2 = pd.merge(data, metadata, left_on='asset', right_on='name', suffixes=('_benchmark', '_candidate'))

    # NOTE: adding metadata of benchmark
    df_1 = pd.merge(data, metadata, left_on='index', right_on='name', how='left', suffixes=('', '_benchmark'))

    # NOTE: adding metadata of candidate
    df_2 = pd.merge(df_1, metadata, left_on='asset', right_on='name', how='left', suffixes=('', '_candidate'))

    return df_2


def map_period_timestamps(data, metadata, how='left'):
    df_1 = pd.merge(data, metadata, on=['period', 'phase'], how=how)
    return df_1


def load_period(input_dir, period_dir, metadata):
    dfs = []
    for file in os.listdir(input_dir + period_dir):
        metadata_2 = file.split('__')
        df = pd.read_csv(input_dir + period_dir + file)

        #print(df.shape)

        df_mapped = map_metadata(df, metadata)

        df_mapped['selection'] = metadata_2[0]
        df_mapped['period'] = metadata_2[1]
        df_mapped['phase'] = metadata_2[2]
        df_mapped['source'] = input_dir + period_dir
        df_mapped['file'] = file

        dfs.append(df_mapped)

    try:
        return pd.concat(dfs, ignore_index=True)
    except:
        return pd.DataFrame()


def full_data_load(input_dir, metadata):
    periods = []
    for file in os.listdir(input_dir):
        if os.path.isdir(input_dir + file):
            period = load_period(input_dir, file + '/', metadata)
            periods.append(period)

    return pd.concat(periods)

