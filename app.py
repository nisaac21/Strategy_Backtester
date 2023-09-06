from dash import Dash, html
import dash
import dash_bootstrap_components as dbc
import os
import sys

from components.navbar import navbar

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])

app.layout = html.Div([

    navbar,

    dash.page_container

])


if __name__ == '__main__':
    currDir = os.path.dirname(os.path.realpath(__file__))
    rootDir = os.path.abspath(os.path.join(currDir, '..'))
    app.run(debug=True)
