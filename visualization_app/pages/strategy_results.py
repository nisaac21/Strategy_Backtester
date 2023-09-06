from dash import html, dcc, callback, Input, Output, State
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3

from components.strategy_page_components import content_explanation, initial_stats_table, initial_performance_graph, create_stats_table, create_performance_graph
from components.utils import _get_statistics, _strategy_table_convention
from components.const import INTIAL_CAPITAL, DATABASE_PATH

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
                        [dcc.Graph(id='performance_graph',
                                   figure=initial_performance_graph)],
                        style={'margin': '25px'},
                        id='performance_graph_row'
                    ),

                    # Statistics Card
                    dbc.Row(
                        [dbc.Card(
                            dbc.CardBody(
                                id='stats_table',
                                children=initial_stats_table
                            ),
                            id='stats_card'
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
    Output(component_id='performance_graph', component_property='figure'),
    Output(component_id='stats_table', component_property='children'),
    Input(component_id='strategy_button', component_property='n_clicks'),
    State(component_id='look_back', component_property='value'),
    State(component_id='lottery_window', component_property='value'),
    State(component_id='rebalnce_period', component_property='value'),
    State(component_id='firms_held', component_property='value')
)
def update_performance(n_clicks, look_back, lottery_window, rebalnce_period, firms_held):
    conn = sqlite3.connect(DATABASE_PATH)

    equity_df = pd.read_sql(
        f"""SELECT * FROM {_strategy_table_convention(
            look_back=look_back,
            lottery_window=lottery_window,
            rebalance=rebalnce_period,
            firms_held=firms_held
        )}""",
        con=conn
    )

    equity_stats = _get_statistics(equity_df, INTIAL_CAPITAL)

    return create_performance_graph(equity_df), create_stats_table(equity_stats)
