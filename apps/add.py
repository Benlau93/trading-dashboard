from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output, State
from app import app
from datetime import date


date_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Date:"), width={"size":2,"offset":2}),
        dbc.Col(dcc.DatePickerSingle(
            id="date-picker",
            min_date_allowed=date(2015, 1, 1),
            max_date_allowed=date.today(),
            initial_visible_month=date.today(),
            date=date.today(),
            display_format='DD-MMM-YYYY'
    ), width=2)
    ], align="center")
], className="mb-3")

sym_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Symbol: "), width={"size":2,"offset":2}),
        dbc.Col([dbc.Input(type="text", id="sym-input", placeholder="Enter Symbol",required=True),
        dbc.FormText(
            "Enter Ticker's Symbol recognised by Yahoo Finance"
        )], width=6)
    ], align="center")
], className="mb-3")

price_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Price: "), width={"size":2,"offset":2}),
        dbc.Col([dbc.Input(type="number", id="price-input", placeholder="Enter Price",required=True)], width=6)
    ], align="center")
], className="mb-3")

qty_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Quantity: "), width={"size":2,"offset":2}),
        dbc.Col([dbc.Input(type="number", id="qty-input", placeholder="Enter Quantity",required=True)], width=6)
    ], align="center")
], className="mb-3")

fees_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Fees: "), width={"size":2,"offset":2}),
        dbc.Col([dbc.Input(type="number", id="fees-input", placeholder="Enter Fees",value=0)], width=6)
    ], align="center")
], className="mb-3")

er_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Exchange Rate: "), width={"size":2,"offset":2}),
        dbc.Col([dbc.Input(type="number", id="er-input", placeholder="Enter Exchange Rate", value=1)], width=6)
    ], align="center")
], className="mb-3")

action_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Action: "), width={"size":2,"offset":2}),
        dbc.Col([ dbc.RadioItems(
            options=[
                {"label": "Buy", "value": "Buy"},
                {"label": "Sell", "value": "Sell"}
            ],
            value="Buy",
            id="action-input",
            labelCheckedClassName="text-primary",
            inputCheckedClassName="border border-info bg-info",
        )], width=2)
    ], align="center")
], className="mb-3")

button = html.Div([
    dbc.Row([
        dbc.Col(dbc.Button("Add Transaction", id="button",color="success",type="submit"),width=6)
    ], align="center", justify="center")
])

form = dbc.Form([
    date_input,
    sym_input,
    price_input,
    qty_input,
    fees_input,
    er_input,
    action_input,
    button
], id="form")

layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody([
                html.P("Add Transaction Data"),
                html.Br(),
                form
            ]))
            ,width={"size":8,"offset":2})
        ]),
        dbc.Row([
            dbc.Col(html.P(id="TEST"))
        ])

    ])
], style={"display":"block","text-align":"center"})

@app.callback(
    Output(component_id="TEST", component_property="children"),
    Input(component_id="form", component_property="n_submit"),
    State(component_id="date-picker", component_property="date"),
    State(component_id="sym-input", component_property="value"),
    State(component_id="price-input", component_property="value"),
    State(component_id="qty-input", component_property="value"),
    State(component_id="fees-input", component_property="value"),
    State(component_id="er-input", component_property="value"),
    State(component_id="action-input", component_property="value"),
    prevent_initial_call=True,
)
def submit_form(n_submit, date, sym, price, qty, fees, er, action):
    print(n_submit, date, sym, price, qty, fees, er, action)