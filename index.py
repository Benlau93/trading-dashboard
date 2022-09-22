from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from app import app
from apps import dashboard, portfolio, add, analysis, dividend, watchlist, add_watchlist
from datetime import date
import requests
import pandas as pd
from dash.exceptions import PreventUpdate
from dash import callback_context

# building the navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Portfolio", href="/")),
        dbc.NavItem(dbc.NavLink("Watchlist", href="/watchlist")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Dividend", href="/dividend"),
                dbc.DropdownMenuItem("Historical Trades", href="/trading"),
                dbc.DropdownMenuItem("Trade Anaylsis", href="/analysis"),

            ],
            nav=True,
            in_navbar=True,
            label="History"
        ),
        dbc.NavItem(dbc.NavLink("Export",id="export-button", href="/")),
        dcc.Download(id="download-dataframe-xlsx"),

    ],
    brand="TRADING DASHBOARD",
    brand_href="/",
    color="primary",
    dark=True
)


# load data

def load_data():
    # ticker information
    tickerinfo = requests.get("http://127.0.0.1:8000/api/ticker")
    tickerinfo = pd.DataFrame.from_dict(tickerinfo.json())
    tickerinfo["type"] = tickerinfo["type"] + " - " + tickerinfo["currency"].str[:-1]
    type_map = tickerinfo[["symbol","type"]].drop_duplicates()

    # transactional data
    data = requests.get("http://127.0.0.1:8000/api/transaction")
    data = pd.DataFrame.from_dict(data.json())
    data = pd.merge(data, tickerinfo, on="symbol")
    data.columns = data.columns.str.capitalize()
    data["Date"] = pd.to_datetime(data["Date"], format="%Y-%m-%d")
    data["DATE"] = data["Date"].dt.strftime("%b-%y")

    # closed position
    closed = requests.get("http://127.0.0.1:8000/api/closed")
    closed = pd.DataFrame.from_dict(closed.json())
    closed = pd.merge(closed, tickerinfo, on="symbol")
    closed.columns = closed.columns.str.capitalize()
    closed["Date"] = pd.to_datetime(closed["Date_close"], format="%Y-%m-%d")
    closed["DATE"] = closed["Date"].dt.strftime("%b-%y")
    closed = closed.rename({
                            "Pl_sgd":"P/L (SGD)",
                            "Pl_per":"P/L (%)",
                            "Holding":"Holding (days)",
                            "Date_close":"Date_Close",
                            "Date_open":"Date_Open",
                            "Id":"id"}, axis=1)

    # open position
    open_position = requests.get("http://127.0.0.1:8000/api/open")
    open_position = pd.DataFrame.from_dict(open_position.json())
    open_position = pd.merge(open_position, tickerinfo, on="symbol")
    open_position.columns = open_position.columns.str.capitalize()
    open_position["Date"] = pd.to_datetime(open_position["Date_open"], format="%Y-%m-%d")
    # get holdings
    open_position["Total_holding"] = (pd.to_datetime(date.today()) - open_position["Date"]).dt.days
    open_position = open_position.rename({
        "Id":"id",
        "Total_value_sgd": "Amount (SGD)",
        "Total_quantity":"Total Quantity",
        "Date_open":"Date_Open"
    }, axis=1)


    # historical pl
    historical = requests.get("http://127.0.0.1:8000/api/historical")
    historical = pd.DataFrame.from_dict(historical.json())
    historical = pd.merge(historical, type_map, on="symbol")
    historical.columns = historical.columns.str.capitalize()
    historical["Date"] = pd.to_datetime(historical["Date"], format="%Y-%m-%d")
    historical = historical.rename({
        "Pl_sgd":"Unrealised P/L",
    }, axis=1)
    historical = pd.merge(historical,open_position[["Symbol","Amount (SGD)"]], on="Symbol")
    current_price = historical.sort_values(["Symbol","Date"]).groupby("Symbol").tail(1)[["Symbol","Unrealised P/L","Price"]]

    # update open position current price
    open_position = pd.merge(open_position, current_price)
    open_position["Unrealised P/L (%)"] = open_position["Unrealised P/L"] / open_position["Amount (SGD)"]
    open_position["Value"] = open_position["Amount (SGD)"] + open_position["Unrealised P/L"]


    # import dividend
    dividend_df = requests.get("http://127.0.0.1:8000/api/dividend")
    dividend_df = pd.DataFrame.from_dict(dividend_df.json())
    dividend_df["date_dividend"] = pd.to_datetime(dividend_df["date_dividend"], format="%Y-%m-%d")
    # join to ticker to get currency
    dividend_df = pd.merge(dividend_df, tickerinfo[["symbol","currency"]], on="symbol")
    dividend_df.columns = dividend_df.columns.str.capitalize()

    # import watchlist
    watchlist_df = requests.get("http://127.0.0.1:8000/api/watchlist")
    watchlist_df = pd.DataFrame.from_dict(watchlist_df.json())
    watchlist_df.columns = watchlist_df.columns.str.capitalize()

    return data.to_dict(orient="records"), closed.to_dict(orient="records"), open_position.to_dict(orient="records"), historical.to_dict(orient="records"), dividend_df.to_dict(orient="records"), watchlist_df.to_dict(orient="records")


        

# embedding the navigation bar
def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=True),
        html.Div(id="refresh-alert",style={"font-size":"large", "font-family": "Arial, Helvetica, sans-serif","text-align":"center"}),
        navbar,
        html.Div(
            dbc.Row(
                dbc.Col(dbc.Button("Refresh Dashboard",id="refresh-button",color="warning", style={"margin":"5px"}),width=2)
                , align="start", justify="start")
            ),
        html.Div(id='page-content'),

        dcc.Store(id="data-store"),
        dcc.Store(id="closed-store"),
        dcc.Store(id="open-store"),
        dcc.Store(id="historical-store"),
        dcc.Store(id="dividend-store"),
        dcc.Store(id="watchlist-store")
    ])

app.layout = serve_layout


@app.callback(
    Output(component_id='page-content', component_property='children'),
    Output(component_id='data-store', component_property='data'),
    Output(component_id='closed-store', component_property='data'),
    Output(component_id='open-store', component_property='data'),
    Output(component_id='historical-store', component_property='data'),
    Output(component_id='dividend-store', component_property='data'),
    Output(component_id="watchlist-store", component_property="data"),
    Input(component_id='url', component_property='pathname')
)
def display_page(pathname):
    if pathname == '/trading':
        layout = dashboard.layout
    elif pathname == "/portfolio/add":
        layout =  add.layout
    elif pathname == "/dividend":
        layout = dividend.layout
    elif pathname == "/analysis":
        layout =  analysis.layout
    elif pathname == "/watchlist":
        layout = watchlist.layout
    elif pathname == "/watchlist/add":
        layout = add_watchlist.layout
    else:
        layout = portfolio.layout

    # load data
    print("RETRIEVE DATA FROM BACKEND API")
    data, closed, open_position, historical, dividend_df, watchlist_df = load_data()

    return layout, data, closed, open_position, historical, dividend_df, watchlist_df


@app.callback(
    Output(component_id="refresh-alert", component_property="children"),
    Output(component_id="refresh-alert", component_property="className"),
    Output(component_id='url', component_property='pathname'),
    Input(component_id="refresh-button", component_property="n_clicks"),
    prevent_initial_call=True
)
def refresh_data(n_clicks):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if "refresh-button" in changed_id:

        # refresh data
        # portfolio
        response = requests.get("http://127.0.0.1:8000/api/refresh")
        if response.status_code == 200:
            print("Updated Portfolio Sucessfully")
        else:
            print("Failed to updated Portfolio")

        # dividend
        dividend_response = requests.get("http://127.0.0.1:8000/api/refresh-dividend")
        if dividend_response.status_code == 200:
            print("Updated Dividend Sucessfully")
        else:
            print("Failed to update Dividend")

        # watchlist
        watchlist_response = requests.get("http://127.0.0.1:8000/api/refresh-watchlist")
        if watchlist_response.status_code == 200:
            print("Updated Watchlist Sucessfully")
        else:
            print("Failed to update Watchlist")

        if response.status_code == 200:
            return dbc.Alert("Price successfully refreshed", color="Primary"), "alert alert-success", "http://127.0.0.1:8050/"
        else:
            return dbc.Alert("Price failed to refresh, please try again later", color="danger"), "alert alert-danger", "http://127.0.0.1:8050/"
    else:
        raise PreventUpdate
    
@app.callback(
    Output(component_id="download-dataframe-xlsx", component_property="data"),
    Input(component_id="export-button",component_property="n_clicks"),
    prevent_initial_call=True,
)
def export_data(n_clicks):

    # ticker information
    tickerinfo = requests.get("http://127.0.0.1:8000/api/ticker")
    tickerinfo = pd.DataFrame.from_dict(tickerinfo.json())

    # transaction
    data = requests.get("http://127.0.0.1:8000/api/transaction")
    data = pd.DataFrame.from_dict(data.json())

    # closed position
    closed = requests.get("http://127.0.0.1:8000/api/closed")
    closed = pd.DataFrame.from_dict(closed.json())

    # open position
    open_position = requests.get("http://127.0.0.1:8000/api/open")
    open_position = pd.DataFrame.from_dict(open_position.json())

    # dividend
    dividend_df = requests.get("http://127.0.0.1:8000/api/dividend")
    dividend_df = pd.DataFrame.from_dict(dividend_df.json())

    def to_xlsx(bytes_io):
        xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
        tickerinfo.to_excel(xlsx_writer, index=False, sheet_name="Ticker")
        data.to_excel(xlsx_writer, index=False, sheet_name="Transaction")
        closed.to_excel(xlsx_writer, index=False, sheet_name="Closed Position")
        open_position.to_excel(xlsx_writer, index=False, sheet_name="Open Position")
        dividend_df.to_excel(xlsx_writer, index=False, sheet_name="Dividend")
        xlsx_writer.save()

    return dcc.send_bytes(to_xlsx, "Trading Dashboard.xlsx")



# start server
if __name__ == '__main__':
    app.run_server(debug=True)