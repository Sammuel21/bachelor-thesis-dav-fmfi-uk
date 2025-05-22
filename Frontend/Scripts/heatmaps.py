# Plotly Integration Heatmaps -> Shiny App
import os
import sys

sys.dont_write_bytecode = True
import dotenv
dotenv.load_dotenv()
sys.path.append(os.getenv('PROJECT_PATH'))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objs import FigureWidget

from Frontend.Scripts.data import *

try:
    from data import select_period, select_phase
    from Config.config import *
except ModuleNotFoundError:
    pass



def select_pair_pivot(data, benchmark, asset):
    return data.query(f'index == "{benchmark}" and asset == "{asset}"').pivot(index='tau1', columns='tau2', values='cq')


def create_heatmap_plotly(fig, data, X, Y, cmap='RdBu', row=1, col=1, **kwargs):
    target = select_pair_pivot(data, X, Y).T.sort_index(ascending=True)
    heatmap = go.Heatmap(
        z = target.values,
        x = [str(tau) for tau in target.columns],
        y = [str(tau) for tau in target.index],
        colorscale = cmap,
        **kwargs
    )

    fig.add_trace(heatmap, row=row, col=col)
    fig.update_xaxes(title_text='tau1', row=row, col=col)
    fig.update_yaxes(title_text='tau2', row=row, col=col)


def create_heatmaps_plotly(data, period, phase, candidate=None, row_count=4, figsize=(800, 600), hspace=0.1, wspace=0.1, cmap='RdBu', **kwargs):
    
    if candidate is None:
        candidate = data['asset'].unique()[0]

    assets = data['index'].unique()
    assets = assets[assets != candidate]
    asset_count = len(assets)

    subset = (
        data.pipe(select_period, period)
        .pipe(select_phase, phase)
    )

    cols = row_count
    rows = asset_count // cols

    if asset_count % row_count != 0:
        rows += 1

    titles = [f'{assets[i]} | {candidate}' for i in range(asset_count)]

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=titles,
        horizontal_spacing=hspace,
        vertical_spacing=wspace
    )

    '''
    fig.update_layout(
        xaxis=dict(constrain='domain'),
        yaxis=dict(scaleanchor='x', scaleratio=1)
    )
    '''

    for i, asset in enumerate(assets):
        row = i // cols + 1
        col = i % cols + 1

        if asset != candidate:
            create_heatmap_plotly(fig, subset, X=asset, Y=candidate, row=row, col=col, cmap=cmap, **kwargs)


    return fig


def create_candidate_heatmaps_plotly(data, period, phase, benchmark=None, row_count=4, hspace=0.1, wspace=0.1, cmap='RdBu', **kwargs):

    if benchmark is None:
        benchmark = data['index'].unique()[0]

    assets = data['asset'].unique()
    assets = assets[assets != benchmark]
    asset_count = len(assets)

    subset = (
        data.pipe(select_period, period)
        .pipe(select_phase, phase)
    )

    cols = row_count
    rows = asset_count // cols

    if asset_count % row_count != 0:
        rows += 1

    titles = [f'{benchmark} | {assets[i]}' for i in range(asset_count)]

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=titles,
        horizontal_spacing=hspace,
        vertical_spacing=wspace
    )

    for i, asset in enumerate(assets):
        row = i // cols + 1
        col = i % cols + 1

        if asset != benchmark:
            create_heatmap_plotly(fig, subset, X=benchmark, Y=asset, row=row, col=col, cmap=cmap, **kwargs)

    return fig