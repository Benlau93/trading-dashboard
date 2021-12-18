from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from dash import dash_table
from app import app

df = pd.read_excel("Transaction Data.xlsx", sheet_name=None)

# transactional data
data = df["Data"]
data["DATE"] = data["Date"].dt.strftime("%b-%y")

# closed position
closed_position = df["Closed Position"]
closed_position["DATE"] = closed_position["Date_Close"].dt.strftime("%b-%y")
closed_position["Type"] = closed_position["Type"] + " - " + closed_position["Currency"].str[:-1]

# define template used
TEMPLATE = "plotly_white"

# main KPI
def generate_indicator(df):
    df_ = df.copy()
    total_pl = df_["P/L (SGD)"].sum()
    avg_pl_per = df_["P/L (%)"].mean()
    avg_holding = df_["Holding (days)"].mean()

    indicator_fig = go.Figure()
    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=total_pl,
                        title = "Total P/L",
                        number = dict(valueformat="$,.0f"),
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
                        number = dict(valueformat=".0f"),
                        domain={"row":0, "column":2})
    )

    indicator_fig.update_layout(
        grid= {"rows":1, "columns":3},
        height=250,
        template=TEMPLATE
    )

    return indicator_fig

def generate_trade_indicator(df):
    trade_kpi = df[["P/L (SGD)","P/L (%)"]].copy()
    trade_kpi["Win"] = df["P/L (SGD)"].map(lambda x: True if x>=0 else False)
    win_rate = trade_kpi["Win"].mean()
    avg_pl_win = trade_kpi[trade_kpi["Win"]]["P/L (%)"].mean()
    median_pl_win = trade_kpi[trade_kpi["Win"]]["P/L (%)"].median()
    avg_pl_loss = trade_kpi[~trade_kpi["Win"]]["P/L (%)"].mean()
    max_pl_loss = trade_kpi[~trade_kpi["Win"]]["P/L (%)"].min()

    trade_indicator = go.Figure()
    trade_indicator.add_trace(
        go.Indicator(mode="gauge+number", value=win_rate,number = dict(valueformat=".0%"), title={"text":"Win Rate"}, 
        gauge={"axis":{"visible":False,"range":[0,1]}}, domain = {'x': [0, 0.33], 'y': [0.2, 0.8]})
    )
    trade_indicator.add_trace(
        go.Indicator(mode="number",value=avg_pl_win, title="Avg Win P/L (%)", number = dict(valueformat=".0%"), domain = {'x': [0.33, 0.66], 'y': [0.5, 1]})
    )
    trade_indicator.add_trace(
        go.Indicator(mode="number",value=median_pl_win, title="Median Win P/L (%)", number = dict(valueformat=".0%"), domain = {'x': [0.66, 1], 'y': [0.5, 1]})
    )
    trade_indicator.add_trace(
        go.Indicator(mode="number",value=avg_pl_loss, title="Avg Loss P/L (%)", number = dict(valueformat=".0%"), domain = {'x': [0.33, 0.66], 'y': [0, 0.5]})
    )
    trade_indicator.add_trace(
        go.Indicator(mode="number",value=max_pl_loss, title="Max Loss P/L (%)", number = dict(valueformat=".0%"), domain = {'x': [0.66, 1], 'y': [0, 0.5]})
    )

    trade_indicator.update_layout(
        height=500,
        template=TEMPLATE,
        margin=dict(t=0)
    )


    return trade_indicator


# culmulative p/L over time & P/L per month

def generate_line(df):
    cul_pl = df.groupby("DATE")[["P/L (SGD)"]].sum().rename({"P/L (SGD)":"P/L"}, axis=1).reset_index()
    cul_pl["DATE(SORT)"] = pd.to_datetime(cul_pl["DATE"], format="%b-%y")
    cul_pl = cul_pl.sort_values(["DATE(SORT)"]).drop("DATE(SORT)", axis=1)
    cul_pl["Cumulative P/L"] = cul_pl["P/L"].cumsum()

    line_fig = make_subplots(specs=[[{"secondary_y": True}]])
    line_fig.add_trace(
        go.Scatter(x=cul_pl["DATE"], y=cul_pl["Cumulative P/L"], name="Cumulative P/L",mode="lines+markers+text", texttemplate="%{y:$,.0f}", textposition="bottom right")
    )
    line_fig.add_trace(
        go.Scatter(x=cul_pl["DATE"], y=cul_pl["P/L"], name="P/L", mode="lines+markers+text",texttemplate="%{y:$,.0f}",textposition="top left",line=dict(dash="dash")),
        secondary_y=True
    )

    line_fig.update_layout(
                            xaxis = dict(showgrid=False),
                            legend=dict(x=0.05,y=0.9),
                            margin=dict(t=0),
                            template=TEMPLATE
    )
    line_fig.update_yaxes(title="Cumulative P/L",secondary_y=False,showgrid=True, zeroline=True,tickformat="$,.0f")
    line_fig.update_yaxes(title="P/L",secondary_y=True, showgrid=False, zeroline=False,tickformat="$,.0f")

    return line_fig


# P/L by quotetype

def generate_bar(df):
    pl_by_type = df.groupby("Type")[["P/L (SGD)"]].sum().rename({"P/L (SGD)":"P/L"}, axis=1).reset_index()
    pl_by_type = pl_by_type.sort_values(["P/L"])

    bar_fig = go.Figure()
    bar_fig.add_trace(
        go.Bar(x=pl_by_type["P/L"],y=pl_by_type["Type"], orientation="h", texttemplate="%{x:$,.0f}", textposition="inside", hovertemplate = "%{y}, %{x:$,.0f}", name="P/L")
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

    pl_by_name_profit = pl_by_name[pl_by_name["P/L"]>=0].rename({"P/L":"Profit","P/L (%)":"Profit (%)"}, axis=1)
    pl_by_name_loss = pl_by_name[pl_by_name["P/L"]<0].rename({"P/L":"Loss","P/L (%)":"Loss (%)"}, axis=1)
    pl_by_name_loss["Loss"] = pl_by_name_loss["Loss"].map(lambda x: abs(x))
    pl_by_name_loss["Loss (%)"] = pl_by_name_loss["Loss (%)"].map(lambda x: abs(x))

    treemap_closed_profit = px.treemap(pl_by_name_profit, path=[px.Constant("Asset Types"),"Type","Name"], values="Profit", color="Profit (%)" ,
                                                    color_continuous_scale="RdBu",
                                                    range_color = [pl_by_name_profit["Profit (%)"].min(), pl_by_name_profit["Profit (%)"].max()],
                                                    hover_data = {"Name":True,"Profit":":$,.0f","Profit (%)":":.0%"},branchvalues="total")
    treemap_closed_profit.update_layout(margin = dict(t=0), template=TEMPLATE)

    treemap_closed_loss = px.treemap(pl_by_name_loss, path=[px.Constant("Asset Types"),"Type","Name"], values="Loss", color="Loss (%)" ,
                                                    color_continuous_scale="RdBu_r",
                                                    range_color = [pl_by_name_loss["Loss (%)"].min(), pl_by_name_loss["Loss (%)"].max()],
                                                    hover_data = {"Name":True,"Loss":":$,.0f","Loss (%)":":.0%"},branchvalues="total")
    treemap_closed_loss.update_layout(margin = dict(t=0), template=TEMPLATE)

    return treemap_closed_profit, treemap_closed_loss


def generate_table(df):
    df_ = df.copy()
    df_ = df_.rename({"Type":"Asset Type",
                    "Price_Open":"Price (Open)",
                    "Price_Close":"Price (Close)",
                    "Amount (SGD)_Open":"Value (Open)",
                    "P/L (SGD)":"P/L"}, axis=1)
    df_ = df_[["Name","Asset Type","Price (Open)","Price (Close)","Value (Open)","P/L","P/L (%)","Holding (days)"]].sort_values(["P/L"], ascending=False)
    
    # formatting
    money = dash_table.FormatTemplate.money(2)
    percentage = dash_table.FormatTemplate.percentage(2)

    table_fig = dash_table.DataTable(
        id="table",
        columns = [
            dict(id="Name", name="Name"),
            dict(id="Price (Open)", name="Price (Open)",type="numeric",format=money),
            dict(id="Price (Close)", name="Price (Close)",type="numeric",format=money),
            dict(id="P/L", name="P/L",type="numeric",format=money),
            dict(id="P/L (%)", name="P/L (%)",type="numeric",format=percentage),
            dict(id="Value (Open)", name="Value (Open)",type="numeric",format=money),
            dict(id="Holding (days)", name="Holding (days)", type="numeric")
        ],
        data=df_.to_dict('records'),
        sort_action="native",
        style_cell={
        'height': 'auto',
        'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
        'whiteSpace': 'normal'},
        style_table={'overflowX': 'scroll'},
        style_as_list_view=True,
        page_action="native",
        page_current= 0,
        page_size= 10,
    )

    return table_fig

# define layout
layout = html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([dcc.Dropdown(id='date-dropdown',placeholder="Filter by Year" )],width={"size": 3, "offset": 3}),
                dbc.Col([dcc.Dropdown(id='type-dropdown',placeholder="Filter by Types" )],width={"size": 3})
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
                dbc.Col(
                    [dcc.Graph(id="trade-indicator")], width={"size": 10, "offset": 1})]),
            dbc.Row([
                dbc.Col(html.H5(children='P/L by Asset Types', className="text-center"),
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
            ]),
            dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='Table',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-0 mb-4")
            ]),
        dbc.Row([
            dbc.Col(id="table-container",width={"size":10,"offset":1})
        ], align="center")
    ])
])


@app.callback(
    Output(component_id="date-dropdown", component_property="options"),
    Input(component_id="type-dropdown", component_property="value")
)
def update_date_dropdown(type):
    if type == None:
        date_options = [{"label":d, "value":d} for d in closed_position.sort_values("Date_Close", ascending=False)["Date_Close"].dt.year.unique()]
    else:
        date_options = [{"label":d, "value":d} for d in closed_position[closed_position["Type"]==type].sort_values("Date_Close", ascending=False)["Date_Close"].dt.year.unique()]

    return date_options


@app.callback(
    Output(component_id="type-dropdown", component_property="options"),
    Input(component_id="date-dropdown", component_property="value")
)
def update_type_dropdown(date):
    if date == None:
        type_options = [{"label":d, "value":d} for d in closed_position["Type"].unique()]
    else:
        type_options = [{"label":d, "value":d} for d in closed_position[closed_position["Date_Close"].dt.year==date]["Type"].unique()]

    return type_options

@app.callback(
    Output(component_id="indicator",component_property="figure"),
    Output(component_id="trade-indicator",component_property="figure"),
    Output(component_id="line", component_property="figure"),
    Output(component_id="bar", component_property="figure"),
    Output(component_id="stacked_bar", component_property="figure"),
    Output(component_id="treemap-closed-profit", component_property="figure"),
    Output(component_id="treemap-closed-loss", component_property="figure"),
    Output(component_id="table-container", component_property="children"),
    Input(component_id="date-dropdown", component_property="value"),
    Input(component_id="type-dropdown", component_property="value")
)
def update_graph(date,type):

    if date == None and type == None:
        data_filtered = data.copy()
        closed_position_filtered = closed_position.copy()

    else:
        if date != None and type != None:
            data_filtered = data[(data["Date"].dt.year==date) & (data["Type"]==type)].copy()
            closed_position_filtered = closed_position[(closed_position["Date_Close"].dt.year==date) & (closed_position["Type"]==type)].copy()

        elif date != None:
            data_filtered = data[(data["Date"].dt.year==date)].copy()
            closed_position_filtered = closed_position[(closed_position["Date_Close"].dt.year==date)].copy()

        else:
            data_filtered = data[(data["Type"]==type)].copy()
            closed_position_filtered = closed_position[(closed_position["Type"]==type)].copy()



    indicator_fig = generate_indicator(closed_position_filtered)
    trade_indicator = generate_trade_indicator(closed_position_filtered)
    line_fig = generate_line(closed_position_filtered)
    bar_fig = generate_bar(closed_position_filtered)
    stack_bar = generate_stack_bar(data_filtered)
    treemap_closed_profit, treemap_closed_loss = generate_treemap(closed_position_filtered)
    table_fig = generate_table(closed_position_filtered)

    return indicator_fig, trade_indicator, line_fig, bar_fig, stack_bar,treemap_closed_profit,treemap_closed_loss,table_fig