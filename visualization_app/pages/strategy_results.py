from dash import html, dcc, callback, Input, Output
import dash
import dash_bootstrap_components as dbc
from components.strategy_page_components import content_explanation, stats_table
import pandas as pd
import plotly.express as px


dash.register_page(__name__)

spx_d_df = pd.read_csv("./backtester_logic/data/spx_d.csv")
spx_d_df['Close'] = spx_d_df['Close'] * (100_000 / 91.15)
spx_d_df['Date'] = pd.to_datetime(spx_d_df['Date'], format='%m/%d/%Y')

equity_df = pd.read_csv("./backtester_logic/equity.csv")
equity_df['Date'] = pd.to_datetime(
    equity_df['Date'], format='%Y%m%d')

# Create a line chart using Plotly Express
fig = px.line(spx_d_df, x='Date', y='Close', title='Line Chart', log_y=True)
fig.add_trace(px.line(equity_df, x='Date', y='Equity',
              color_discrete_sequence=['red'], log_y=True).data[0])

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
                        [dcc.Graph(figure=fig)],
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
