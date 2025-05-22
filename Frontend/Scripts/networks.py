# Networks page code

import numpy as np
import pandas as pd
import networkx as nx
import json
import matplotlib.colors as mcolors
from pyvis.network import Network



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


def create_network(subset):
    return create_nx_network(subset)


def css(col_name):
    """Return a hex string vis.js understands."""
    try:                       
        return mcolors.to_hex(col_name)
    except ValueError:
        return col_name 


def decorate_for_pyvis(G, rad=0.30):
    
    neg_edges = [(u, v) for u, v, d in G.edges(data=True) if d['cq'] < 0]
    pos_edges = [(u, v) for u, v, d in G.edges(data=True) if d['cq'] > 0]
    G_neg, G_pos = G.edge_subgraph(neg_edges), G.edge_subgraph(pos_edges)

    top_receiver = lambda g: max(g.in_degree,  key=lambda x: x[1])[0] if g.number_of_edges() else None
    top_emitter  = lambda g: max(g.out_degree, key=lambda x: x[1])[0] if g.number_of_edges() else None
    tr_neg, te_neg = top_receiver(G_neg), top_emitter(G_neg)
    tr_pos, te_pos = top_receiver(G_pos), top_emitter(G_pos)

    in_deg  = dict(G.in_degree())
    out_deg = dict(G.out_degree())
    total   = {n: in_deg[n] + out_deg[n] for n in G.nodes()}
    maxdeg  = max(total.values()) or 1
    scale   = lambda d: 20 + (60-20) * d / maxdeg

    clr_neg = ('mediumpurple', 'lightgreen')
    clr_pos = ('indianred',   'salmon')

    for n in G.nodes():
        col = 'tab:blue'

        if n == tr_neg:      col = clr_neg[0]
        elif n == te_neg:    col = clr_neg[1]
        elif n == tr_pos:    col = clr_pos[0]
        elif n == te_pos:    col = clr_pos[1]
        elif n == 'Gold Futures':
            col = 'goldenrod'

        G.nodes[n]['color'] = css(col)
        G.nodes[n]['size']  = scale(total[n])
        G.nodes[n]['label'] = n          
    
    for u, v, d in G.edges(data=True):
        d['color'] = css('green' if d['cq'] < 0 else 'red')
        d['value'] = np.log1p(abs(d['cq']))
        d['title'] = f"cq={d['cq']:.3f} tau1={d['tau1']}, tau2={d['tau2']}"
   
    pos = nx.circular_layout(G)
    for n, (x, y) in pos.items():
        G.nodes[n]['x'] = float(x*1000)
        G.nodes[n]['y'] = float(y*1000)
        G.nodes[n]['fixed'] = {'x':True, 'y':True}

    G.graph['rad'] = rad
    return G




def show_pyvis(G, height="750px", width="100%"):
    net = Network(height=height, width=width, directed=True, cdn_resources="in_line")
    net.from_nx(G)                              
    rad = G.graph.get('rad', 0.3)
    options = {
        "physics": {"enabled": False},
        "edges":   {"smooth": {"type": "curvedCW", "roundness": rad}},
        "nodes": {
            "shadow": False,
            "font": {                 
                "size": 26,           
                "face": "Arial",
                "bold": {"mod": "bold"}   
            },
            "scaling": {           
                "label": {"enabled": True, "min": 14, "max": 40}
            }
        }
    }

    net.set_options(json.dumps(options))
    

    return net





