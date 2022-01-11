from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output, State
from app import app
from datetime import date, timedelta
import requests
import plotly.graph_objects as go
from dash import dash_table
from dash.dash_table.Format import Format,Scheme

# define template used
TEMPLATE = "plotly_white"

def generate_candle(df, data):
    candle_fig = go.Figure(data=[
        go.Candlestick(
            x = df["Date"],
            open = df["Open"],
            high = df["High"],
            low = df["Low"],
            close = df["Close"]
        , name="Price")
    ])

    # add buy and sell price
    buy_price = data[data["Action"]=="Buy"].copy()
    sell_price = data[data["Action"]=="Sell"].copy()
    
    candle_fig.add_trace(
        go.Scatter(x=buy_price["Date"], y=buy_price["Price"], mode="markers",marker=dict(color="LightSkyBlue",size=20, line=dict(color="black", width=2)),marker_symbol="triangle-up", name="Buy")
    )
    candle_fig.add_trace(
        go.Scatter(x=sell_price["Date"], y=sell_price["Price"], mode="markers",marker=dict(color="orange",size=20, line=dict(color="black", width=2)),marker_symbol="triangle-down", name="Sell")
    )

    # add 10 and 20 SMA
    df["SMA10"] = df["Close"].rolling(10).mean()
    df["SMA20"] = df["Close"].rolling(20).mean()

    candle_fig.add_trace(
        go.Scatter(x=df["Date"], y=df["SMA10"],line=dict(color="purple", width=2), opacity=0.4, name="SMA-10")
    )

    candle_fig.add_trace(
        go.Scatter(x=df["Date"], y=df["SMA20"],line=dict(color="blue", width=2), opacity=0.4, name="SMA-20")
    )



    candle_fig.update_layout(
                            xaxis = dict(showgrid=False),
                            xaxis_rangeslider_visible=False,
                            showlegend=False,
                            template=TEMPLATE)
    return candle_fig


def generate_transaction(df):

    df_ = df.drop("Value",axis=1).rename({"Value_sgd":"Value",
                    "Exchange_rate":"Exchange Rate"},axis=1).copy()

    # formatting
    df_ = df_.sort_values("Date")
    df_["Date"] = df_["Date"].dt.date
    money = dash_table.FormatTemplate.money(2)
    
    transaction_fig = dash_table.DataTable(
        id="transaction",
        columns = [
            dict(id="Date", name="Date"),
            dict(id="Name", name="Name"),
            dict(id="Symbol", name="Symbol"),
            dict(id="Action", name="Action"),
            dict(id="Price", name="Price",type="numeric",format=money),
            dict(id="Value", name="Value",type="numeric",format=money),
        ],
        data=df_.to_dict('records'),
        sort_action="native",
        style_cell={
        'height': 'auto',
        'minWidth': '150px', 'width': '150px', 'maxWidth': '150px',
        'whiteSpace': 'normal'},
        style_table={'overflowX': 'scroll'},
        style_as_list_view=True,
        page_action="native",
        page_current= 0,
        page_size= 5,
    )

    return transaction_fig

layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H3("Select Position:"),width=3),
            dbc.Col([
                dbc.RadioItems(
                    id="radios-analysis",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-info",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "Open", "value": "Open"},
                        {"label": "Closed", "value": "Closed"}
                    ],
                    value="Open")
            ], width=3)
        ], align="center", justify="center", style=dict(margin="10px")),
        html.Br(),
        html.Br(),
        dbc.Row([
            dbc.Col(html.H3("Select Symbol:"), width=3),
            dbc.Col(dcc.Dropdown(id="analysis-dropdown", placeholder="Select Symbol"), width=3)
        ], align="center", justify="center"),
        dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='Analysis of Past Transaction(s)',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-4 mb-4")
            ]),
        dbc.Row(
            dbc.Col(dcc.Graph(id="candle"))
            ),
        html.Br(),
        dbc.Row([
            dbc.Col(html.H5(children='Transactions', className="text-center"),
                            width=6, className="mt-2")
        ], justify="center"),
        html.Br(),
        dbc.Row([
            dbc.Col(id="analysis-transaction",width={"size":10})
        ], align="center", justify="center"),
    ])
])

@app.callback([
    Output(component_id="analysis-dropdown", component_property="options"),
    Output(component_id="analysis-dropdown", component_property="value"),
    Input(component_id="radios-analysis", component_property="value"),
    State(component_id="open-store", component_property="data"),
    State(component_id="closed-store", component_property="data")
])
def generate_dropdown(position, open, closed):
    if position == "Open":
        if open == None:
            return None, None
        else:
            data = pd.DataFrame(open)
    else:
        if closed == None:
            return None, None
        else:
            data = pd.DataFrame(closed)
        
    symbol_list = data["Symbol"].sort_values().unique()
    options =  [{"label":v, "value":v} for v in symbol_list]
    value = symbol_list[0]
    return options, value


@app.callback([
    Output(component_id="candle", component_property="figure"),
    Input(component_id="analysis-dropdown", component_property="value"),
    State(component_id="data-store", component_property="data")
])
def update_ohlc(symbol, data):
    if data == None:
        return None

    data = pd.DataFrame(data)
    data = data[data["Symbol"]==symbol].copy()
    data["Date"] = pd.to_datetime(data["Date"])
    start_date = (data["Date"].min() - timedelta(days=90)).date()

    post_data = {
        "symbol":symbol,
        "start_date":start_date,
        "interval":"1d"
    }
    response = requests.post("http://127.0.0.1:8000/api/download",data=post_data)
    if response.status_code == 200:
        df = pd.DataFrame.from_dict(response.json())
        ohlc_fig = generate_candle(df, data)
        return [ohlc_fig]
    else:
        return None


@app.callback(
    Output(component_id="analysis-transaction", component_property="children"),
    Input(component_id="analysis-dropdown", component_property="value"),
    State(component_id="data-store", component_property="data"),
)
def update_table(symbol,data):
    if data == None:
        return None
    else:
        data = pd.DataFrame(data)
        data["Date"] = pd.to_datetime(data["Date"])
        data = data[data["Symbol"]==symbol].copy()

        transaction_fig = generate_transaction(data)

        return [transaction_fig]

    