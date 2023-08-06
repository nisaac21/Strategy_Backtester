import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import plotly.express as px


"""
    Strategy Used and Backtesting Process Card
    ------------------------------------------
"""


def create_tab(markdown_text: str, tab_label: str) -> dbc.Tab:
    """Creates a dash bootstrap component Tab """

    return dbc.Tab(
        dbc.Card(
            dbc.CardBody(
                [
                    dcc.Markdown(markdown_text)
                ]
            ),
            class_name='mt-3'
        ),
        label=tab_label)


about_markdown_text = """
In order to test the viability of a Momentum Strategy, as described by Wesley R. Gray and 
Jack R. Vogel in their book 'Quantitative Momentum: A Practitioner's Guide to Building a Momentum-Based
Stock Selection System,' the following backtesting engine was developed. The backtester looks to test 
an intermediate based momentum strategy against decades of stock market data in order to get a sense of the 
performance potential of such a strategy. As noted by Michale L. Halls-Moore in 'Succesful Algorithmic Trading', 
a backtester must be wary of optimization bias, look-ahead bias, survivorship bias, and including market friction effects 
(such as transaction costs, market impact, and slippage). 

For this demo, we used 
"""

strategy_markdown_text = """
Hello World!
"""

content_explanation = dbc.Tabs(
    [
        create_tab(about_markdown_text, "About"),
        create_tab(strategy_markdown_text, "Strategy"),
    ]
)

"""
    TODO: Benchmark Graph
    ---------------
"""


"""
    Performance Statics Table
    -------------------------
"""

table_header = [
    html.Thead(html.Tr([html.Th(""), html.Th(
        "Strategy Performance"), html.Th("Benchmark Performance")]))
]

statistics = [
    'CAGR',
    'Standard Deviation',
    'Downside Deviation',
    'Sharpe Ratio',
    'Sortino Ratio',
    'Worst Drawdown',
    'Worst Month Return',
    'Best Month Return',
    'Profitable Months'
]

table_body = [html.Tbody(
    [html.Tr([html.Td(statistic), html.Td("N/A")]) for statistic in statistics])]

stats_table = dbc.Table(table_header + table_body, bordered=True)
