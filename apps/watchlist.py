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

layout = html.Div([html.H1("WATCHLIST")])