from dash import html, dcc, callback, Input, Output
import dash
import dash_bootstrap_components as dbc
from components.strategy_page_components import content_explanation, stats_table, performance_graph
import pandas as pd
import plotly.express as px


dash.register_page(__name__)


"""
    App Layout
    ----------
"""
layout = html.Div([

    # Header
    html.Div(
        html.H1(children="Strategy Backtest Results",
                style={
                    'textAlign': 'center',
                    'margin': '25px'})
    ),

    # Body
    html.Div([
        # Wrapper
        dbc.Row(
            [

                # Cards explaining website purpose, etc
                dbc.Col(content_explanation),


                dbc.Col([
                    # Graph
                    dbc.Row(
                        [dcc.Graph(figure=performance_graph)],
                        style={'margin': '25px'}
                    ),

                    # Statistics Card
                    dbc.Row(
                        [dbc.Card(
                            dbc.CardBody(
                                stats_table
                            ),
                        )],
                        style={'margin': '25px'}
                    )
                ])
            ],

            style={
                'margin': '50px'
            }
        )
    ])

])


@callback(
    Output(component_id='my-output', component_property='children'),
    Input(component_id='strategy_button', component_property='n_clicks')
)
def update_output_div(input_value):
    return f'You Chose: {input_value}'
