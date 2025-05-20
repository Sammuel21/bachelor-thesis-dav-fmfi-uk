# NOTE: Networks functions - visualization & topology

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from Scripts.PROD.constants import *


# NETWORKS


def select_data_subset(data, period, phase, tau1=None, tau2=None):
    copy = data.copy()
    if tau1 is not None:
        copy = copy.query(f'tau1 in ({tau1})')
    if tau2 is not None:
        copy = copy.query(f'tau2 in ({tau2})')
    return copy.query(f'period == "{period}" and phase == "{phase}"')


def create_nx_network(data, width_factor=1):
    import networkx as nx
    G = nx.DiGraph()
    nodes = set(data['index']) | set(data['asset'])
    G.add_nodes_from(nodes)
    for _, row in data.iterrows():
        if row['H0_rejected']:
            width = abs(row['cq']) * width_factor
            color = cq_to_color(row['cq'])
            G.add_edge(row['index'], row['asset'], cq=row['cq'], tau1=row['tau1'], tau2=row['tau2'], width=width, color=color)
    
    return G


# TOPOLOGY

def get_network_density(data, LOW=0.05, HIGH=0.95, include_spillover=False, return_pivot=True):
    node_count = data['index'].unique().shape[0]
    denominator = node_count * (node_count - 1)
    
    edge_subset = data.query(f'H0_rejected and tau1 in ({LOW},) and tau2 in ({LOW, HIGH})')
    
    grouping_cols = ['period', 'phase']
    if include_spillover:
        grouping_cols += ['spillover']
    grouping = edge_subset.groupby(grouping_cols)['cq'].count() / denominator

    if return_pivot:
        return grouping.reset_index().pivot(
            index=['phase', 'spillover'] if include_spillover else ['phase'],
            columns=['period'],
            values='cq'
        )

    return grouping.reset_index()


def get_network_density_FIXED(data, LOW=0.05, HIGH=0.95, include_spillover=False, return_pivot=True):
    grouping_cols = ["period", "phase"]
    if include_spillover:
        grouping_cols.append("spillover")

    allowed_tau2 = (LOW, HIGH)               # (0.05, 0.95)
    edge_subset = data.query(
        "H0_rejected and tau1 == @LOW and tau2 in @allowed_tau2"
    )

    edge_n = (
        edge_subset
        .groupby(grouping_cols, observed=True)
        .size()
        .rename("edge_n")
    )

    
    node_n = (
        data.groupby(grouping_cols, observed=True)["index"]
            .nunique()
            .rename("node_n")
    )

    
    dens = (
        pd.concat([edge_n, node_n], axis=1)         
          .fillna({"edge_n": 0})                   
          .assign(density=lambda d: d.edge_n / (d.node_n * (d.node_n - 1)))
          .reset_index()
    )

    if not return_pivot:
        return dens[grouping_cols + ["density"]]

    
    index_cols = ["phase", "spillover"] if include_spillover else ["phase"]
    return (
        dens.pivot(index=index_cols, columns="period", values="density")
            .rename_axis(index=None, columns=None)
    )



def compute_net_centralities_periods(data, phase):
    grouping = data.query(f'H0_rejected and phase == "{phase}"')
    grouping = grouping.query('spillover in ("Safe-Haven", "Contagion")')
    grouping = grouping.groupby(['period', 'phase'])

    res = []
    for group, df in grouping:
        period, phase = group

        G_group_sh = create_nx_network(df.query('spillover == "Safe-Haven"'))
        G_group_cn = create_nx_network(df.query('spillover == "Contagion"'))

        df_group = pd.DataFrame()
        df_group['safe_haven_in_deg_centrality'] = nx.in_degree_centrality(G_group_sh)
        df_group['contagion_in_deg_centrality']  = nx.in_degree_centrality(G_group_cn)
        df_group['safe_haven_out_deg_centrality'] = nx.out_degree_centrality(G_group_sh)
        df_group['contagion_out_deg_centrality'] = nx.out_degree_centrality(G_group_cn)

        df_group['net_in_deg_centrality'] = df_group['safe_haven_in_deg_centrality'] - df_group['contagion_in_deg_centrality']
        df_group['net_out_deg_centrality'] = df_group['safe_haven_out_deg_centrality'] - df_group['contagion_out_deg_centrality']

        df_group[['period', 'phase']] = period, phase
        
        res.append(df_group)

    df_res = pd.concat(res)

    output = df_res.reset_index().query('phase == "full_period"').pivot(
        index='index',
        columns=['period', 'phase'],
        values = ['net_in_deg_centrality', 'net_out_deg_centrality']
    )

    return output.reindex(columns=CRISIS_ORDER_COLUMNS, level=1).round(3).fillna('')


def compute_topology_summary_table(data, all_phases=False, **kwargs):

    tau_x = kwargs.get('tau1', 0.05)
    tau_y = kwargs.get('tau2', 0.95)
    market_benchmarks = kwargs.get('market_benchmarks', False)
    
    phase = kwargs.get('phase', 'full_period')

    TARGET_ASSET = kwargs.get('target_asset', None)

    TAU_1 = [tau_x]
    TAU_2 = [tau_x, tau_y]

    normalize = kwargs.get('normalize', True)

    assets = data['index'].unique()
    n = len(assets)
    norm = n - 1

    subset = data.query(f'tau1 in @TAU_1 and tau2 in @TAU_2')
    if market_benchmarks and MARKETS:
        subset =  subset.query(f'index in @MARKETS')

    if TARGET_ASSET:
        subset = subset.query('index == @TARGET_ASSET')

    grouping = subset.query('H0_rejected and spillover in ("Safe-Haven", "Contagion")').groupby(['period', 'phase'])
    res = []
    for group, df in grouping:
        group_period, group_phase = group
        G_group_sh = create_nx_network(df.query('spillover == "Safe-Haven"'))
        G_group_cn = create_nx_network(df.query('spillover == "Contagion"'))

        G_group_sh.add_nodes_from(assets)
        G_group_cn.add_nodes_from(assets)

        df_group = pd.DataFrame()

        # dynamicka norma -> nech normalizuje len poctom realnych assets
        if group_period in ['GFC', 'ESDC']:
            n = 15
        elif group_period in ['COVID', 'UA']:
            n = 17

        if normalize:
            norm = n - 1
        else:
            norm = 1

        # normalizovany objem
        df_group['in_deg_weight_norm_sh'] = pd.Series(dict(G_group_sh.in_degree(weight='cq'))) / norm
        df_group['in_deg_weight_norm_cn'] = pd.Series(dict(G_group_cn.in_degree(weight='cq'))) / norm

        df_group['net_in_deg_weight_norm'] = df_group['in_deg_weight_norm_sh'] + df_group['in_deg_weight_norm_cn']

        # in deg centralita
        df_group['in_deg_centrality_sh']  = pd.Series(nx.in_degree_centrality(G_group_sh))
        df_group['in_deg_centrality_cn']  = pd.Series(nx.in_degree_centrality(G_group_cn))

        df_group['net_in_deg_centrality'] = df_group['in_deg_centrality_sh'] - df_group['in_deg_centrality_cn']

        # metadata
        df_group[['period', 'phase']] = group_period, group_phase
        res.append(df_group)
    
    res = pd.concat(res)

    if all_phases:
        phases = ['full_period', 'phase_I', 'phase_II', 'phase_III']
    else:
        phases = [phase]

    output = res.reset_index().query(f'phase in @phases').pivot(
        index=['index'],
        columns=['period', 'phase'],
        values=['net_in_deg_weight_norm', 'net_in_deg_centrality']
    ).reindex(
        columns=CRISIS_ORDER_COLUMNS,
        level=1
    )

    #output = output.fillna(0)

    mean_weights = output['net_in_deg_weight_norm'].mean(axis=1, skipna=False)
    mean_centrality = output['net_in_deg_centrality'].mean(axis=1, skipna=False)

    output['weight_rank'] = mean_weights.rank(ascending=True, na_option='bottom', method='dense')
    output['centrality_rank'] = mean_centrality.rank(ascending=False, na_option='bottom', method='dense')

    return output.sort_values(by=['weight_rank', 'centrality_rank']).round(3).fillna('')



def compute_topology_summary_table_OUT_DEGREE(data, all_phases=False, **kwargs):

    tau_x = kwargs.get('tau1', 0.05)
    tau_y = kwargs.get('tau2', 0.95)
    market_benchmarks = kwargs.get('market_benchmarks', False)
    
    phase = kwargs.get('phase', 'full_period')

    TARGET_ASSET = kwargs.get('target_asset', None)

    TAU_1 = [tau_x]
    TAU_2 = [tau_x, tau_y]

    normalize = kwargs.get('normalize', True)

    assets = data['index'].unique()
    n = len(assets)
    norm = n - 1

    subset = data.query(f'tau1 in @TAU_1 and tau2 in @TAU_2')
    if market_benchmarks and MARKETS:
        subset =  subset.query(f'index in @MARKETS')

    if TARGET_ASSET:
        subset = subset.query('index == @TARGET_ASSET')

    grouping = subset.query('H0_rejected and spillover in ("Safe-Haven", "Contagion")').groupby(['period', 'phase'])
    res = []
    for group, df in grouping:
        group_period, group_phase = group
        G_group_sh = create_nx_network(df.query('spillover == "Safe-Haven"'))
        G_group_cn = create_nx_network(df.query('spillover == "Contagion"'))

        G_group_sh.add_nodes_from(assets)
        G_group_cn.add_nodes_from(assets)

        df_group = pd.DataFrame()

        # dynamicka norma -> nech normalizuje len poctom realnych assets
        if group_period in ['GFC', 'ESDC']:
            n = 15
        elif group_period in ['COVID', 'UA']:
            n = 17

        if normalize:
            norm = n - 1
        else:
            norm = 1

        # normalizovany objem
        df_group['out_deg_weight_norm_sh'] = pd.Series(dict(G_group_sh.out_degree(weight='cq'))) / norm
        df_group['out_deg_weight_norm_cn'] = pd.Series(dict(G_group_cn.out_degree(weight='cq'))) / norm

        df_group['net_out_deg_weight_norm'] = df_group['out_deg_weight_norm_sh'] + df_group['out_deg_weight_norm_cn']

        # in deg centralita
        df_group['out_deg_centrality_sh']  = pd.Series(nx.out_degree_centrality(G_group_sh))
        df_group['out_deg_centrality_cn']  = pd.Series(nx.out_degree_centrality(G_group_cn))

        df_group['net_out_deg_centrality'] = df_group['out_deg_centrality_sh'] - df_group['out_deg_centrality_cn']

        # metadata
        df_group[['period', 'phase']] = group_period, group_phase
        res.append(df_group)
    
    res = pd.concat(res)

    if all_phases:
        phases = ['full_period', 'phase_I', 'phase_II', 'phase_III']
    else:
        phases = [phase]

    output = res.reset_index().query(f'phase in @phases').pivot(
        index=['index'],
        columns=['period', 'phase'],
        values=['net_out_deg_weight_norm', 'net_out_deg_centrality']
    ).reindex(
        columns=CRISIS_ORDER_COLUMNS,
        level=1
    )

    #output = output.fillna(0)

    mean_weights = output['net_out_deg_weight_norm'].mean(axis=1, skipna=False)
    mean_centrality = output['net_out_deg_centrality'].mean(axis=1, skipna=False)

    output['weight_rank'] = mean_weights.rank(ascending=True, na_option='bottom', method='dense')
    output['centrality_rank'] = mean_centrality.rank(ascending=False, na_option='bottom', method='dense')

    return output.sort_values(by=['weight_rank', 'centrality_rank']).round(3).fillna('')








# VISUALIZATION


def cq_to_color(cq):
    mag = abs(cq)  # magnitude between 0 and 1
    if cq < 0:
        # Green: scale the green component from 0.5 (low intensity) to 1 (high intensity)
        return f'rgba(0, {int(255 * (0.5 + 0.5 * mag))}, 0, 1)'
    elif cq > 0:
        # Red: scale the red component from 0.5 (low intensity) to 1 (high intensity)
        return f'rgba({int(255 * (0.5 + 0.5 * mag))}, 0, 0, 1)'
    else:
        return 'gray'  # Neutral color for cq == 0


def plot_nx_network_circular(G, ax=None, title=None, legend=True, width=1, rad=0.3):


    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 10))


    neg_edges = [(u, v) for u, v, d in G.edges(data=True) if d['cq'] < 0]
    pos_edges = [(u, v) for u, v, d in G.edges(data=True) if d['cq'] > 0]
    G_neg = G.edge_subgraph(neg_edges).copy()
    G_pos = G.edge_subgraph(pos_edges).copy()

 
    def top_receiver(Gsub):
        return max(Gsub.in_degree, key=lambda x: x[1])[0] if Gsub.number_of_edges() else None
    def top_emitter(Gsub):
        return max(Gsub.out_degree, key=lambda x: x[1])[0] if Gsub.number_of_edges() else None

    tr_neg, te_neg = top_receiver(G_neg), top_emitter(G_neg)
    tr_pos, te_pos = top_receiver(G_pos), top_emitter(G_pos)


    in_deg  = dict(G.in_degree())
    out_deg = dict(G.out_degree())
    total_deg = {n: in_deg[n] + out_deg[n] for n in G.nodes()}
    max_deg = max(total_deg.values()) if total_deg else 1
    scale = lambda d: 300 + (1500 - 300) * d / max_deg
    node_sizes = [scale(total_deg[n]) for n in G.nodes()]


    clr_neg = ('mediumpurple', 'lightgreen')
    clr_pos = ('indianred', 'salmon')

    node_colors = []
    for n in G.nodes():
        if n == tr_neg:
            node_colors.append(clr_neg[0])
        elif n == te_neg:
            node_colors.append(clr_neg[1])
        elif n == tr_pos:
            node_colors.append(clr_pos[0])
        elif n == te_pos:
            node_colors.append(clr_pos[1])
        elif n == 'Gold Futures':
            node_colors.append('goldenrod')
        else:
            node_colors.append('tab:blue')


    widths = [np.log1p(abs(G[u][v]['cq'])) * width for u, v in G.edges()]
    edge_colors = ['green' if G[u][v]['cq'] < 0 else 'red' for u, v in G.edges()]

    nx.draw(
        G, ax=ax, pos=nx.circular_layout(G),
        width=widths, edge_color=edge_colors,
        node_size=node_sizes, node_color=node_colors,
        with_labels=True, connectionstyle=f'arc3,rad={rad}'
    )

    if legend:

        edge_legend = [
            Line2D([0], [0], color='green', lw=2, label='cq < 0  (Safe-Haven)'),
            Line2D([0], [0], color='red',   lw=2, label='cq > 0  (Contagion)')
        ]
        node_legend = [
            Patch(facecolor=clr_neg[0], label=f'Top receiver  (Negative): {tr_neg}'),
            Patch(facecolor=clr_neg[1], label=f'Top emitter   (Negative): {te_neg}'),
            Patch(facecolor=clr_pos[0], label=f'Top receiver  (Positive): {tr_pos}'),
            Patch(facecolor=clr_pos[1], label=f'Top emitter   (Positive): {te_pos}')
        ]

        ax.legend(handles=edge_legend + node_legend, loc='upper right', frameon=True)

    if title:
        ax.set_title(title)
    
    ax.axis('equal')




# SNAPSHOTY NETWORKOV


def draw_snapshot(data, period, phase, tau1, tau2, ax, width=1, rad=0.3, title=None, legend=False):
    subset = select_data_subset(data, period, phase, tau1, tau2)
    G = create_nx_network(subset)
    plot_nx_network_circular(G, ax=ax, title=title, width=width, rad=rad, legend=legend)



def plot_period_evolution(data, period, tau1, tau2, figsize=(20, 20), width=1, legend=False):
    phases = ['phase_I', 'phase_II', 'phase_III', 'full_period']

    fig, axs = plt.subplots(2, 2, figsize=figsize)
    axs = axs.flatten()

    for i, phase in enumerate(phases):
        draw_snapshot(data, period=period, phase=phases[i], tau1=tau1, tau2=tau2, ax=axs[i], title=phase, width=width, legend=legend)

    #fig.suptitle(f'Vývoj prepojenia aktív počas krízy ({period})')

    return fig, axs



def plot_periods(data, phase, tau1, tau2, width=1, figsize=(20, 20), legend=False):
    periods = ['GFC', 'ESDC', 'COVID', 'UA']

    fig, axs = plt.subplots(2, 2, figsize=figsize)
    axs = axs.flatten()

    for i, period in enumerate(periods):
        draw_snapshot(data, period, phase, tau1, tau2, ax=axs[i], width=width, legend=legend, title=period)

    #fig.suptitle(f'Vývoj prepojenia aktív naprieč krízami ({phase})')
    
    return fig, axs






































