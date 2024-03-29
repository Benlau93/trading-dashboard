from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash import dash_table
from app import app
from datetime import date
from dash.dash_table.Format import Format,Scheme

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
    avg_pl_win_per = trade_kpi[trade_kpi["Win"]]["P/L (%)"].mean()
    avg_pl_win = trade_kpi[trade_kpi["Win"]]["P/L (SGD)"].mean()
    avg_pl_loss_per = trade_kpi[~trade_kpi["Win"]]["P/L (%)"].mean()
    avg_pl_loss = trade_kpi[~trade_kpi["Win"]]["P/L (SGD)"].mean()

    trade_indicator = go.Figure()
    trade_indicator.add_trace(
        go.Indicator(mode="gauge+number", value=win_rate,number = dict(valueformat=".0%"), title={"text":"Win Rate"}, 
        gauge={"axis":{"visible":False,"range":[0,1]}}, domain = {'x': [0, 0.33], 'y': [0.2, 0.8]})
    )
    trade_indicator.add_trace(
        go.Indicator(mode="number",value=avg_pl_win_per, title="Avg Win P/L (%)", number = dict(valueformat=".0%"), domain = {'x': [0.33, 0.66], 'y': [0.5, 1]})
    )
    trade_indicator.add_trace(
        go.Indicator(mode="number",value=avg_pl_win, title="Avg Win P/L", number = dict(valueformat="$,.0f"), domain = {'x': [0.66, 1], 'y': [0.5, 1]})
    )
    trade_indicator.add_trace(
        go.Indicator(mode="number",value=avg_pl_loss_per, title="Avg Loss P/L (%)", number = dict(valueformat=".0%"), domain = {'x': [0.33, 0.66], 'y': [0, 0.5]})
    )
    trade_indicator.add_trace(
        go.Indicator(mode="number",value=avg_pl_loss, title="Avg Loss P/L", number = dict(valueformat="$,.0f"), domain = {'x': [0.66, 1], 'y': [0, 0.5]})
    )

    trade_indicator.update_layout(
        height=500,
        template=TEMPLATE,
        margin=dict(t=0)
    )


    return trade_indicator


# culmulative p/L over time & P/L per month

def generate_line(df):

    # P/L
    df_ = df.groupby("DATE")[["P/L (SGD)"]].agg(["sum","count"]).rename({"P/L (SGD)":"P/L"}, axis=1).reset_index()
    df_.columns = ["DATE","P/L","Transaction"]
    df_["DATE(SORT)"] = pd.to_datetime(df_["DATE"], format="%b-%y")
    df_ = df_.sort_values(["DATE(SORT)"]).drop("DATE(SORT)", axis=1)
    df_["Cumulative P/L"] = df_["P/L"].cumsum()

    # define bar color
    bar_colors = ["crimson" if pl <0 else "#2E8B57" for pl in df_["P/L"].values]

    # line_fig = go.Figure()
    line_fig = make_subplots(rows=2, cols = 1, row_heights=[0.8,0.2])
    
    line_fig.add_trace(
        go.Scatter(x=df_["DATE"], y=df_["Cumulative P/L"], name="Cumulative P/L",mode="lines+markers+text", texttemplate="%{y:$,.0f}", textposition="bottom right"),
        row = 1, col=1
    )
    line_fig.add_trace(
        go.Bar(x=df_["DATE"], y=df_["P/L"], name="P/L",texttemplate="%{y:$,.0f}",textposition="inside", marker_color = bar_colors, opacity=0.5),
        row=1, col=1
    )

    line_fig.add_trace(
        go.Bar(x = df_["DATE"], y=df_["Transaction"], name="No. Transaction", texttemplate="%{y}",textposition="inside", marker_color ="rgb(55, 83, 109)", opacity=0.8),
        row=2, col=1
    )

    line_fig.update_yaxes(row=1,col=1,title="P/L",rangemode="tozero",tickformat="$,.0f", zeroline=True, zerolinecolor="black")
    line_fig.update_yaxes(row=2, col=1, title="No. Transaction", rangemode="tozero", showgrid=False)
    line_fig.update_xaxes(row=2, col=1, showgrid=False, visible=False)

    line_fig.update_layout(
                            xaxis = dict(showgrid=False),
                            legend=dict(x=0.05,y=0.9),
                            margin=dict(t=0),
                            height=1000,
                            template=TEMPLATE
    )
    return line_fig


# P/L by quotetype

def generate_bar(df, type):
    GROUP = "Symbol" if type != None else "Type"
    df_ = df.groupby(GROUP)[["P/L (SGD)"]].sum().rename({"P/L (SGD)":"P/L"}, axis=1).reset_index()
    df_ = df_.sort_values(["P/L"])

    bar_fig = go.Figure()
    bar_fig.add_trace(
        go.Bar(x=df_["P/L"],y=df_[GROUP], orientation="h", texttemplate="%{x:$,.0f}", textposition="inside", hovertemplate = "%{y}, %{x:$,.0f}", name="P/L")
    )
    bar_fig.update_layout(
                        xaxis=dict(showgrid=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zerolinecolor="black"),
                        margin=dict(t=0),
                        height=500,
                        template=TEMPLATE                 
    )

    return bar_fig

def generate_box(df):

    df["Profit/Loss"] = df["P/L (SGD)"].map(lambda x: "Profit" if x>=0 else "Loss")

    box_plot = px.box(df, x="Type", y = "Holding (days)", color="Profit/Loss")

    box_plot.update_layout(
        xaxis=dict(showgrid=False, title=None),
        yaxis = dict(showgrid=False, rangemode="tozero"),
        template = TEMPLATE,
        height = 500
    )

    return box_plot

def generate_pie(df, type):
    GROUP = "Symbol" if type != None else "Type"

    # handle profit
    df_profit = df[df["P/L (SGD)"]>=0].groupby(GROUP)[["P/L (SGD)"]].sum().rename({"P/L (SGD)":"Profit"}, axis=1).reset_index()

    pie_profit = go.Figure()
    if len(df_profit) != 0:

        pie_profit.add_trace(
            go.Pie(labels = df_profit[GROUP], values = df_profit["Profit"], textinfo= "label+percent", name="Profit", hovertemplate = "%{label}: %{value:$,.02f}",
            hole = 0.5, rotation=30)
        )

        pie_profit.update_layout(
            template= TEMPLATE,
            height = 500,
            showlegend=False
        )
    

    # handle loss
    df_loss = df[df["P/L (SGD)"]<0].groupby(GROUP)[["P/L (SGD)"]].sum().rename({"P/L (SGD)":"Loss"}, axis=1).reset_index()
    df_loss["Loss"] = df_loss["Loss"].map(lambda x: x*-1)

    pie_loss = go.Figure()
    if len(df_loss) != 0:
        pie_loss.add_trace(
            go.Pie(labels = df_loss[GROUP], values = df_loss["Loss"], textinfo= "label+percent", name="Loss", hovertemplate = "%{label}: %{value:$,.02f}",
            hole = 0.5, rotation = 30)
        )

        pie_loss.update_layout(
            template= TEMPLATE,
            height = 500,
            showlegend=False
        )

    return pie_profit, pie_loss



# P/L by name
def generate_treemap(df):
    df_ = df.groupby(["Type","Name"])[["P/L (SGD)","P/L (%)"]].sum().rename({"P/L (SGD)":"P/L"}, axis=1).reset_index()

    # handle profit
    df_profit = df_[df_["P/L"]>=0].rename({"P/L":"Profit","P/L (%)":"Profit (%)"}, axis=1)
    if len(df_profit) == 0:
        treemap_closed_profit = go.Figure()
    else:
        df_profit["PROFIT_TEXT"] = df_profit.apply(lambda row: "$" + str(round(row["Profit"])) +", "+ str(round(row["Profit (%)"]*100)) + "%", axis=1)
        treemap_closed_profit = px.treemap(df_profit, path=[px.Constant("Asset Types"),"Type","Name","PROFIT_TEXT"], values="Profit", color="Profit (%)" ,
                                                    color_continuous_scale="RdBu",
                                                    range_color = [df_profit["Profit (%)"].min(), df_profit["Profit (%)"].max()],
                                                    hover_data = {"Name":True,"Profit":":$,.02f","Profit (%)":":.01%"},branchvalues="total")
        treemap_closed_profit.update_layout(margin = dict(t=0), template=TEMPLATE)

    
    # handle loss
    df_loss = df_[df_["P/L"]<0].rename({"P/L":"Loss","P/L (%)":"Loss (%)"}, axis=1)
    if len(df_loss) == 0:
        treemap_closed_loss = go.Figure()
    else:
        df_loss["Loss"] = df_loss["Loss"].map(lambda x: abs(x))
        df_loss["Loss (%)"] = df_loss["Loss (%)"].map(lambda x: abs(x))
        df_loss["LOSS_TEXT"] = df_loss.apply(lambda row: "-$" + str(round(row["Loss"])) +", -"+ str(round(row["Loss (%)"]*100)) + "%", axis=1)



        treemap_closed_loss = px.treemap(df_loss, path=[px.Constant("Asset Types"),"Type","Name","LOSS_TEXT"], values="Loss", color="Loss (%)" ,
                                                        color_continuous_scale="RdBu_r",
                                                        range_color = [df_loss["Loss (%)"].min(), df_loss["Loss (%)"].max()],
                                                        hover_data = {"Name":True,"Loss":":$,.0f","Loss (%)":":.0%"},branchvalues="total")
        treemap_closed_loss.update_layout(margin = dict(t=0), template=TEMPLATE)

    return treemap_closed_profit, treemap_closed_loss


def generate_table(df):
    df_ = df.copy()
    df_ = df_.rename({"Type":"Asset Type",
                    "Date_Open":"Date (Open)",
                    "Date_Close":"Date (Close)",
                    "P/L (SGD)":"P/L"}, axis=1)
    df_ = df_.sort_values(["Date (Close)","Name"], ascending=[False,True])
    for dat in ["Date (Open)","Date (Close)"]:
        df_[dat] = df_[dat].dt.date

    # formatting
    money = dash_table.FormatTemplate.money(2)
    percentage = dash_table.FormatTemplate.percentage(2)

    table_fig = dash_table.DataTable(
        id="table",
        columns = [
            dict(id="Date (Open)", name="Date (Open)"),
            dict(id="Date (Close)", name="Date (Close)"),
            dict(id="Name", name="Name"),
            dict(id="Asset Type", name="Asset Type"),
            dict(id="P/L", name="P/L",type="numeric",format=money),
            dict(id="P/L (%)", name="P/L (%)",type="numeric",format=percentage),
            dict(id="Holding (days)", name="Holding (days)", type="numeric")
        ],
        data=df_.to_dict('records'),
        sort_action="native",
        row_selectable='single',
        style_cell={
        'height': 'auto',
        'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
        'whiteSpace': 'normal'},
        style_table={'overflowX': 'scroll'},
        style_as_list_view=True,
        page_action="native",
        page_current= 0,
        page_size= 5,
    )
    return table_fig

def generate_transaction(df, id):

    df_ = df.drop("Value",axis=1).rename({"Value_sgd":"Value",
                    "Exchange_rate":"Exchange Rate"},axis=1).copy()
    # get transactional data
    if id == None or len(id) == 0:
        df_ = df_.sort_values("Date").copy()
    else:
        id = id[0].split("|")
        if len(id) == 3:
            ticker, start, end = id[0], id[1], id[2]
        else:
            ticker, start = id[0], id[1]
            end = date.today()

        start, end = pd.to_datetime(start,format="%Y-%m-%d"), pd.to_datetime(end,format="%Y-%m-%d")
        df_ = df_[(df_["Symbol"]==ticker) & (df_["Date"] >= start) & (df_["Date"]<=end)].sort_values("Date").copy()

    # formatting
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
            dict(id="Quantity", name="Quantity",type="numeric"),
            dict(id="Fees", name="Fees",type="numeric",format=money),
            dict(id="Exchange Rate", name="Exchange Rate",type="numeric", format=Format(precision=2,scheme=Scheme.fixed)),
            dict(id="Value", name="Value",type="numeric",format=money),
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
        page_size= 5,
    )

    return transaction_fig


# define layout
layout = html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([dcc.Dropdown(id='date-dropdown',placeholder="Filter by Year" )],width={"size": 3, "offset": 3}),
                dbc.Col([dcc.Dropdown(id='type-dropdown',placeholder="Filter by Types" )],width={"size": 3})
            ]),
            dbc.Row([
                dbc.Col(
                    [dcc.Graph(id="indicator")], width=10)], justify="center"),
            dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='Monthly Analysis',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-4 mb-4")
            ]),
            dbc.Row([
                dbc.Col(html.H5(children='Cumulative & Monthly P/L', className="text-center"),
                                width=6, className="mt-4")
                ], justify="center"),
            dbc.Row([
                dbc.Col([dcc.Graph(id="line")], width=12)
            ],),

            dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='Breakdown of Trades',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-4 mb-4")
            ]),
            dbc.Row([
                dbc.Col([dcc.Graph(id="trade-indicator")], width={"size": 10, "offset": 1})]),
            dbc.Row([
                dbc.Col(html.H5(children='P/L by Asset Types', className="text-center"),
                                width=4, className="mt-4"),
                dbc.Col(html.H5(children='Holding days by Type & P/L', className="text-center"), width=8, className="mt-4"),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id="bar"), width=6),
                dbc.Col(dcc.Graph(id="box"), width=6)
            ]),
            dbc.Row([
                dbc.Col(dbc.Card(html.H4(children='Profit Analysis',
                                 className="text-center text-light bg-success"), body=True, color="success")
                , className="mt-4 mb-4")
            ]),
            dbc.Row([
            dbc.Col(html.H5(children='% of Total Profit', className="text-center"),
                            width=4, className="mt-4"),
            dbc.Col(html.H5(children='P/L by Name (Profit)', className="text-center"), width=8, className="mt-4"),
            ]),
            dbc.Row([
                dbc.Col([dcc.Graph(id="pie-profit")], width=6),
                dbc.Col([dcc.Graph(id="treemap-closed-profit")], width=6)
            ]),
            dbc.Row([
                dbc.Col(dbc.Card(html.H4(children='Loss Analysis',
                                 className="text-center text-light bg-danger"), body=True, color="danger")
                , className="mt-4 mb-4")
            ]),
            dbc.Row([
                dbc.Col(html.H5(children='% of Total Loss', className="text-center"),
                                width=4, className="mt-4"),
                dbc.Col(html.H5(children='P/L by Name (Loss)', className="text-center"), width=8, className="mt-4"),
            ]),
            dbc.Row([
                dbc.Col([dcc.Graph(id="pie-loss")], width=6),
                dbc.Col([dcc.Graph(id="treemap-closed-loss")], width=6)
            ]),
            dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='Tables',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-0 mb-4")
            ]),
            dbc.Row([
                dbc.Col(html.H5(children='Summary Position', className="text-center"),
                                width=6, className="mt-2")
            ], justify="center"),
            dbc.Row([
                dbc.Col(id="table-container",width={"size":10,"offset":1})
            ], align="center"),
            html.Br(),
            dbc.Row([
                dbc.Col(html.H5(children='Transactions', className="text-center"),
                                width=6, className="mt-2")
            ], justify="center"),
            dbc.Row([
                dbc.Col(id="transaction-container",width={"size":10})
            ], align="center", justify="center"),
    ])
])


@app.callback(
    Output(component_id="date-dropdown", component_property="options"),
    Input(component_id="type-dropdown", component_property="value"),
    State(component_id="closed-store", component_property="data")
)
def update_date_dropdown(type, closed):
    if closed == None:
        return None
    closed = pd.DataFrame(closed)
    closed["Date"] = pd.to_datetime(closed["Date"])

    if type == None:
        date_options = [{"label":d, "value":d} for d in closed.sort_values("Date", ascending=False)["Date"].dt.year.unique()]
    else:
        date_options = [{"label":d, "value":d} for d in closed[closed["Type"]==type].sort_values("Date", ascending=False)["Date"].dt.year.unique()]

    return date_options


@app.callback(
    Output(component_id="type-dropdown", component_property="options"),
    Input(component_id="date-dropdown", component_property="value"),
    State(component_id="closed-store", component_property="data")
)
def update_type_dropdown(date, closed):
    if closed == None:
        return None

    closed = pd.DataFrame(closed)
    closed["Date"] = pd.to_datetime(closed["Date"])

    if date == None:
        type_options = [{"label":d, "value":d} for d in closed["Type"].unique()]
    else:
        type_options = [{"label":d, "value":d} for d in closed[closed["Date"].dt.year==date]["Type"].unique()]

    return type_options

@app.callback(
    Output(component_id="indicator",component_property="figure"),
    Output(component_id="trade-indicator",component_property="figure"),
    Output(component_id="line", component_property="figure"),
    Output(component_id="bar", component_property="figure"),
    Output(component_id="box", component_property="figure"),
    Output(component_id="treemap-closed-profit", component_property="figure"),
    Output(component_id="treemap-closed-loss", component_property="figure"),
    Output(component_id="pie-profit", component_property="figure"),
    Output(component_id="pie-loss", component_property="figure"),
    Output(component_id="table-container", component_property="children"),
    Input(component_id="date-dropdown", component_property="value"),
    Input(component_id="type-dropdown", component_property="value"),
    State(component_id="data-store", component_property="data"),
    State(component_id="closed-store", component_property="data")
)
def update_graph(date,type, data, closed):
    if data == None or closed == None:
        return None, None, None, None, None, None, None, None, None, None

    data = pd.DataFrame(data)
    data["Date"] = pd.to_datetime(data["Date"])
    closed = pd.DataFrame(closed)
    for dat in ["Date_Open","Date_Close","Date"]:
        closed[dat] = pd.to_datetime(closed[dat])

    if date == None and type == None:
        data_filtered = data.copy()
        closed_position_filtered = closed.copy()

    else:
        if date != None and type != None:
            data_filtered = data[(data["Date"].dt.year==date) & (data["Type"]==type)].copy()
            closed_position_filtered = closed[(closed["Date"].dt.year==date) & (closed["Type"]==type)].copy()

        elif date != None:
            data_filtered = data[(data["Date"].dt.year==date)].copy()
            closed_position_filtered = closed[(closed["Date"].dt.year==date)].copy()

        else:
            data_filtered = data[(data["Type"]==type)].copy()
            closed_position_filtered = closed[(closed["Type"]==type)].copy()



    indicator_fig = generate_indicator(closed_position_filtered)
    trade_indicator = generate_trade_indicator(closed_position_filtered)
    line_fig = generate_line(closed_position_filtered)
    bar_fig = generate_bar(closed_position_filtered, type)
    pie_profit, pie_loss = generate_pie(closed_position_filtered, type)
    box_fig = generate_box(closed_position_filtered)
    treemap_closed_profit, treemap_closed_loss = generate_treemap(closed_position_filtered)
    table_fig = generate_table(closed_position_filtered)

    return indicator_fig, trade_indicator, line_fig, bar_fig,box_fig, treemap_closed_profit,treemap_closed_loss,pie_profit, pie_loss, table_fig


@app.callback(
    Output(component_id="transaction-container", component_property="children"),
    Input(component_id="table", component_property="selected_row_ids"),
    State(component_id="data-store", component_property="data"),
)
def update_table(id, data):
    if data == None:
        return None

    data = pd.DataFrame(data)
    data["Date"] = pd.to_datetime(data["Date"])

    transaction_fig = generate_transaction(data,id)

    return transaction_fig