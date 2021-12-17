from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output
from dash import dash_table
from app import app
import math

# read in open position
df = pd.read_excel("Transaction Data.xlsx", sheet_name="Open Position", parse_dates=["Date"])


# define template used
TEMPLATE = "plotly_white"



# main kpi
def generate_indicator(df):
    df_ = df.copy()
    
    current_value = df_["Value (SGD)"].sum()
    unrealised_pl = df_["P/L (SGD)"].sum()
    unrealised_pl_per = df_["P/L (SGD)"].sum() / df_["Amount (SGD)"].sum()
    total_position = df_["Name"].nunique()

    indicator_fig = go.Figure()
    indicator_fig.add_trace(
        go.Indicator(mode="number", 
                    title="Total Portfolio Value",
                    value=current_value, 
                    number = dict(valueformat="$,.2f"),
                    domain={"x":[0.2,0.8],"y":[0.6,1]})
    )

    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=unrealised_pl,
                        title = "Unrealized P/L",
                        number = dict(valueformat="$,.2f"),
                        domain={"x":[0,0.33],"y":[0.1,0.4]})
    )

    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=unrealised_pl_per,
                        title = "Unrealized P/L (%)",
                        number = dict(valueformat=".2%"),
                        domain={"x":[0.33,0.66],"y":[0.1,0.4]})
    )
    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=total_position,
                        title = "Total Position(s)",
                        domain={"x":[0.66,1],"y":[0.1,0.4]})
    )

    indicator_fig.update_layout(
        height=350,
        template=TEMPLATE
    )

    return indicator_fig


def generate_bar(df, value):
    VIEW = "P/L" if value == "Absolute" else "P/L (%)"
    FORMAT = "%{y:$,.2f}" if value == "Absolute" else "%{y:.2%}"
    pl_by_name = df.sort_values("Date")[["Name","Symbol","P/L (SGD)","P/L (%)"]].rename({"P/L (SGD)":"P/L"}, axis=1)

    bar_fig = go.Figure()
    bar_fig.add_trace(
        go.Bar(x=pl_by_name["Symbol"],y=pl_by_name[VIEW],texttemplate =FORMAT, textposition="inside", yaxis="y1",name=VIEW, hovertemplate="%{x}, "+FORMAT)
    )

    bar_fig.update_layout(
                        xaxis=dict(showgrid=False, position=1,tickangle=0),
                        margin=dict(t=0),
                        yaxis=(dict(showgrid=False,showticklabels=False,zerolinecolor="black")),
                        template=TEMPLATE                 
    )                

    return bar_fig

def generate_treemap(df, value):
    VIEW = "P/L" if value == "Absolute" else "P/L (%)"
    value_by_name = df[["Type","Symbol","Name","Value (SGD)","P/L (SGD)", "P/L (%)"]].rename({"P/L (SGD)":"P/L","Value (SGD)":"Value","Symbol":"Ticker"}, axis=1)

    treemap_fig = px.treemap(value_by_name, path=[px.Constant("Positions"),"Type","Name"], values="Value", color=VIEW ,
                                                    color_continuous_scale="RdBu",
                                                    range_color = [value_by_name[VIEW].min(), value_by_name[VIEW].max()],
                                                    hover_data = {"Name":False,"Ticker":True,"P/L":":$,.2f","Value":":$,.2f","P/L (%)":":.2%"}, branchvalues="total")
    treemap_fig.update_layout(margin = dict(t=0), template=TEMPLATE)


    return treemap_fig


def generate_table(df):
    df_ = df.copy()
    df_ = df_.rename({"Previous Close":"Current Price",
                    "Avg Price":"Price",
                    "Value (SGD)":"Value",
                    "P/L (SGD)":"Unrealised P/L",
                    "P/L (%)":"Unrealised P/L (%)",
                    "Weightage":"% of Portfolio",
                    "Shares":"Qty"}, axis=1)
    df_ = df_[["Name","Date","Qty","Price","Current Price","Unrealised P/L","Unrealised P/L (%)","Value","Holdings (days)","% of Portfolio"]].sort_values(["Unrealised P/L"])
    
    # formatting
    df_["Date"] = df_["Date"].dt.date
    money = dash_table.FormatTemplate.money(2)
    percentage = dash_table.FormatTemplate.percentage(2)

    table_fig = dash_table.DataTable(
        id="table",
        columns = [
            dict(id="Name", name="Name"),
            dict(id="Date", name="Date"),
            dict(id="Qty", name="Qty"),
            dict(id="Price", name="Price",type="numeric",format=money),
            dict(id="Current Price", name="Current Price",type="numeric",format=money),
            dict(id="Unrealised P/L", name="Unrealised P/L",type="numeric",format=money),
            dict(id="Unrealised P/L (%)", name="Unrealised P/L (%)",type="numeric",format=percentage),
            dict(id="Value", name="Value",type="numeric",format=money),
            dict(id="Holdings (days)", name="Holdings (days)"),
            dict(id="% of Portfolio", name="% of Portfolio",type="numeric",format=percentage),
        ],
        data=df_.to_dict('records'),
        sort_action="native",
        style_cell={
        'height': 'auto',
        'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
        'whiteSpace': 'normal'},
        style_table={'overflowX': 'scroll'},
        style_as_list_view=True,
    )

    return table_fig

indicator_fig = generate_indicator(df)
table_fig = generate_table(df)


layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(dbc.Button("Add Transaction",color="success",href="/portfolio/add",style=dict(margin=10)),width={"size":3,"offset":9}, align="start")
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id="main-indicator",figure=indicator_fig), width={"size":8,"offset":2}),
        ],align="center"),
        dbc.Row([
            dbc.Col(dbc.Card(html.H3(children='BreakDown',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-4 mb-4")
        ]),
        dbc.Row([
            dbc.Col(html.H3("Select View:"),width={"size":3,"offset":3}),
            dbc.Col([
                dbc.RadioItems(
                    id="radios",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-info",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "Absolute", "value": "Absolute"},
                        {"label": "Percentage", "value": "Percentage"}
                    ],
                    value="Absolute")
            ], width=3)
        ], align="center"),

        dbc.Row([
            dbc.Col(html.H5(children='Position by P/L', className="text-center"),
                            width={"size":2,"offset":2}, className="mt-4"),
            dbc.Col(html.H5(children='Position by Value', className="text-center"),
                            width={"size":2, "offset":4}, className="mt-4")
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id="bar_open"), width={"size":6}),
            dbc.Col(dcc.Graph(id="treemap_open"), width={"size":6})
        ]),
        dbc.Row([
            dbc.Col(dbc.Card(html.H3(children='Table',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-0 mb-4")
            ]),
        dbc.Row([
            dbc.Col(table_fig, width={"size":10,"offset":1})
        ], align="center")
    ])
])

@app.callback(
    Output(component_id="bar_open",component_property="figure"),
    Output(component_id="treemap_open",component_property="figure"),
    Input(component_id="radios", component_property="value")
)
def update_graph(value):
    bar_fig = generate_bar(df, value)
    treemap_fig = generate_treemap(df, value)

    return bar_fig, treemap_fig