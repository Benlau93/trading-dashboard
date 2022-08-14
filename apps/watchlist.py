from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from app import app

# define template used
TEMPLATE = "plotly_white"

layout = html.Div([
        dbc.Container([
            dbc.Row([
                dcc.Location(id='watch-refresh-url', refresh=True),
                dbc.Col(html.Div( className="mt-0 mb-4"))
            ]),
            dbc.Row([
                dbc.Col(dbc.Button("+ Ticker",id="add-watch-button",color="info"),width=1),
                dbc.Col(dbc.Button("- Ticker",id="del-watch-button",color="warning"),width=1)
            ], align="start", justify="end"),
            dbc.Row([
                dbc.Col(html.Div( className="mt-0 mb-4"))
            ]),
    ])
])
