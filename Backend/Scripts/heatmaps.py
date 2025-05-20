# NOTE: Heatmap analyza skripty

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from data import select_period, select_phase
except ModuleNotFoundError:
    from Scripts.PROD.data import select_period, select_phase


# THESIS

def select_pair_pivot(data, benchmark, candidate):
    return data.query(f'index == "{benchmark}" and asset == "{candidate}"').pivot(index='tau1', columns='tau2', values='cq')


def create_heatmap(data, X, Y, cmap='coolwarm', **kwargs):
    target = select_pair_pivot(data, X, Y).T.sort_index(ascending=False)
    sns.heatmap(target, cmap=cmap, **kwargs)


def create_heatmaps(data, period, phase, candidate=None,
                    row_count=4, figsize=(6, 5), hspace=0.4, wspace=0.4, **kwargs):

    if candidate is None:
        candidate = data['asset'].unique()[0]

    assets = data['index'].unique()
    assets = assets[assets != candidate]
    asset_count = len(assets)

    subset = (
        data.pipe(select_period, period)
        .pipe(select_phase, phase)
    )

    column_count = asset_count // row_count
    if asset_count % row_count != 0:
        column_count += 1

    fig, axs = plt.subplots(column_count, row_count, figsize=figsize)
    axs = axs.flatten()

    for i, ax in enumerate(axs):
        try:
            create_heatmap(subset, X=assets[i], Y=candidate, ax=axs[i], **kwargs)
            ax.set_title(f'{assets[i]} | {candidate}')
        except IndexError:
            ax.axis('off')

    fig.subplots_adjust(hspace=hspace, wspace=wspace)

    return fig, axs


def create_candidate_heatmaps(data, period, phase, benchmark=None,
                    row_count=4, figsize=(6, 5), hspace=0.4, wspace=0.4, **kwargs):

    if benchmark is None:
        benchmark = data['asset'].unique()[0]

    assets = data['asset'].unique()
    assets = assets[assets != benchmark]
    asset_count = len(assets)

    subset = (
        data.pipe(select_period, period)
        .pipe(select_phase, phase)
    )

    column_count = asset_count // row_count
    if asset_count % row_count != 0:
        column_count += 1

    fig, axs = plt.subplots(column_count, row_count, figsize=figsize)
    axs = axs.flatten()

    for i, ax in enumerate(axs):
        try:
            create_heatmap(subset, X=benchmark, Y=assets[i], ax=axs[i], **kwargs)
            ax.set_title(f'{benchmark} | {assets[i]}')
        except IndexError:
            ax.axis('off')

    fig.subplots_adjust(hspace=hspace, wspace=wspace)

    return fig, axs


# same config -> multiple crises

def create_config_periods_heatmaps(data, phase, benchmark, candidate, figsize=[6.4, 4.8], **kwargs):
    
    subset = (
        data.pipe(select_phase, phase)
    )

    fig, axs = plt.subplots(2, 2, figsize=figsize)
    axs = axs.flatten()

    crisis_order = ['GFC', 'ESDC', 'COVID', 'UA']
    
    for i, ax in enumerate(axs):
        crisis = crisis_order[i]

        subset2 = select_period(subset, period=crisis)
        create_heatmap(subset2, benchmark, candidate, ax=ax, **kwargs)

        ax.set_title(f"{crisis} ({subset2['period_start'].unique()[0]} - {subset2['period_end'].unique()[0]})")

    return fig, axs

# APPLICATION





