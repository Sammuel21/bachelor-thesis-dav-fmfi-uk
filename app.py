# NOTE: App file:
# runs Shiny for Python web application
# data visualization

# NOTE: LOCAL RUN
# for API request based runs redirect to ./API/

from functools import partial
from shiny import reactive, render
from shiny.express import ui
from shiny.express import input, render, session
from shiny.ui import page_navbar
from shinywidgets import render_plotly, render_widget, output_widget

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.dont_write_bytecode = True
here = os.path.dirname(os.path.abspath(__file__))
sys.path.append(here)

from Frontend.Config.config import *
from Frontend.Config.constants import *
from Frontend.Scripts.heatmaps import *
from Frontend.Scripts.networks import *
from Frontend.Scripts.data import *


# data load

data = pd.read_csv(CQ_DATA_DIR_PATH + '/' + CQ_DATA_FILE_PATH)
custom_data = pd.read_csv('./Data/CQ/Tests/api_test.csv')

available_data_files = os.listdir(CQ_DATA_DIR_PATH)
available_custom_data_files = os.listdir('./Data/CQ/Tests/')

if not available_custom_data_files:
    available_custom_data_files = ['-']

# APPLICATION PART

# SETTINGS

ui.page_opts(
    title = 'Conectedness between assets |',
    page_fn = partial(page_navbar, id='page'),
    fillable=True
)


# LAYOUT

with ui.nav_panel('Heatmaps'):
    ui.h4('Heatmap content area.')
    with ui.layout_sidebar(fillable=True):
        with ui.sidebar():
            ui.h4('Heatmaps Configuration:')
            ui.input_select('data_heatmaps', 'Data:', choices=available_data_files, selected=available_data_files[0])
            ui.input_select('period_heatmaps', 'Period:', choices=CRISES, selected=CRISES[0])
            ui.input_select('phase_heatmaps', 'Phase:', choices=PHASES, selected=PHASES[0])
            ui.input_select('asset_heatmaps', 'Asset:', choices=ALL_ASSETS, selected=ALL_ASSETS[0])
            ui.input_radio_buttons(
                'radio_type_heatmaps',
                'Type:',
                choices={
                    '1' : 'Benchmark candidates',
                    '2' : 'Candidate potential'
                },
                selected='1'
            )
            ui.input_radio_buttons(
                'radio_markets_only_heatmaps',
                'Markets only:',
                choices={
                    '1' : 'No',
                    '2' : 'Yes'
                },
                selected='1'
            )
            ui.h5('Styling configuration:')

            ui.input_slider('slider_heatmaps', 'Heatmap range:', 0, 1, 0.4, step=0.1)
            ui.input_select('cmap_heatmaps', 'Heatmap colormap:', choices=CMAPS, selected='rdbu')
            ui.input_select('cmap_reverse_heatmaps', 'Reversed colormap:', choices=['True', 'False'], selected='True')

        ui.tags.style("""
            #heatmaps_card {
                height: 75vh !important;
            }
            #heatmaps_card .plotly.html-widget {
                width: 100% !important;
                height: 100% !important;
            }
        """)

        with ui.card(fill=True, idd='heatmaps_card'):
            @render_plotly
            def plot_heatmaps():
                subset = filter_data_heatmaps()
                
                period = input.period_heatmaps()
                phase = input.phase_heatmaps()
                heatmap_range = input.slider_heatmaps()
                cmap = input.cmap_heatmaps()
                cmap_reversed = input.cmap_reverse_heatmaps().lower() == 'true'

                # NOTE: backend mapping
                period = PERIOD_BACKEND_MAPPING.get(period, '')
                phase = PHASE_BACKEND_MAPPING.get(phase, '')
                reverse_cmap = False

                if cmap_reversed:
                    reverse_cmap = True

                Y = input.asset_heatmaps()
                
                if input.radio_type_heatmaps() == '1':
                    fig = create_heatmaps_plotly(
                        data=subset,
                        period=period,
                        phase=phase,
                        candidate=Y,
                        row_count=4,
                        figsize=None,
                        cmap=cmap,
                        zmin=-heatmap_range,
                        zmax=heatmap_range,
                        reversescale=reverse_cmap
                    )
                else:
                    fig = create_candidate_heatmaps_plotly(
                        data=subset,
                        period=period,
                        phase=phase,
                        benchmark=Y,
                        row_count=4,
                        cmap=cmap,
                        zmin=-heatmap_range,
                        zmax=heatmap_range,
                        reversescale=reverse_cmap
                    )

                fig.update_layout(
                    autosize=True,
                    height=1000,
                    width=1200,
                    margin = dict(
                        l = 40,
                        r = 80,
                        t = 80,
                        b = 40
                    )
                )

                return fig
            
                

with ui.nav_panel('Networks'):
    with ui.layout_sidebar(fillable=True):
        with ui.sidebar():
            ui.h4('Network Configuration:')
            ui.input_select('data_network', 'Data:', choices=available_data_files, selected=available_data_files[0])
            ui.input_select('period_network', 'Period:', choices=CRISES, selected=CRISES[0])
            ui.input_select('phase_network', 'Phase:', choices=PHASES, selected=PHASES[0])
            ui.input_select('tau_x_network', 'Tau X:', choices=TAU_SPECTRUM, selected=TAU_SPECTRUM[0])
            ui.input_select('tau_y_network', 'Tau Y:', choices=TAU_SPECTRUM, selected=TAU_SPECTRUM[-1])

        #with ui.card(fill=True, idd='network_card'):
        @render.ui
        def network_visualization():
            subset = filter_data_networks()
            G = create_network(subset)
            G = decorate_for_pyvis(G)
            net = show_pyvis(G)
            
            return ui.HTML(net.generate_html(notebook=False))


# ================================= CUSTOM

with ui.nav_panel('Custom Networks'):
    with ui.layout_sidebar(fillable=True):
        with ui.sidebar():
            ui.h4('Custom Network Configuration:')
            ui.input_select('data_custom_network', 'Data:', choices=available_custom_data_files, selected=available_data_files[0])
            ui.input_select('start_custom_network', 'Start:', choices=CRISES, selected=CRISES[0])
            ui.input_select('end_custom_network', 'End:', choices=PHASES, selected=PHASES[0])
            ui.input_select('tau_x_custom_network', 'Tau X:', choices=TAU_SPECTRUM, selected=TAU_SPECTRUM[0])
            ui.input_select('tau_y_custom_network', 'Tau Y:', choices=TAU_SPECTRUM, selected=TAU_SPECTRUM[-1])

        #with ui.card(fill=True, idd='network_card'):
        @render.ui
        def network_visualization_custom():
            subset = filter_data_networks_custom()
            G = create_network(subset)
            G = decorate_for_pyvis(G)
            net = show_pyvis(G)
            
            return ui.HTML(net.generate_html(notebook=False))


# NOTE: Reactive funckie -> SERVER BACKEND

def reload_data(file):
    global data
    try:
        data = pd.read_csv(file)
    except:
        pass

def reload_custom_data(file):
    global custom_data
    try:
        custom_data = pd.read_csv(file)
    except:
        pass


# SUMMARY PAGE

# HEATMAPS PAGE

@reactive.calc
def filter_data_heatmaps():

    data_file = input.data_heatmaps()
    period = input.period_heatmaps()
    phase = input.phase_heatmaps()

    # BUG: FIXED: period, phase -> mappin[period], mapping[phase]
    #print("Reaction")
    #print(period, phase)

    reload_data(CQ_DATA_DIR_PATH + data_file)

    period = PERIOD_BACKEND_MAPPING.get(period, '')
    phase = PHASE_BACKEND_MAPPING.get(phase, '')

    subset = (
        data.pipe(select_period, period)
        .pipe(select_phase, phase)
    )

    if input.radio_markets_only_heatmaps() == '2':
        subset = subset.query(f'name_benchmark in ({MARKETS})')

    return subset


# NETWORKS PAGE

@reactive.calc
def filter_data_networks():

    data_file = input.data_network()
    period = input.period_network()
    phase = input.phase_network()

    tau1 = float(input.tau_x_network())
    tau2 = float(input.tau_y_network())

    reload_data(CQ_DATA_DIR_PATH + data_file)

    period = PERIOD_BACKEND_MAPPING.get(period, '')
    phase = PHASE_BACKEND_MAPPING.get(phase, '')

    subset = (
        data.pipe(select_period, period)
        .pipe(select_phase, phase)
    )

    subset = subset.query('tau1 == @tau1 and tau2 in (@tau1, @tau2)')

    return subset


@reactive.calc
def filter_data_networks_custom():

    data_file = input.data_custom_network()

    tau1 = float(input.tau_x_custom_network())
    tau2 = float(input.tau_y_custom_network())

    reload_custom_data(CQ_DATA_DIR_PATH + data_file)

    subset = custom_data

    subset = subset.query('tau1 == @tau1 and tau2 in (@tau1, @tau2)')

    return subset



# PORTTFOLIO API PAGE


