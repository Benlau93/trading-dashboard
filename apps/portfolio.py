from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash.dash_table.Format import Format,Scheme
from app import app
import warnings
from datetime import timedelta

warnings.filterwarnings("ignore")

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


def generate_pie(df, view, value):
    VIEW = view
    df_ = df.groupby(VIEW).sum()[["Value"]].reset_index().sort_values("Value")
    df_["Value"] = df_["Value"].map(lambda x: round(x,2))
    textinfo = "label+value" if value == "Absolute" else "label+percent"

    # generate chart
    pie_fig = go.Figure()

    pie_fig.add_trace(
        go.Pie(labels = df_[VIEW], values = df_["Value"], textinfo= textinfo, name="Current Value",
        hole = 0.5, rotation = 35)
    )

    pie_fig.update_layout(
        template= TEMPLATE,
        height = 500,
        showlegend=False
    )

    return pie_fig



def generate_bar(df, view,value):
    VIEW = view
    FORMAT = "%{x:$,.2f}" if value == "Absolute" else "%{x:.2%}"
    df_ = df.groupby(VIEW).sum()[["Unrealised P/L","Amount (SGD)","Value"]].reset_index().sort_values("Unrealised P/L")

    if value != "Absolute":
        df_["Unrealised P/L"] = (df_["Value"] - df_["Amount (SGD)"]) / df_["Amount (SGD)"]

    df_ = df_.sort_values(["Unrealised P/L"])

    # generate chart
    bar_fig = go.Figure()
    bar_fig.add_trace(
        go.Bar(x=df_["Unrealised P/L"],y=df_[VIEW],texttemplate =FORMAT, textposition="inside",name="Unrealised P/L", hovertemplate="%{y}, "+FORMAT,
        orientation="h")
    )

    bar_fig.update_layout(
                        xaxis=dict(showgrid=False, zerolinecolor="black", tickformat="$,.0f" if value == "Absolute" else ".0%"),
                        yaxis=(dict(showgrid=False)),
                        height=500,
                        template=TEMPLATE                 
    )                

    return bar_fig


def generate_line(df, ticker_list):
    df_ = df.copy()
    df_["VALUE"] = df_["Amount (SGD)"] + df_["Unrealised P/L"]
    VIEW = "VALUE"
    FORMAT = "%{y:$,.0f}" 


    # get endofweek
    def get_endofweek(date):
        start = date - timedelta(days = date.weekday())
        end = start + timedelta(days=6)
    
        return end

    df_["endofweek"] = df_["Date"].map(get_endofweek)
    df_ = df_.sort_values(["Symbol","Date"])
    

    line_fig = go.Figure()

    if ticker_list == None or len(ticker_list) ==0:
        df_ = df_.groupby(["Symbol","endofweek"]).tail(1).groupby("endofweek").sum().reset_index()
        line_fig.add_trace(
            go.Scatter(x=df_["endofweek"], y=df_[VIEW], mode="lines+markers"
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
            df_filtered = df_[df_["Symbol"]==t].groupby(["Symbol","endofweek"]).tail(1).groupby("endofweek").sum().reset_index()
            
            line_fig.add_trace(
                go.Scatter(x=df_filtered["endofweek"], y=df_filtered[VIEW], mode="lines+markers", hovertemplate = "%{x}, " + FORMAT, name=t
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
        df_ = df_.sort_values("Date", ascending=False).copy()
    else:
        id = id[0].split("|")
        ticker, start = id[0], id[1]
        start = pd.to_datetime(start,format="%Y-%m-%d")
        df_ = df_[(df_["Symbol"]==ticker) & (df_["Date"] >= start)].sort_values("Date", ascending=False).copy()

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


def generate_waterfall(df, view, value):
    VIEW = view
    
    # generate total for each type
    df_ = df[["Type","Symbol","Unrealised P/L","Amount (SGD)","Value"]].rename({"Unrealised P/L":"Value","Value":"Current"}, axis=1).sort_values(["Type"])

    # get initial capital
    initial = df_.groupby("Type").sum()[["Amount (SGD)"]].rename({"Amount (SGD)":"Value"}, axis=1).reset_index()
    initial["Symbol"] = "Capital"
    
    # get pl
    GROUPBY = VIEW if VIEW == "Type" else ["Type","Symbol"]
    pl = df_.groupby(GROUPBY).sum()[["Value","Amount (SGD)"]].reset_index()

    if value != "Absolute":
        initial_ = initial.rename({"Value":"Initial"}, axis=1).drop("Symbol", axis=1)
        pl = pd.merge(initial_, pl, on = "Type")
        initial["Value"] = 1
        pl["Value"] = pl["Value"] / pl["Initial"]
        y_max = 1.05 + pl.groupby("Type").sum()["Value"].max()
    else:
        y_max = df_.groupby("Type").sum()["Current"].max() * 1.01 # define max y value

    # get final
    final = df_.groupby("Type").tail(1)
    final["Symbol"] = "Current Value"
    final["Value"] = None
 

    # combine
    combined = pd.concat([initial,pl, final], sort=True, ignore_index=True).sort_values(["Type"])
    measure_map = {"Capital":"absolute",
                    "Current Value":"total"}
    combined["Measure"] = combined["Symbol"].map(measure_map).fillna("relative")
    combined["Symbol"] = combined["Symbol"].fillna("P/L")
    combined["Value"] = combined["Value"].map(lambda x: round(x,2))
    combined = combined.sort_values(["Type","Measure"])

    # generate chart
    num_col = combined["Type"].nunique() 
    waterfall_fig = make_subplots(rows=1, cols=num_col)

    for v,c in zip(combined["Type"].unique(),list(range(num_col))):
        _ = combined[combined["Type"]==v].copy()
        waterfall_fig.add_trace(
            go.Waterfall(x = [_["Type"].tolist(),_["Symbol"].tolist()], y = _["Value"], measure = _["Measure"],base = 0,name=v),
            row = 1, col = c + 1
        )

    # update layout

    FORMAT = "$,.0f" if value == "Absolute" else ".0%"
    waterfall_fig.update_yaxes(showgrid=False, range = [0, y_max], tickformat=FORMAT)
    

    waterfall_fig.update_layout(
        showlegend=False,
        template = TEMPLATE,
        height = 500
    )

    return waterfall_fig

layout = html.Div([
    dbc.Container([
        dbc.Row([
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
            dbc.Col(html.H3("Select View:"),width={"size":3,"offset":1}),
            dbc.Col([
                dbc.RadioItems(
                    id="view-radios",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "Asset Class", "value": "Type"},
                        {"label": "Symbol", "value": "Symbol"}
                    ],
                    value="Type")
            ], width=4)
        ], align="center", justify="center"),
        dbc.Row([html.Div(style={"margin-top":20})]),
        dbc.Row([
            dbc.Col(html.H3("Select Value:"),width=3),
            dbc.Col([
                dbc.RadioItems(
                    id="value-radios",
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
        dbc.Row([html.Div(style={"margin-top":20})]),
        dbc.Row([
            dbc.Col(html.H5(children='Position by Current Value', className="text-center"),
                            width={"size":2,"offset":2}, className="mt-4"),
            dbc.Col(html.H5(children='Position by P/L', className="text-center"),
                            width={"size":2, "offset":4}, className="mt-4")
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id="pie_open"), width=6),
            dbc.Col(dcc.Graph(id="bar_open"), width=6)
        ]),
        dbc.Row([
            dbc.Col(html.H5(children='P/L by Asset Class', className="text-center"),
                            width=4, className="mt-4")
        ], justify="center"),
        dbc.Row([
            dbc.Col(dcc.Graph(id = "waterfall_open"), width= 12)
        ]),
        dbc.Row([html.Div(style={"margin-top":20})]),
        dbc.Row([
            dbc.Col(html.H5(children='Total Value over Time', className="text-center"),
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
    Output(component_id="pie_open",component_property="figure"),
    Output(component_id="bar_open",component_property="figure"),
    Output(component_id="waterfall_open",component_property="figure"),
    Output(component_id="line_open",component_property="figure"),
    Output(component_id="table-container-open",component_property="children"),
    Input(component_id="view-radios", component_property="value"),
    Input(component_id="value-radios", component_property="value"),
    Input(component_id="type-dropdown-open", component_property="value"),
    Input(component_id="symbol-dropdown",component_property="value"),
    State(component_id="open-store", component_property="data"),
    State(component_id="historical-store", component_property="data"),
)
def update_graph(view, value, type, ticker_list, open_position, historical):
    if open_position == None or historical == None:
        return None, None, None, None, None, None

    open_position = pd.DataFrame(open_position)
    for dat in ["Date","Date_Open"]:
        open_position[dat] = pd.to_datetime(open_position[dat])

    historical = pd.DataFrame(historical)
    historical["Date"] = pd.to_datetime(historical["Date"])


    bar_fig = generate_bar(open_position, view, value)
    pie_fig = generate_pie(open_position, view, value)
    waterfall_fig = generate_waterfall(open_position, view, value)

    if type == None:
        line_fig = generate_line(historical,ticker_list)
    else:
        line_fig = generate_line(historical[historical["Type"]==type], None)

    indicator_fig = generate_indicator(open_position)
    table_fig = generate_table(open_position)
    


    return indicator_fig ,pie_fig ,bar_fig, waterfall_fig, line_fig, table_fig

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


