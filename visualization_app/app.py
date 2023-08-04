from dash import Dash, dcc, html, Input, Output, State, callback
import dash
import dash_bootstrap_components as dbc

from components.navbar import navbar

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])

app.layout = html.Div([

    navbar,

    dash.page_container

])


if __name__ == '__main__':
    app.run(debug=True)
