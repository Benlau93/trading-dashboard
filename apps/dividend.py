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

# define template used
TEMPLATE = "plotly_white"


def generate_kpi(df):
    total_dividend = df["dividend_adjusted"].sum()
    total_value = df["share_value"].sum()
    dividend_yield = total_dividend / total_value

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
                        value=dividend_yield,
                        title = "Dividend Yield (%)",
                        number = dict(valueformat=".01%"),
                        domain={"row":0, "column":1})
    )

    
    indicator_fig.update_layout(
        grid= {"rows":1, "columns":2},
        height=250,
        template=TEMPLATE
    )

    return indicator_fig


def generate_line(df):

    # group by year
    df_ = df.groupby([df["date_dividend"].dt.year]).sum()[["dividend_adjusted"]].reset_index()


    # generate graph
    line_fig = go.Figure()
    
    line_fig.add_trace(
        go.Scatter(x=df_["date_dividend"], y=df_["dividend_adjusted"], name="Dividend",mode="lines+markers+text", texttemplate="%{y:$,.0f}", textposition="bottom right")
    )

    line_fig.update_layout(
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                height=500,
                template=TEMPLATE
    )
    return line_fig

layout = html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Div( className="mt-0 mb-4"))
            ]),
            dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='Dividend',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-0 mb-4")
            ]),
            dbc.Row([
                dbc.Col([html.H5("Year:")],width=2, align="center"),
                dbc.Col([dcc.Dropdown(id='dividend-date',placeholder="Filter by Year" )],width=3, align="center"),
                dbc.Col([html.H5("Exchange:")],width=2, align="center"),
                dbc.Col([dcc.Dropdown(options=[{"label":"SG","value":"SGD"}, {"label":"US","value":"USD"}],id='dividend-exchange',placeholder="Filter by Exchange" )],width=3, align="center")
            ], justify="center"),
            dbc.Row([
                dbc.Col([dcc.Graph(id="dividend-indicator")], width={"size": 10, "offset": 1})]),
            dbc.Row([
                dbc.Col([dcc.Graph(id="dividend-line")], width=10)], justify="center"),
    ])
])

@app.callback(
    Output(component_id="dividend-date", component_property="options"),
    Input(component_id="url", component_property="pathname"),
    State(component_id="dividend-store", component_property="data")
)
def update_date_dropdown(_, dividend_df):
    dividend_df = pd.DataFrame(dividend_df)
    dividend_df["date_dividend"] = pd.to_datetime(dividend_df["date_dividend"])
    dividend_df = dividend_df.sort_values("date_dividend", ascending=False)

    date_options = [{"label":d, "value":d} for d in dividend_df["date_dividend"].dt.year.unique()]

    return date_options

@app.callback(
    Output(component_id="dividend-indicator", component_property="figure"),
    Output(component_id="dividend-line", component_property="figure"),
    Input(component_id="dividend-date", component_property="value"),
    Input(component_id="dividend-exchange", component_property="value"),
    State(component_id="dividend-store", component_property="data")
)
def generate_graph(year, exchange, dividend_df):
    dividend_df = pd.DataFrame(dividend_df)
    dividend_df["date_dividend"] = pd.to_datetime(dividend_df["date_dividend"])
    dividend_filtered = dividend_df.copy()

    # filter year
    if year != None:
        year = int(year)
        dividend_filtered = dividend_df[dividend_df["date_dividend"].dt.year==year].copy()

    if exchange != None:
        dividend_df = dividend_df[dividend_df["currency"]==exchange].copy()
        dividend_filtered = dividend_filtered[dividend_filtered["currency"]==exchange].copy()

    # generate graph
    indicator_fig = generate_kpi(dividend_filtered)
    line_fig = generate_line(dividend_df)

    return indicator_fig, line_fig