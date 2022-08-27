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

# import watchlist
watchlist_df = requests.get("http://127.0.0.1:8000/api/watchlist")
watchlist_df = pd.DataFrame.from_dict(watchlist_df.json())

def generate_table(df):
    df_ = df.copy()

    # get % from target
    df_["DIFF"] = (df_["target_price"] - df_["current_price"]) / df_["current_price"]
    df_["SORT"] = df_["DIFF"].map(lambda x: abs(x))
    
    def achieved_target(row):
        achieved =  (row["direction"]== "Below" and row["DIFF"] >0) or (row["direction"] == "Above" and row["DIFF"]<0)
        return "True" if achieved else "False"

    df_["REACHED"] = df_.apply(achieved_target, axis=1)

    # sort
    df_ = df_.sort_values("SORT")

    # formatting
    money = dash_table.FormatTemplate.money(2)
    percentage = dash_table.FormatTemplate.percentage(2)

    table_fig = dash_table.DataTable(
        id="table-watchlist",
        columns = [
            dict(id="symbol", name="Symbol"),
            dict(id="name", name="Name"),
            dict(id="current_price", name="Current Price",type="numeric", format=money),
            dict(id="target_price", name="Target Price",type="numeric",format=money),
            dict(id="DIFF", name="% from Target", type="numeric", format=percentage),
            dict(id="REACHED", name="Achieved")
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

table_fig = generate_table(watchlist_df)

layout = html.Div([
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
            	dbc.Col(id="table-container-watchlist", children=table_fig, width=10)
        ], align="center", justify="center"),
    ])
])

# @app.callback(
# 	Output(component_id="table-container-watchlist", component_property="children"),
#     Input()
# )