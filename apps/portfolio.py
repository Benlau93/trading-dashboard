from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash.dash_table.Format import Format,Scheme
from app import app
import requests

# define template used
TEMPLATE = "plotly_white"

# main kpi
def generate_indicator(df):
    df_ = df.copy()
    
    current_value = df_["Value"].sum()
    unrealised_pl = df_["Unrealised P/L"].sum()
    unrealised_pl_per = df_["Unrealised P/L"].sum() / df_["Amount (SGD)"].sum()
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
    VIEW = "Unrealised P/L" if value == "Absolute" else "Unrealised P/L (%)"
    FORMAT = "%{y:$,.2f}" if value == "Absolute" else "%{y:.2%}"
    df_ = df.sort_values("Date")[["Name","Symbol","Unrealised P/L","Unrealised P/L (%)"]].copy()

    bar_fig = go.Figure()
    bar_fig.add_trace(
        go.Bar(x=df_["Symbol"],y=df_[VIEW],texttemplate =FORMAT, textposition="inside",name=VIEW, hovertemplate="%{x}, "+FORMAT)
    )

    bar_fig.update_layout(
                        xaxis=dict(showgrid=False, position=1,tickangle=0),
                        margin=dict(t=0),
                        yaxis=(dict(showgrid=False,showticklabels=False,zerolinecolor="black")),
                        template=TEMPLATE                 
    )                

    return bar_fig

def generate_treemap(df, value):
    VIEW = "Unrealised P/L" if value == "Absolute" else "Unrealised P/L (%)"
    df_ = df[["Type","Symbol","Name","Value","Unrealised P/L", "Unrealised P/L (%)"]].copy()

    treemap_fig = px.treemap(df_, path=[px.Constant("Positions"),"Type","Name"], values="Value", color=VIEW ,
                                                    color_continuous_scale="RdBu",
                                                    range_color = [df_[VIEW].min(), df_[VIEW].max()],
                                                    hover_data = {"Name":False,"Symbol":True,"Unrealised P/L":":$,.2f","Value":":$,.2f","Unrealised P/L (%)":":.2%"}, branchvalues="total")
    treemap_fig.update_layout(margin = dict(t=0), template=TEMPLATE)


    return treemap_fig


def generate_line(df, value, ticker_list):
    VIEW = "Unrealised P/L" if value == "Absolute" else "Unrealised P/L (%)"
    FORMAT = "%{y:$,.2f}" if value == "Absolute" else "%{y:.2%}"
    df_ = df.copy()

    line_fig = go.Figure()

    if ticker_list == None or len(ticker_list) ==0:
        df_ = df_.groupby("Date").sum().reset_index()
        df_["Unrealised P/L (%)"] = df_["Unrealised P/L"] / df_["Amount (SGD)"]
        line_fig.add_trace(
            go.Scatter(x=df_["Date"], y=df_[VIEW], mode="lines+markers+text", texttemplate=FORMAT, textposition="bottom right", textfont=dict(size=10)
            )
        )
        line_fig.update_layout(
            margin=dict(t=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(zerolinecolor="black",title=VIEW, tickformat=FORMAT[4:-3] + "0" + FORMAT[-2]),
            template=TEMPLATE
        )
    else:
        for t in ticker_list:
            df_filtered = df_[df_["Symbol"]==t].groupby("Date").sum().reset_index()
            df_filtered["Unrealised P/L (%)"] = df_filtered["Unrealised P/L"] / df_filtered["Amount (SGD)"]
            
            line_fig.add_trace(
                go.Scatter(x=df_filtered["Date"], y=df_filtered[VIEW], mode="lines+markers", hovertemplate = "%{x}, " + FORMAT, name=t
                )
            )
        line_fig.update_layout(
            margin=dict(t=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(zerolinecolor="black",title=VIEW, tickformat=FORMAT[4:-3] + "0" + FORMAT[-2]),
            template=TEMPLATE
        )

    return line_fig


def generate_table(df):
    df_ = df.copy()
    total_value = df_["Value"].sum()
    df_["Weightage"] = df_["Value"].map(lambda x: x/total_value)
    df_ = df_.rename({
                    "Price":"Current Price",
                    "Avg_price":"Avg Price",
                    "Value":"Current Value",
                    "Total_holding":"Holding (days)"}, axis=1)
    df_ = df_.sort_values(["Unrealised P/L"], ascending=False)
    
    # formatting
    df_["Date"] = df_["Date"].dt.date
    money = dash_table.FormatTemplate.money(2)
    percentage = dash_table.FormatTemplate.percentage(2)

    table_fig = dash_table.DataTable(
        id="table-open",
        columns = [
            dict(id="Date", name="Date"),
            dict(id="Name", name="Name"),
            dict(id="Total Quantity", name="Total Quantity"),
            dict(id="Avg Price", name="Avg Price",type="numeric",format=money),
            dict(id="Current Price", name="Current Price",type="numeric",format=money),
            dict(id="Unrealised P/L", name="Unrealised P/L",type="numeric",format=money),
            dict(id="Unrealised P/L (%)", name="Unrealised P/L (%)",type="numeric",format=percentage),
            dict(id="Current Value", name="Current Value",type="numeric",format=money),
            dict(id="Holding (days)", name="Holding (days)"),
            dict(id="Weightage", name="Weightage",type="numeric",format=percentage),
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
def generate_transaction(data, open_position, id):
    open_ = open_position[["Symbol","Date_Open","Avg_exchange_rate"]].copy()
    df_ = pd.merge(data.drop("Value",axis=1), open_, on="Symbol")
    df_ = df_[df_["Date"]>=df_["Date_Open"]].copy()
    df_ = df_.rename({"Value_sgd":"Value","Avg_exchange_rate":"Exchange Rate"},axis=1).copy()

    # get transactional data
    if id == None or len(id) == 0:
        df_ = df_.sort_values("Date").copy()
    else:
        id = id[0].split("|")
        ticker, start = id[0], id[1]
        start = pd.to_datetime(start,format="%Y-%m-%d")
        df_ = df_[(df_["Symbol"]==ticker) & (df_["Date"] >= start)].sort_values("Date").copy()

    # formatting
    df_["Date"] = df_["Date"].dt.date
    money = dash_table.FormatTemplate.money(2)
    
    transaction_fig = dash_table.DataTable(
        id="transaction-open",
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

layout = html.Div([
    dcc.Location(id='refresh-url', refresh=True),
    html.Div(id="refresh-alert",style={"font-size":"large", "font-family": "Arial, Helvetica, sans-serif","text-align":"center"}),
    dbc.Container([
        dbc.Row([
            dbc.Col(dbc.Button("Refresh Ticker Price",id="refresh-button",color="warning",style={"margin-top":10,"margin-right":0}),width=2),
            dbc.Col(dbc.Button("Add Transaction",color="success",href="/portfolio/add",style={"margin-top":10, "margin-left":0}),width=2)
        ], align="start", justify="end"),
        dbc.Row([
            dbc.Col(dcc.Graph(id="main-indicator"), width={"size":8,"offset":2}),
        ],align="center"),
        dbc.Row([
            dbc.Col(dbc.Card(html.H3(children='BreakDown',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-4 mb-4")
        ]),
        dbc.Row([
            dbc.Col(html.H3("Select View:"),width=3),
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
        ], align="center", justify="center"),

        dbc.Row([
            dbc.Col(html.H5(children='Position by P/L', className="text-center"),
                            width={"size":2,"offset":2}, className="mt-4"),
            dbc.Col(html.H5(children='Position by Value', className="text-center"),
                            width={"size":2, "offset":4}, className="mt-4")
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id="bar_open"), width=6),
            dbc.Col(dcc.Graph(id="treemap_open"), width=6)
        ]),
        dbc.Row([
            dbc.Col(html.H5(children='P/L over Time', className="text-center"),
                            width=4, className="mt-4")
        ], justify="center"),
        dbc.Row([
            dbc.Col(dcc.Graph(id="line_open"), width=8),
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H4("Select Filters", className="text-center"),
                    html.Br(),
                    dcc.Dropdown(id ="type-dropdown-open", placeholder="Select Asset Class"),
                    html.Br(),
                    html.Br(),
                    dcc.Dropdown(id="symbol-dropdown", placeholder="Select Symbol",multi=True)

                ])), width=4)
        ]),
        dbc.Row([
            dbc.Col(dbc.Card(html.H3(children='Table',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-0 mb-4")
            ]),
        dbc.Row([
            dbc.Col(html.H5(children='Open Position(s)', className="text-center"),
                                width=6, className="mt-2")
            ], justify="center"),
        dbc.Row([
            dbc.Col(id="table-container-open", width=10)
        ], align="center", justify="center"),
        html.Br(),
        dbc.Row([
            dbc.Col(html.H5(children='Transactions', className="text-center"),
                                width=6, className="mt-2")
            ], justify="center"),
        dbc.Row([
            dbc.Col(id="transaction-container-open",width=10)
            ], align="center", justify="center"),
    ])
])

@app.callback(
    Output(component_id="type-dropdown-open", component_property="options"),
    Input(component_id="symbol-dropdown", component_property="value"),
    State(component_id="open-store", component_property="data")
)
def update_type_dropdown(value, open_position):
    if open_position == None:
        return None
    open_position = pd.DataFrame(open_position)

    options=[{"label":v, "value":v} for v in open_position["Type"].unique()]

    return options

@app.callback(
    Output(component_id="symbol-dropdown", component_property="options"),
    Input(component_id="type-dropdown-open", component_property="value"),
    State(component_id="open-store", component_property="data")
)
def update_ticker_dropdown(value, open_position):
    if open_position == None:
        return None
    open_position = pd.DataFrame(open_position)

    if value == None:
        options = [{"label":v, "value":v} for v in open_position["Symbol"].unique()]
    else:
        options = [{"label":v, "value":v} for v in open_position[open_position["Type"]==value]["Symbol"].unique()]

    return options

@app.callback(
    Output(component_id="main-indicator",component_property="figure"),
    Output(component_id="bar_open",component_property="figure"),
    Output(component_id="treemap_open",component_property="figure"),
    Output(component_id="line_open",component_property="figure"),
    Output(component_id="table-container-open",component_property="children"),
    Input(component_id="radios", component_property="value"),
    Input(component_id="type-dropdown-open", component_property="value"),
    Input(component_id="symbol-dropdown",component_property="value"),
    State(component_id="open-store", component_property="data"),
    State(component_id="historical-store", component_property="data"),
)
def update_graph(value, type, ticker_list, open_position, historical):
    if open_position == None or historical == None:
        return None, None, None, None, None

    open_position = pd.DataFrame(open_position)
    for dat in ["Date","Date_Open"]:
        open_position[dat] = pd.to_datetime(open_position[dat])

    historical = pd.DataFrame(historical)
    historical["Date"] = pd.to_datetime(historical["Date"])


    bar_fig = generate_bar(open_position, value)
    treemap_fig = generate_treemap(open_position, value)

    if type == None:
        line_fig = generate_line(historical, value,ticker_list)
    else:
        line_fig = generate_line(historical[historical["Type"]==type], value, None)

    indicator_fig = generate_indicator(open_position)
    table_fig = generate_table(open_position)


    return indicator_fig, bar_fig, treemap_fig, line_fig, table_fig

@app.callback(
    Output(component_id="transaction-container-open", component_property="children"),
    Input(component_id="table-open", component_property="selected_row_ids"),
    State(component_id="data-store", component_property="data"),
    State(component_id="open-store", component_property="data"),
)
def update_table(id, data, open_position):
    if data == None or open_position == None:
        return None
    data = pd.DataFrame(data)
    data["Date"] = pd.to_datetime(data["Date"])

    open_position = pd.DataFrame(open_position)
    for dat in ["Date","Date_Open"]:
        open_position[dat] = pd.to_datetime(open_position[dat])

    transaction_fig = generate_transaction(data,open_position ,id)

    return transaction_fig

@app.callback(
    Output(component_id="refresh-alert", component_property="children"),
    Output(component_id="refresh-alert", component_property="className"),
    Output(component_id = "refresh-url", component_property = "href"),
    Input(component_id="refresh-button", component_property="n_clicks"),
    Input(component_id="refresh-url", component_property="href"),
    prevent_initial_call=True,
)
def refresh_data(n_clicks, url):

    if n_clicks != None and n_clicks >= 1:
        response = requests.get("http://127.0.0.1:8000/api/refresh")
        return_url = "http://127.0.0.1:8050/portfolio/refresh" if url.endswith("portfolio") else "http://127.0.0.1:8050/portfolio"

        if response.status_code == 200:
            return dbc.Alert("Price successfully refreshed", color="Primary"), "alert alert-success", return_url
        else:
            return dbc.Alert("Price failed to refresh, please try again later", color="danger"), "alert alert-danger", return_url
    else:
        raise PreventUpdate
