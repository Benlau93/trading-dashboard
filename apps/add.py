from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output
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
        dbc.Col([dbc.Input(type="text", id="price-input", placeholder="Enter Price",required=True)], width=6)
    ], align="center")
], className="mb-3")

qty_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Quantity: "), width={"size":2,"offset":2}),
        dbc.Col([dbc.Input(type="text", id="qty-input", placeholder="Enter Quantity",required=True)], width=6)
    ], align="center")
], className="mb-3")

fees_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Fees: "), width={"size":2,"offset":2}),
        dbc.Col([dbc.Input(type="text", id="fees-input", placeholder="Enter Fees",required=True)], width=6)
    ], align="center")
], className="mb-3")

er_input = html.Div([
    dbc.Row([
        dbc.Col(dbc.Label("Exchange Rate: "), width={"size":2,"offset":2}),
        dbc.Col([dbc.Input(type="text", id="er-input", placeholder="Enter Exchange Rate", value=1)], width=6)
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
        dbc.Col(dbc.Button("Add Transaction", color="success"),width=6)
    ], align="center", justify="center")
])


layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(
                dbc.Card(dbc.CardBody([
                html.P("Add Transaction Data"),
                html.Br(),
                date_input,
                sym_input,
                price_input,
                qty_input,
                fees_input,
                er_input,
                action_input,
                button
            ]))
            ,width={"size":8,"offset":2})
        ])

    ])
], style={"display":"block","text-align":"center"})