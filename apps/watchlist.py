from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash.dash_table.Format import Format,Scheme
from dash import callback_context
from app import app
import yfinance as yf
import requests

# define template used
TEMPLATE = "plotly_white"

def generate_table(df):
    df_ = df.copy()
    # get id
    df_["id"] = df_["Symbol"] + "|" + df_["Name"] + "|" + df_["Target_price"].astype(str)

    # get % from target
    df_["DIFF"] = (df_["Target_price"] - df_["Current_price"]) / df_["Current_price"]
    
    def achieved_target(row):
        achieved =  (row["Direction"]== "Below" and row["DIFF"] >0) or (row["Direction"] == "Above" and row["DIFF"]<0)
        return "Yes" if achieved else "No"

    df_["REACHED"] = df_.apply(achieved_target, axis=1)
    # change % from target to 0 if reached target
    df_["DIFF"] = df_.apply(lambda row: row["DIFF"] if row["REACHED"]=="No" else 0, axis=1)

    # sort
    df_["SORT"] = df_["DIFF"].map(lambda x: abs(x))
    df_ = df_.sort_values("SORT")

    # formatting
    money = dash_table.FormatTemplate.money(2)
    percentage = dash_table.FormatTemplate.percentage(2)

    table_fig = dash_table.DataTable(
        id="table-watchlist",
        columns = [
            dict(id="Symbol", name="Symbol"),
            dict(id="Name", name="Name"),
            dict(id="Current_price", name="Current Price",type="numeric", format=money),
            dict(id="Target_price", name="Target Price",type="numeric",format=money),
            dict(id="DIFF", name="% from Target", type="numeric", format=percentage),
            dict(id="REACHED", name="Hit Target")
        ],
        data=df_.to_dict('records'),
        sort_action="native",
        row_selectable='single',
        style_cell={
        'height': 'auto',
        'minWidth': '150px', 'width': '150px', 'maxWidth': '150px',
        'whiteSpace': 'normal'},
        style_as_list_view=True,
        page_action="native",
        page_current= 0,
        page_size= 15,
        style_data_conditional=(
            [
                {
                    "if":{
                        "column_id":"REACHED",
                        "filter_query":"{REACHED} = 'No'"
                    },
                    "backgroundColor":"crimson",
                    "color":"white"
                },

                {
                    "if":{
                        "column_id":"REACHED",
                        "filter_query":"{REACHED} = 'Yes'"
                    },
                    "backgroundColor":"#2E8B57",
                    "color":"white"
                }
            ]
        )
    )

    return table_fig


def generate_candle(df, target):
    # get ath
    ath, current_price = df["Close"].max(), df["Close"].iloc[-1]

    # generate indicator
    indicator_fig = go.Figure()
    indicator_fig.add_trace(
        go.Indicator(mode="number+delta", 
                    title="ATH (last 6mths)",
                    delta = {"reference":current_price, "relative":True , "valueformat":".01%"},
                    value=ath, 
                    number = dict(valueformat="$,.2f"),
                    domain={"row":0, "column":0})
    )

    indicator_fig.add_trace(
        go.Indicator(mode="number+delta", 
                    title="Current Price",
                    delta = {"reference":ath, "relative":True , "valueformat":".01%"},
                    value=current_price, 
                    number = dict(valueformat="$,.2f"),
                    domain={"row":0, "column":1})
    )

    indicator_fig.update_layout(
        grid= {"rows":1, "columns":2},
        height=250,
        template=TEMPLATE
    )

    # generate candlestick chart
    candle_fig = go.Figure(data=[
        go.Candlestick(
            x = df["Date"],
            open = df["Open"],
            high = df["High"],
            low = df["Low"],
            close = df["Close"]
        , name="Price")
    ])

    # add target price
    candle_fig.add_hline(y=target, line_dash = "dash", annotation_text = "Target Price", annotation_position = "top right")

    candle_fig.update_layout(
                            xaxis = dict(showgrid=False),
                            xaxis_rangeslider_visible=False,
                            height=500,
                            showlegend=False,
                            template=TEMPLATE)
    return indicator_fig, candle_fig

layout = html.Div([
        dcc.Interval(id="placeholder-input", interval=1, n_intervals=0, max_intervals=0),
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Div( className="mt-0 mb-4"))
            ]),
            dbc.Row([
                dbc.Col(dbc.Button("Add Watchlist",id="add-watch-button",href="/watchlist/add",color="success"),width=2),
            ], align="start", justify="end"),
            dbc.Row([
                dbc.Col(html.Div( className="mt-0 mb-4"))
            ]),
            dbc.Row([
            dbc.Col(dbc.Card(html.H3(children='Watchlist',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-0 mb-4")
            ]),
            dbc.Row([
            	dbc.Col(id="table-container-watchlist", width=10)
        ], align="center", justify="center"),
            html.Br(),
            dbc.Row([
                dbc.Col(dbc.Button("Delete",id="remove-watch-button",color="danger", href = "http://127.0.0.1:8050/watchlist"),width=2),
            ], align="start", justify="end"),
            html.Br(),
            html.Div(id="candle-container", children = [
                dbc.Row([
                    dbc.Col(html.H3( className="text-center", id="watchlist-chart-title"),
                            width=6)],align="end", justify="center"),
                dbc.Row(
                    dbc.Col(children = [dcc.Graph(id="watchlist-candle")])),
                dbc.Row(
                    dbc.Col(children = [dcc.Graph(id="watchlist-kpi")], width=8), align="center", justify="center")
            ]
        ),
    ])
])

@app.callback(
	Output(component_id="table-container-watchlist", component_property="children"),
    Input(component_id="placeholder-input", component_property="n_intervals"),
    State(component_id="watchlist-store", component_property="data")
)
def generate_charts(_,watchlist_df):
    watchlist_df = pd.DataFrame(watchlist_df)

    table_fig = generate_table(watchlist_df)

    return table_fig


@app.callback([
    Output(component_id="candle-container", component_property="style"),
    Output(component_id="watchlist-kpi", component_property="figure"),
    Output(component_id="watchlist-candle", component_property="figure"),
    Output(component_id="watchlist-chart-title", component_property="children"),
    Input(component_id="table-watchlist", component_property="selected_row_ids"),
    Input(component_id="remove-watch-button", component_property="n_clicks")
],  prevent_initial_call=True,)
def update_ohlc(row_id, clicks):

    if row_id == None:
        return {"display":"none"}, go.Figure(), go.Figure(), None
    else:
        row_id = row_id[0].split("|")
        symbol, name,  target = row_id[0], row_id[1] , float(row_id[2])

        # check if delete button was clicked
        changed_id = [p['prop_id'] for p in callback_context.triggered][0]
        if "remove-watch-button" in changed_id:
            data_del = {"pk":symbol}
            response = requests.delete("http://127.0.0.1:8000/api/watchlist", data=data_del)
            return {"display":"none"}, go.Figure(), None

        data =  yf.download(tickers=symbol, period = "6mo",interval="1d", progress=False)
        data = data.reset_index() 

        indicator_fig, ohlc_fig = generate_candle(data, target)

        return {"display":"block"}, indicator_fig, ohlc_fig, name