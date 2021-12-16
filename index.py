from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from app import app
from apps import historical, portfolio, add

# building the navigation bar
dropdown = dbc.DropdownMenu(
    children=[
        dbc.DropdownMenuItem("Home", href="/"),
    ],
    nav = True,
    in_navbar = True,
    label = "Explore",
)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Dashboard", href="/")),
        dbc.NavItem(dbc.NavLink("Portfolio", href="/portfolio")),

    ],
    brand="TRADING DASHBOARD",
    brand_href="/",
    color="primary",
    dark=True
)

# embedding the navigation bar
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/portfolio':
        return portfolio.layout
    elif pathname == "/portfolio/add":
        return add.layout
    return historical.layout




# start server
if __name__ == '__main__':
    app.run_server(debug=True)