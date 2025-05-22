# NOTE: Frontend App architecture

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

from Config.config import *
from Config.constants import *
from Scripts.heatmaps import *
from Scripts.networks import *


# NOTE: DO NOT USE !!! -> WIP: use app.py


# Data load
# NOTE: in app.py -> frontend main file

# Architecture

class ShinyApp:
    
    def __init__(self):
        ui.page_opts(
            title = 'Conectedness between assets |',
            page_fn = partial(page_navbar, id='page'),
            fillable=True
        )

        self.data = None


    def load_data(self, file_path=None, db=None):
        # NOTE: db architecture not yet supported
        if file_path is not None:
            self.data = pd.read_csv(file_path)


    def run(self):
        with ui.nav_panel('Summary'):
            with ui.layout_sidebar():
                with ui.sidebar():
                    ui.h4('Summary Configuration:')
                    ui.input_select('period_summary', 'Period:', choices=CRISES, selected='Ukraine War 2022')
                    ui.input_select('phase_summary', 'Phase:', choices=PHASES, selected='Full period')

                ui.h4('MAIN')


        with ui.nav_panel('Heatmaps'):
            ui.h4('Heatmap content area.')
            with ui.layout_sidebar(fillable=True):
                with ui.sidebar():
                    ui.h4('Heatmaps Configuration:')
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
                    ui.input_select('period_network', 'Period:', choices=CRISES, selected=CRISES[0])
                    ui.input_select('phase_network', 'Phase:', choices=PHASES, selected=PHASES[0])
                    ui.input_select('tau_x_network', 'Tau X:', choices=TAU_SPECTRUM, selected=TAU_SPECTRUM[0])
                    ui.input_select('tau_y_network', 'Tau Y:', choices=TAU_SPECTRUM, selected=TAU_SPECTRUM[-1])

                with ui.card(fill=True, idd='network_card'):
                    @render.ui
                    def network_visualization():
                        subset = filter_data_networks()
                        G = create_network(subset)
                        G = decorate_for_pyvis(G)
                        net = show_pyvis(G)
                        
                        return ui.HTML(net.generate_html(notebook=False))


        with ui.nav_panel('Markets'):
            pass


        with ui.nav_panel('Portfolio API'):
            ui.h4('Portfolio API App.')


        with ui.nav_panel('Info'):
            pass

        

        # ---
        # BACKEND CALCS
        # HEATMAPS PAGE

        @reactive.calc
        def filter_data_heatmaps():

            period = input.period_heatmaps()
            phase = input.phase_heatmaps()

            # BUG: FIXED: period, phase -> mappin[period], mapping[phase]
            #print("Reaction")
            #print(period, phase)

            period = PERIOD_BACKEND_MAPPING.get(period, '')
            phase = PHASE_BACKEND_MAPPING.get(phase, '')

            subset = (
                self.data.pipe(select_period, period)
                .pipe(select_phase, phase)
            )

            if input.radio_markets_only_heatmaps() == '2':
                subset = subset.query(f'name_benchmark in ({MARKETS})')

            return subset


        # NETWORKS PAGE

        @reactive.calc
        def filter_data_networks():

            period = input.period_network()
            phase = input.phase_network()

            tau1 = float(input.tau_x_network())
            tau2 = float(input.tau_y_network())

            period = PERIOD_BACKEND_MAPPING.get(period, '')
            phase = PHASE_BACKEND_MAPPING.get(phase, '')

            subset = (
                self.data.pipe(select_period, period)
                .pipe(select_phase, phase)
            )

            subset = subset.query('tau1 == @tau1 and tau2 in (@tau1, @tau2)')

            return subset