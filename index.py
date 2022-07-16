from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from app import app
from apps import dashboard, portfolio, add, analysis, dividend
from datetime import date
import requests
import pandas as pd

# building the navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Dashboard", href="/")),
        dbc.NavItem(dbc.NavLink("Portfolio", href="/portfolio")),
        dbc.NavItem(dbc.NavLink("Dividend", href="/dividend")),
        dbc.NavItem(dbc.NavLink("Analysis", href="/analysis")),
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

    return data.to_dict(orient="records"), closed.to_dict(orient="records"), open_position.to_dict(orient="records"), historical.to_dict(orient="records")


        

# embedding the navigation bar
def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        navbar,
        html.Div(id='page-content'),

        dcc.Store(id="data-store"),
        dcc.Store(id="closed-store"),
        dcc.Store(id="open-store"),
        dcc.Store(id="historical-store")
    ])
app.layout = serve_layout

@app.callback(
    Output(component_id='page-content', component_property='children'),
    Output(component_id='data-store', component_property='data'),
    Output(component_id='closed-store', component_property='data'),
    Output(component_id='open-store', component_property='data'),
    Output(component_id='historical-store', component_property='data'),
    Input(component_id='url', component_property='pathname')
)
def display_page(pathname):
    if pathname == '/portfolio':
        layout = portfolio.layout
    elif pathname == "/portfolio/refresh":
        layout =  portfolio.layout
    elif pathname == "/portfolio/add":
        layout =  add.layout
    elif pathname == "/dividend":
        layout = dividend.layout
    elif pathname == "/analysis":
        layout =  analysis.layout
    else:
        layout = dashboard.layout

    # load data
    print("RETRIEVE DATA FROM BACKEND API")
    data, closed, open_position, historical = load_data()

    return layout, data, closed, open_position, historical 
    
@app.callback(
    Output(component_id="download-dataframe-xlsx", component_property="data"),
    Input(component_id="export-button",component_property="n_clicks"),
    State(component_id='data-store', component_property='data'),
    State(component_id='closed-store', component_property='data'),
    State(component_id='open-store', component_property='data'),
    prevent_initial_call=True,
)
def export_data(n_clicks, data, closed, open_position):
    if data != None and closed != None and open_position != None:
        data = pd.DataFrame(data).drop("DATE", axis=1)
        closed = pd.DataFrame(closed).drop(["Date","DATE"], axis=1)
        open_position = pd.DataFrame(open_position).drop("Date", axis=1)

        def to_xlsx(bytes_io):
            xlsx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
            data.to_excel(xlsx_writer, index=False, sheet_name="Transaction")
            closed.to_excel(xlsx_writer, index=False, sheet_name="Closed Position")
            open_position.to_excel(xlsx_writer, index=False, sheet_name="Open Position")
            xlsx_writer.save()

        return dcc.send_bytes(to_xlsx, "Trading Dashboard.xlsx")



# start server
if __name__ == '__main__':
    app.run_server(debug=True)