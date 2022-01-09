from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output, State
from app import app
from datetime import date, timedelta
import requests
import plotly.graph_objects as go

# define template used
TEMPLATE = "plotly_white"

def generate_candle(df):
    candle_fig = go.Figure(data=[
        go.Candlestick(
            x = df["Date"],
            open = df["Open"],
            high = df["High"],
            low = df["Low"],
            close = df["Close"]
        )
    ])

    candle_fig.update_layout(title=df["Symbol"].unique()[0] + " Price Chart",
                            xaxis = dict(showgrid=False),
                            yaxis = dict(showgrid=False),
                            xaxis_rangeslider_visible=False,
                            template=TEMPLATE)
    return candle_fig

layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(dcc.Dropdown(id="analysis-dropdown", placeholder="Select Symbol"))
        ]),
        dbc.Row(
            dbc.Col(dcc.Graph(id="candle"))
            )
    ])
], id="dummy")

@app.callback([
    Output(component_id="analysis-dropdown", component_property="options"),
    Output(component_id="analysis-dropdown", component_property="value"),
    Input(component_id="dummy", component_property="className"),
    State(component_id='data-store', component_property='data')
])
def generate_dropdown(_, data):
    if data == None:
        return None, None
    data = pd.DataFrame(data)
    symbol_list = data["Symbol"].sort_values().unique()
    options =  [{"label":v, "value":v} for v in symbol_list]
    value = symbol_list[0]
    return options, value


@app.callback([
    Output(component_id="candle", component_property="figure"),
    Input(component_id="analysis-dropdown", component_property="value"),
    State(component_id="data-store", component_property="data")
])
def update_ohlc(value, data):
    if data == None:
        return None

    data = pd.DataFrame(data)
    data["Date"] = pd.to_datetime(data["Date"])
    start_date = (data[data["Symbol"]==value]["Date"].min() - timedelta(days=180)).date()
    print(start_date)
    post_data = {
        "symbol":value,
        "start_date":start_date,
        "interval":"1d"
    }
    response = requests.post("http://127.0.0.1:8000/api/download",data=post_data)
    if response.status_code == 200:
        df = pd.DataFrame.from_dict(response.json())
        ohlc_fig = generate_candle(df)
        return [ohlc_fig]
    else:
        return None
