from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash.dash_table.Format import Format,Scheme
from app import app
import requests

# define template used
TEMPLATE = "plotly_white"

def generate_table(df):
    df_ = df.copy()

    # get % from target
    df_["DIFF"] = (df_["Target_price"] - df_["Current_price"]) / df_["Current_price"]
    df_["SORT"] = df_["DIFF"].map(lambda x: abs(x))
    
    def achieved_target(row):
        achieved =  (row["Direction"]== "Below" and row["DIFF"] >0) or (row["Direction"] == "Above" and row["DIFF"]<0)
        return "Yes" if achieved else "No"

    df_["REACHED"] = df_.apply(achieved_target, axis=1)

    # sort
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
        style_table={'overflowX': 'scroll'},
        style_as_list_view=True,
        page_action="native",
        page_current= 0,
        page_size= 15,
    )

    return table_fig

layout = html.Div([
        dcc.Interval(id="placeholder-input", interval=1, n_intervals=0, max_intervals=0),
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Div( className="mt-0 mb-4"))
            ]),
            dbc.Row([
                dbc.Col(dbc.Button("+ Ticker",id="add-watch-button",href="/watchlist/add",color="success"),width=1),
                dbc.Col(dbc.Button("- Ticker",id="del-watch-button",color="warning"),width=1)
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