from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from app import app
import requests

# define template used
TEMPLATE = "plotly_white"


def generate_kpi(df):
    total_dividend = df["Dividend_adjusted"].sum()
    dividend_per = df["Dividend_per"].sum()

    # generate indicator
    indicator_fig = go.Figure()
    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=total_dividend,
                        title = "Total Dividend",
                        number = dict(valueformat="$,.02f"),
                        domain={"row":0, "column":0})
    )

    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=dividend_per,
                        title = "Cumulative Dividend (%)",
                        number = dict(valueformat=".01%"),
                        domain={"row":0, "column":1})
    )

    
    indicator_fig.update_layout(
        grid= {"rows":1, "columns":2},
        height=250,
        template=TEMPLATE
    )

    return indicator_fig


def generate_grp_bar(df):
    df_ = df.groupby("Symbol").sum()[["Dividend_adjusted","Dividend_per"]].reset_index()
    df_ = df_.sort_values("Symbol")

    # generate bar chart
    bar_fig = make_subplots(specs=[[{"secondary_y": True}]])

    bar_fig.add_trace(
        go.Bar(x = df_["Symbol"], y = df_["Dividend_adjusted"], name="Dividend", textposition="inside", texttemplate="%{y:$,.0f}",offsetgroup=1)
        
    )

    bar_fig.add_trace(
        go.Bar(x = df_["Symbol"], y = df_["Dividend_per"], name="Dividend (%)", textposition="inside", texttemplate="%{y:.01%}",offsetgroup=2),
        secondary_y=True
    )

    bar_fig.update_yaxes(tickformat="$,.0f", title = "Dividend",showgrid=False, secondary_y = False)
    bar_fig.update_yaxes(tickformat=".01%", title = "Cumulative Dividend (%)",showgrid=False, secondary_y=True)

    bar_fig.update_layout(
        showlegend=False,
        height = 500,
        template= TEMPLATE
    )

    return bar_fig

def generate_line(df, value):

    # get year month
    df["YEARMONTH"] = df["Date_dividend"].dt.strftime("%b-%Y")
    df["YEAR"] = df["Date_dividend"].dt.year

    # define y
    y = "Dividend_adjusted" if value == "Absolute" else "Dividend_per"
    tickformat = "$,.02f" if value == "Absolute" else ".02%"
    textemplate = "%{y:$,.02f}" if value == "Absolute" else "%{y:.02%}"
    
    # get cumulative dividend
    df_ = df.groupby(["YEAR","YEARMONTH"]).sum()[[y]].reset_index()
    df_["SORT"] = pd.to_datetime(df_["YEARMONTH"], format="%b-%Y")
    df_ = df_.sort_values("SORT")
    df_["Cumulative Dividend"] = df_.groupby("YEAR").cumsum()[y]

    # line_fig = go.Figure()
    line_fig = go.Figure()
    
    line_fig.add_trace(
        go.Scatter(x=[df_["YEAR"].tolist(), df_["YEARMONTH"].tolist()], y=df_["Cumulative Dividend"], name="Cumulative Dividend",mode="lines+markers+text", texttemplate=textemplate, textposition="bottom right")
    )
    line_fig.add_trace(
        go.Bar(x=[df_["YEAR"].tolist(), df_["YEARMONTH"].tolist()], y=df_[y], name="Dividend", marker_color = "#2E8B57", opacity=0.5)

    )

    # add line for each year
    years = df_["YEAR"].unique()
    for year in years:
        x = df_[df_["YEAR"]==year].tail(1)["YEARMONTH"].iloc[0]
        line_fig.add_vline(x=[[year],[x]], line_width=2, line_dash="dash", line_color="black")

    line_fig.update_layout(yaxis=dict(title="Dividend",tickformat=tickformat),
                            xaxis = dict(showgrid=False),
                            legend=dict(x=0.05,y=0.9),
                            height=800,
                            template=TEMPLATE
    )
    return line_fig


layout = html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Div( className="mt-0 mb-4"))
            ]),
            dbc.Row([
                dbc.Col([html.H5("Year:")],width={"size":1 , "offset":1}, align="center"),
                dbc.Col([dcc.Dropdown(id='dividend-date',placeholder="Filter by Year" )],width={"size":2,"offset":0}, align="center"),
                dbc.Col([html.H5("Exchange:")],width={"size":2, "offset":1}, align="center"),
                dbc.Col([dcc.Dropdown(options=[{"label":"SG","value":"SGD"}, {"label":"US","value":"USD"}],id='dividend-exchange',placeholder="Filter by Exchange" )],width={"size":2,"offset":0}, align="center")
            ], justify="center"),
            dbc.Row([
                dbc.Col([dcc.Graph(id="dividend-indicator")], width={"size": 10, "offset": 1})]),
            dbc.Row([
                dbc.Col([dcc.Graph(id="dividend-bar")], width=10)], justify="center"),
            dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='Breakdown',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-0 mb-4")
            ]),
            
            dbc.Row([
                dbc.Col(html.H5("Select Dividend Ticker"),width=3, align="center")
            ], justify = "center"),
            dbc.Row([
                dbc.Col(dcc.Dropdown(id="dividend-selector", placeholder="Ticker"),width=3, align="center")
            ], justify = "center"),
            dbc.Row([
                dbc.Col([dcc.Graph(id="sub-indicator")], width={"size": 10, "offset": 1})]),
            dbc.Row([
                dbc.Col([dcc.Graph(id="dividend-line")], width=10)], justify="center"),
            dbc.Row([
                dbc.Col([
                    dbc.RadioItems(
                        id="dividend-radios",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-info",
                        labelCheckedClassName="active",
                        options=[
                            {"label": "Absolute", "value": "Absolute"},
                            {"label": "Percentage", "value": "Percentage"}
                        ], value="Absolute")]
                    , width={"size":3,"offset":4})]),
    ])
])

@app.callback(
    Output(component_id="dividend-date", component_property="options"),
    Input(component_id="url", component_property="pathname"),
    State(component_id="dividend-store", component_property="data")
)
def update_date_dropdown(_, dividend_df):
    dividend_df = pd.DataFrame(dividend_df)
    dividend_df["Date_dividend"] = pd.to_datetime(dividend_df["Date_dividend"])
    dividend_df = dividend_df.sort_values("Date_dividend", ascending=False)
    date_options = [{"label":d, "value":d} for d in dividend_df["Date_dividend"].dt.year.unique()]

    return date_options 

@app.callback(
    Output(component_id="dividend-selector", component_property="options"),
    Output(component_id="dividend-selector", component_property="value"),
    Input(component_id="url", component_property="pathname"),
    State(component_id="dividend-store", component_property="data")
)
def update_ticker_dropdown(_, dividend_df):
    dividend_df = pd.DataFrame(dividend_df)
    dividend_df.sort_values(["Symbol"])

    selector_options = [{"label":d, "value":d} for d in dividend_df["Symbol"].unique()]
    highest_dividend = dividend_df.groupby("Symbol").sum()[["Dividend_adjusted"]].reset_index().sort_values("Dividend_adjusted", ascending=False)["Symbol"].iloc[0]

    return selector_options, highest_dividend

@app.callback(
    Output(component_id="dividend-indicator", component_property="figure"),
    Output(component_id="dividend-bar", component_property="figure"),
    Input(component_id="dividend-date", component_property="value"),
    Input(component_id="dividend-exchange", component_property="value"),
    State(component_id="dividend-store", component_property="data")
)
def generate_graph(year, exchange, dividend_df):
    dividend_df = pd.DataFrame(dividend_df)
    dividend_df["Date_dividend"] = pd.to_datetime(dividend_df["Date_dividend"])
    dividend_filtered = dividend_df.copy()

    # filter year
    if year != None:
        year = int(year)
        dividend_filtered = dividend_df[dividend_df["Date_dividend"].dt.year==year].copy()

    if exchange != None:
        dividend_df = dividend_df[dividend_df["Currency"]==exchange].copy()
        dividend_filtered = dividend_filtered[dividend_filtered["Currency"]==exchange].copy()

    # generate graph
    indicator_fig = generate_kpi(dividend_filtered)
    bar_fig  = generate_grp_bar(dividend_filtered)

    return indicator_fig, bar_fig


@app.callback(
    Output(component_id="sub-indicator", component_property="figure"),
    Output(component_id="dividend-line", component_property="figure"),
    Input(component_id="dividend-selector", component_property="value"),
    Input(component_id="dividend-radios", component_property="value"),
    State(component_id="dividend-store", component_property="data")
)
def generate_breakdown_graph(symbol, value, dividend_df):
    dividend_df = pd.DataFrame(dividend_df)
    dividend_df["Date_dividend"] = pd.to_datetime(dividend_df["Date_dividend"])

    # filter symvol
    dividend_df = dividend_df[dividend_df["Symbol"]==symbol].copy()

    # generate graph
    indicator_fig = generate_kpi(dividend_df)
    line_fig = generate_line(dividend_df, value)

    return indicator_fig,line_fig