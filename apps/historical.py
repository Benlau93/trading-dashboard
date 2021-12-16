from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from app import app

df = pd.read_excel("Transaction Data.xlsx", sheet_name=None)

# transactional data
data = df["Data"]
data["DATE"] = data["Date"].dt.strftime("%b-%y")

# closed position
closed_position = df["Closed Position"]
closed_position["DATE"] = closed_position["Date_Close"].dt.strftime("%b-%y")

# filters
date_options = [{"label":d, "value":d} for d in closed_position.sort_values("Date_Close", ascending=False)["DATE"].unique()]
type_options =  [{"label":d, "value":d} for d in closed_position["Type"].unique()]

# define template used
TEMPLATE = "plotly_white"

# main KPI
def generate_indicator(df):
    df_ = df.copy()
    total_pl = round(df_["P/L (SGD)"].sum())
    avg_pl_per = df_["P/L (%)"].mean()
    avg_holding = round(df_["Holding (days)"].mean())

    indicator_fig = go.Figure()
    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=total_pl,
                        title = "Total P/L",
                        number = dict(valueformat="$,"),
                        domain={"row":0, "column":0})
    )

    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=avg_pl_per,
                        title = "Avg P/L (%)",
                        number = dict(valueformat=".0%"),
                        domain={"row":0, "column":1})
    )
    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=avg_holding,
                        title = "Avg Holdings (days)",
                        domain={"row":0, "column":2})
    )

    indicator_fig.update_layout(
        grid= {"rows":1, "columns":3},
        height=250,
        template=TEMPLATE
    )

    return indicator_fig


# culmulative p/L over time & P/L per month

def generate_line(df):
    cul_pl = df.groupby("DATE")[["P/L (SGD)"]].sum().rename({"P/L (SGD)":"P/L"}, axis=1).reset_index()
    cul_pl["DATE(SORT)"] = pd.to_datetime(cul_pl["DATE"], format="%b-%y")
    cul_pl = cul_pl.sort_values(["DATE(SORT)"]).drop("DATE(SORT)", axis=1)
    cul_pl["Cumulative P/L"] = cul_pl["P/L"].cumsum()
    cul_pl["Cumulative P/L"] = cul_pl["Cumulative P/L"].map(lambda x: round(x))
    cul_pl["P/L"] = cul_pl["P/L"].map(lambda x: round(x))
    cul_pl["CUM_TEXT"] = cul_pl["Cumulative P/L"].map(lambda x: "-$" + str(abs(x)) if x <0 else "$" + str(x))
    cul_pl["PL_TEXT"] = cul_pl["P/L"].map(lambda x: "-$" + str(abs(x)) if x <0 else "$" + str(x))

    line_fig = make_subplots(specs=[[{"secondary_y": True}]])
    line_fig.add_trace(
        go.Scatter(x=cul_pl["DATE"], y=cul_pl["Cumulative P/L"], name="Cumulative P/L",mode="lines+markers+text", text=cul_pl["CUM_TEXT"], textposition="bottom right")
    )
    line_fig.add_trace(
        go.Scatter(x=cul_pl["DATE"], y=cul_pl["P/L"], name="P/L", mode="lines+markers+text",text=cul_pl["PL_TEXT"],textposition="top left",line=dict(dash="dash")),
        secondary_y=True
    )

    line_fig.update_layout(
                            xaxis = dict(showgrid=False),
                            legend=dict(x=0.1,y=0.9),
                            margin=dict(t=0),
                            template=TEMPLATE
    )
    line_fig.update_yaxes(title="Cumulative P/L",secondary_y=False,showgrid=True, zeroline=True)
    line_fig.update_yaxes(title="P/L",secondary_y=True, showgrid=False, zeroline=False)

    return line_fig


# P/L by quotetype

def generate_bar(df):
    pl_by_type = df.groupby("Type")[["P/L (SGD)"]].sum().reset_index()

    pl_by_type["P/L"] = pl_by_type["P/L (SGD)"].map(lambda x: round(x))
    pl_by_type["TEXT"] = pl_by_type["P/L"].map(lambda x:  "-$" + str(abs(x)) if x<0 else "$" + str((x)))
    pl_by_type = pl_by_type.sort_values(["P/L"])

    bar_fig = go.Figure()
    bar_fig.add_trace(
        go.Bar(x=pl_by_type["P/L"],y=pl_by_type["Type"], orientation="h", text=pl_by_type["TEXT"], textposition="inside")
    )
    bar_fig.update_layout(
                        xaxis=dict(showgrid=False, showticklabels=False),
                        yaxis=dict(showgrid=False),
                        margin=dict(t=0),
                        template=TEMPLATE                 
    )

    return bar_fig

def generate_stack_bar(df):

    # no. of trade by type
    trade = df.groupby(["DATE","Action"])[["Symbol"]].count().rename({"Symbol":"No. Trades"}, axis=1).reset_index()
    trade["DATE(SORT)"] = pd.to_datetime(trade["DATE"], format="%b-%y")
    trade = trade.sort_values(["DATE(SORT)"]).drop("DATE(SORT)", axis=1)

    stack_bar = go.Figure()
    stack_bar.add_trace(
        go.Bar(x=trade[trade["Action"]=="Buy"]["DATE"], y=trade[trade["Action"]=="Buy"]["No. Trades"], name="No. of Buy Position", text=trade[trade["Action"]=="Buy"]["No. Trades"])
    )
    stack_bar.add_trace(
        go.Bar(x=trade[trade["Action"]=="Sell"]["DATE"], y=trade[trade["Action"]=="Sell"]["No. Trades"], name="No. of Sell Position", text=trade[trade["Action"]=="Sell"]["No. Trades"])
    )
    stack_bar.update_layout(barmode='stack',
                            yaxis=dict(showgrid=False, showticklabels=False),
                            legend=dict(x=0.02,y=0.95),
                            margin=dict(t=0),
                            template=TEMPLATE
    )

    return stack_bar


# P/L by name
def generate_treemap(df):
    pl_by_name = df.groupby(["Type","Name"])[["P/L (SGD)","P/L (%)"]].sum().rename({"P/L (SGD)":"P/L"}, axis=1).reset_index()
    pl_by_name["P/L"] = pl_by_name["P/L"].map(lambda x: round(x))

    pl_by_name_profit = pl_by_name[pl_by_name["P/L"]>=0].copy()
    pl_by_name_profit["Profit"] = pl_by_name_profit["P/L"]
    pl_by_name_profit["Profit (%)"] = pl_by_name_profit["P/L (%)"].map(lambda x: str(round(x*100)) + "%")

    pl_by_name_loss = pl_by_name[pl_by_name["P/L"]<0].copy()
    pl_by_name_loss["Loss"] = pl_by_name_loss["P/L"].map(lambda x: abs(x))
    pl_by_name_loss["Loss (%)"] = pl_by_name_loss["P/L (%)"].map(lambda x: "-" + str(round(x*100)) + "%")


    treemap_closed_profit = px.treemap(pl_by_name_profit, path=[px.Constant("Financial Asset"),"Type","Name"], values="Profit", color="Profit" ,
                                                    color_continuous_scale="RdBu",
                                                    range_color = [0, pl_by_name_profit["P/L"].max()],
                                                    hover_data = {"Name":True,"P/L":False,"Profit":True,"Profit (%)":True})
    treemap_closed_profit.update_layout(margin = dict(t=0), template=TEMPLATE)

    treemap_closed_loss = px.treemap(pl_by_name_loss, path=[px.Constant("Financial Asset"),"Type","Name"], values="Loss", color="Loss" ,
                                                    color_continuous_scale="RdBu_r",
                                                    range_color = [0, pl_by_name_loss["P/L"].max()],
                                                    hover_data = {"Name":True,"P/L":False,"Loss":True,"Loss (%)":True})
    treemap_closed_loss.update_layout(margin = dict(t=0), template=TEMPLATE)

    return treemap_closed_profit, treemap_closed_loss

# define layout
layout = html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([dcc.Dropdown(id='date-dropdown',options=date_options,placeholder="Filter by Month" )],width={"size": 3, "offset": 3}),
                dbc.Col([dcc.Dropdown(id='type-dropdown',options=type_options,placeholder="Filter by Types" )],width={"size": 3})
            ]),
            dbc.Row([
                dbc.Col(
                    [dcc.Graph(id="indicator")], width={"size": 8, "offset": 2})]),
            dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='P/L by Month-Year',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-4 mb-4")
            ]),
            dbc.Row([
                dbc.Col(html.H5(children='Cumulative & Monthly P/L', className="text-center"),
                                width={"size":6, "offset":3}, className="mt-4")
                ]),
            dbc.Row([
                dbc.Col([dcc.Graph(id="line")], width=12)
            ],),

            dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='Breakdown of Trades',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-4 mb-4")
            ]),
            dbc.Row([
                dbc.Col(html.H5(children='P/L by Types', className="text-center"),
                                width=4, className="mt-4"),
                dbc.Col(html.H5(children='No. of Trade by Months', className="text-center"), width=8, className="mt-4"),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id="bar"), width=6),
                dbc.Col(dcc.Graph(id="stacked_bar"), width=6)
            ],),
            dbc.Row([
            dbc.Col(html.H5(children='P/L by Name (Profit)', className="text-center"),
                            width=4, className="mt-4"),
            dbc.Col(html.H5(children='P/L by Name (Loss)', className="text-center"), width=8, className="mt-4"),
            ]),
            dbc.Row([
                dbc.Col([dcc.Graph(id="treemap-closed-profit")], width=6),
                dbc.Col([dcc.Graph(id="treemap-closed-loss")], width=6)
            ])
    ])
])

@app.callback(
    Output(component_id="indicator",component_property="figure"),
    Output(component_id="line", component_property="figure"),
    Output(component_id="bar", component_property="figure"),
    Output(component_id="stacked_bar", component_property="figure"),
    Output(component_id="treemap-closed-profit", component_property="figure"),
    Output(component_id="treemap-closed-loss", component_property="figure"),
    Input(component_id="date-dropdown", component_property="value"),
    Input(component_id="type-dropdown", component_property="value")
)
def update_graph(date,type):

    if date == None and type == None:
        data_filtered = data.copy()
        closed_position_filtered = closed_position.copy()
        closed_position_filtered_freeze_date = closed_position.copy()

    else:
        if date != None and type != None:
            data_filtered = data[(data["DATE"]==date) & (data["Type"]==type)].copy()
            closed_position_filtered = closed_position[(closed_position["DATE"]==date) & (closed_position["Type"]==type)].copy()
            closed_position_filtered_freeze_date = closed_position[(closed_position["Type"]==type)].copy()

        elif date != None:
            data_filtered = data[(data["DATE"]==date)].copy()
            closed_position_filtered = closed_position[(closed_position["DATE"]==date)].copy()
            closed_position_filtered_freeze_date = closed_position.copy()

        else:
            data_filtered = data[(data["Type"]==type)].copy()
            closed_position_filtered = closed_position[(closed_position["Type"]==type)].copy()
            closed_position_filtered_freeze_date = closed_position[(closed_position["Type"]==type)].copy()



    indicator_fig = generate_indicator(closed_position_filtered)
    line_fig = generate_line(closed_position_filtered_freeze_date)
    bar_fig = generate_bar(closed_position_filtered)
    stack_bar = generate_stack_bar(data_filtered)
    treemap_closed_profit, treemap_closed_loss = generate_treemap(closed_position_filtered)

    return indicator_fig, line_fig, bar_fig, stack_bar,treemap_closed_profit,treemap_closed_loss