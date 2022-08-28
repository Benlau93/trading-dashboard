from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from app import app
from datetime import date
import requests



sym_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Symbol: "), width={"size":2,"offset":2}),
        dbc.Col([dbc.Input(type="text", id="sym-input-watch", placeholder="Enter Symbol",required=True),
        dbc.FormText(
            "Enter Ticker's Symbol recognised by Yahoo Finance"
        )], width=6)
    ], align="center")
], className="mb-3")

price_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Target Price: "), width={"size":2,"offset":2}),
        dbc.Col([dbc.Input(type="number", id="price-input-watch", placeholder="Enter Target Price",required=True)], width=6)
    ], align="center")
], className="mb-3")

direction_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Direction: "), width={"size":2,"offset":2}),
        dbc.Col([ dbc.RadioItems(
            options=[
                {"label": "Above Target", "value": "Above"},
                {"label": "Below Target", "value": "Below"}
            ],
            value="Below",
            id="direction-input-watch",
            labelCheckedClassName="text-primary",
            inputCheckedClassName="border border-info bg-info",
        )], width=3)
    ], align="center")
], className="mb-3")

button = html.Div([
    dbc.Row([
        dbc.Col(dbc.Button("Add Watchlist", id="watch-button",color="success",type="submit"),width=6)
    ], align="center", justify="center")
])


form = dbc.Form([
    sym_input,
    price_input,
    direction_input,
    button
], id="form-watch")

layout = html.Div([
    html.Div(id="form-alert-watch",style={"font-size":"large", "font-family": "Arial, Helvetica, sans-serif"}),
    dbc.Row([
            dbc.Col(html.Div( className="mt-0 mb-4"))
        ]),
    dbc.Container([
        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody([
                html.P("Add Watchlist", style={"font-size":"xx-large", "font-family": "Arial, Helvetica, sans-serif"}),
                html.Br(),
                form
            ]))
            ,width={"size":8,"offset":2})
        ]),
        html.Br(),
        html.Br(),
        dbc.Row(
            dbc.Col(dbc.Button("Back to Watchlist", href="http://127.0.0.1:8050/watchlist", color ="info"), width=3)
        , align="center", justify = "center")

    ])
], style={"display":"block","text-align":"center"})


@app.callback(
    Output(component_id="form-alert-watch", component_property="children"),
    Output(component_id="form-alert-watch", component_property="className"),
    Output(component_id="sym-input-watch", component_property="value"),
    Output(component_id="price-input-watch", component_property="value"),
    Output(component_id="direction-input-watch", component_property="value"),
    Input(component_id="form-watch", component_property="n_submit"),
    State(component_id="sym-input-watch", component_property="value"),
    State(component_id="price-input-watch", component_property="value"),
    State(component_id="direction-input-watch", component_property="value"),
    prevent_initial_call=True,
)
def submit_form(n_submit, sym, price, direction):
    if n_submit != None:
        data = {
                "symbol":sym.upper(),
                "target_price":price,
                "direction":direction}

        response = requests.post("http://127.0.0.1:8000/api/watchlist",data=data)
        if response.status_code == 200:
            return dbc.Alert(f"Successfully added {sym.upper()} into Watchlist", color="Primary"), "alert alert-success", None, None, "Below"
        else:
            return dbc.Alert(f"Failed to add {sym.upper()} into Watchlist", color="danger"), "alert alert-danger", None, None, "Below"