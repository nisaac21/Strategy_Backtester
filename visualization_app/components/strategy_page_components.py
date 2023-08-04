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
Hello World!
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
