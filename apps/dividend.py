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
                dbc.Col([html.H4("Select Year:")],width=3, align="center"),
                dbc.Col([dcc.Dropdown(id='dividend-date',placeholder="Filter by Year" )],width=3, align="center")
            ], justify="center"),
            dbc.Row([
                dbc.Col([dcc.Graph(id="dividend-indicator")], width={"size": 10, "offset": 1})]),
    ])
])


@app.callback(
    Output(component_id="dividend-indicator", component_property="figure"),
    Input(component_id="dividend-date", component_property="value"),
    State(component_id="dividend-store", component_property="data")
)
def generate_graph(year, dividend_df):
    dividend_df = pd.DataFrame(dividend_df)
    dividend_df["date_dividend"] = pd.to_datetime(dividend_df["date_dividend"])

    # generate graph
    indicator_fig = generate_kpi(dividend_df)

    return indicator_fig