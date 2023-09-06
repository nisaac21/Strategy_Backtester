import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import plotly.express as px
from components.utils import _get_statistics, _strategy_table_convention
from components.const import INTIAL_CAPITAL, DATABASE_PATH
import sqlite3

conn = sqlite3.connect(DATABASE_PATH)

spx_d_df = pd.read_sql("SELECT * FROM SPX_DAILY", con=conn)

equity_df = pd.read_sql(
    f"""SELECT * FROM {_strategy_table_convention(
            look_back=12,
            lottery_window=12,
            rebalance=3,
            firms_held=50
        )}""",
    con=conn
)

spx_stats = _get_statistics(spx_d_df, INTIAL_CAPITAL)
equity_stats = _get_statistics(equity_df, INTIAL_CAPITAL)

"""
    Strategy Used and Backtesting Process Card
    ------------------------------------------
"""


def _create_options(options: list, name: str, unit: str):
    return [
        {'label': f'{name} {value} {unit}', 'value': value} for value in options
    ]


def _create_tab(card_body, tab_label: str) -> dbc.Tab:
    """Creates a dash bootstrap component Tab """

    return dbc.Tab(
        dbc.Card(
            dbc.CardBody(
                card_body
            ),
            class_name='mt-3'
        ),
        label=tab_label)


about_cardbody = [dcc.Markdown(open(
    'visualization_app/components/project_summary.txt', "r").read())]

select_style = {'maxWidth': '300px'}

strategy_cardbody = [

    html.Center(
        [dbc.Select(id='look_back', placeholder='Look Back Window', options=_create_options(
            [12, 36, 60], 'Look Back Window:', 'Months'), style=select_style),
         html.Br(),
         dbc.Select(id='lottery_window', placeholder='Lottery Window', options=_create_options(
             [1, 3, 6, 12], 'Lottery Window:', 'Months'), style=select_style),
         html.Br(),
         dbc.Select(id='rebalnce_period', placeholder='Rebalance Period', options=_create_options(
             [1, 3, 6, 12], 'Rebalance Every:', 'Months'), style=select_style),
         html.Br(),
         dbc.Select(id='firms_held', placeholder='Firms Held', options=_create_options(
             [25, 50, 100, 200], 'Hold:', 'Firms'), style=select_style),
         html.Br(),
         dbc.Button("Visualize Strategy", id='strategy_button'),
         html.Div(id='my-output')]
    )
]

content_explanation = dbc.Tabs(
    [
        _create_tab(about_cardbody, "About"),
        _create_tab(strategy_cardbody, "Strategy"),
    ]
)

"""
    Perormance Visualization
    -------------------------
"""

spx_d_df['Date'] = pd.to_datetime(spx_d_df['Date'], format='%Y%m%d')


def create_performance_graph(equity_df):
    equity_df['Date'] = pd.to_datetime(
        equity_df['Date'], format='%Y%m%d')

    # Lime chart with plotlhy express
    performance_graph = px.line(spx_d_df, x='Date', y='Equity',
                                title='Performance comparison', log_y=True)

    performance_graph.add_trace(px.line(equity_df, x='Date', y='Equity',
                                        color_discrete_sequence=['red'], log_y=True).data[0])

    return performance_graph


initial_performance_graph = create_performance_graph(equity_df)

"""
    Performance Statics Table
    -------------------------
"""

table_header = [
    html.Thead(html.Tr([html.Th(""), html.Th(
        "Strategy Performance"), html.Th("Benchmark Performance")]))
]

statistics = [
    'Overall Return',
    'CAGR',
    'Standard Deviation',
    'Downside Deviation',
    'Sharpe Ratio',
    # 'Sortino Ratio',
    'Max Drawdown',
    'Worst Month Return',
    'Best Month Return',
    'Profitable Months'
]

table_body = [html.Tbody(
    [html.Tr([html.Td(statistic), html.Td(equity_stats[statistic]), html.Td(spx_stats[statistic])]) for statistic in statistics])]


def create_stats_table(equity_stats):

    statistics = [
        'Overall Return',
        'CAGR',
        'Standard Deviation',
        'Downside Deviation',
        'Sharpe Ratio',
        # 'Sortino Ratio',
        'Max Drawdown',
        'Worst Month Return',
        'Best Month Return',
        'Profitable Months'
    ]

    table_body = [html.Tbody(
        [html.Tr([html.Td(statistic), html.Td(equity_stats[statistic]), html.Td(spx_stats[statistic])]) for statistic in statistics])]

    stats_table = dbc.Table(table_header + table_body, bordered=True)

    return stats_table


initial_stats_table = create_stats_table(equity_stats)
