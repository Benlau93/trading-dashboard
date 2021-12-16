from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from dash import dash_table
from app import app

# read in open position
df = pd.read_excel("Transaction Data.xlsx", sheet_name="Open Position", parse_dates=["Date"])


# define template used
TEMPLATE = "plotly_white"

# main kpi
def generate_indicator(df):
    df_ = df.copy()
    unrealised_pl = df_["P/L (SGD)"].sum()
    unrealised_pl_per = df_["P/L (SGD)"].sum() / df_["Amount (SGD)"].sum()
    total_position = df_["Name"].nunique()

    indicator_fig = go.Figure()
    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=unrealised_pl,
                        title = "Unrealized P/L",
                        number = dict(valueformat="$,.2f"),
                        domain={"row":0, "column":0})
    )

    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=unrealised_pl_per,
                        title = "Unrealized P/L (%)",
                        number = dict(valueformat=".2%"),
                        domain={"row":1, "column":0})
    )
    indicator_fig.add_trace(
        go.Indicator(mode="number",
                        value=total_position,
                        title = "Total Position",
                        domain={"row":2, "column":0})
    )

    indicator_fig.update_layout(
        grid= {"rows":3, "columns":1},
        height=600,
        template=TEMPLATE
    )

    return indicator_fig


def generate_bar(df):
    pl_by_name = df.sort_values("Date")[["Name","P/L (SGD)"]].rename({"P/L (SGD)":"P/L"}, axis=1)

    pl_by_name["P/L"] = pl_by_name["P/L"].map(lambda x: round(x,2))
    pl_by_name["TEXT"] = pl_by_name["P/L"].map(lambda x:  "-$" + str(abs(x)) if x<0 else "$" + str((x)))

    bar_fig = go.Figure()
    bar_fig.add_trace(
        go.Bar(x=pl_by_name["Name"],y=pl_by_name["P/L"], text=pl_by_name["TEXT"], textposition="outside")
    )
    bar_fig.update_layout(
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=False, showticklabels=False),
                        margin=dict(t=0),
                        template=TEMPLATE                 
    )

    return bar_fig

def generate_stacked_bar(df):
    position_by_pl = df[["Type","Name","P/L (SGD)"]].copy()
    position_by_pl["P/L"] = position_by_pl["P/L (SGD)"].map(lambda x: "Profit" if x>=0 else "Loss")
    position_by_pl = position_by_pl.groupby(["Type","P/L"])[["Name"]].nunique().rename({"Name":"No. of Open Position"}, axis=1).reset_index()

    stack_bar = go.Figure()
    stack_bar.add_trace(
        go.Bar(x=position_by_pl[position_by_pl["P/L"]=="Profit"]["Type"], y=position_by_pl[position_by_pl["P/L"]=="Profit"]["No. of Open Position"], name="No. of Position (Profit)", text=position_by_pl[position_by_pl["P/L"]=="Profit"]["No. of Open Position"])
    )
    stack_bar.add_trace(
        go.Bar(x=position_by_pl[position_by_pl["P/L"]=="Loss"]["Type"], y=position_by_pl[position_by_pl["P/L"]=="Loss"]["No. of Open Position"], name="No. of Position (Loss)", text=position_by_pl[position_by_pl["P/L"]=="Loss"]["No. of Open Position"])
    )
    stack_bar.update_layout(barmode='stack',
                            yaxis=dict(showgrid=False, showticklabels=False),
                            legend=dict(x=0.02,y=0.95),
                            margin=dict(t=0),
                            template=TEMPLATE
    )



    return stack_bar

def generate_table(df):
    df_ = df.copy()
    df_ = df_.rename({"Previous Close":"Current Price",
                    "Avg Price":"Price",
                    "Value (SGD)":"Value",
                    "P/L (SGD)":"Unrealised P/L",
                    "P/L (%)":"Unrealised P/L (%)",
                    "Weightage":"% of Portfolio"}, axis=1)
    df_ = df_[["Name","Price","Current Price","Unrealised P/L","Unrealised P/L (%)","Value","Holdings (days)","% of Portfolio"]].sort_values(["Unrealised P/L"])
    
    # formatting
    money = dash_table.FormatTemplate.money(2)
    percentage = dash_table.FormatTemplate.percentage(2)

    table_fig = dash_table.DataTable(
        id="table",
        columns = [
            dict(id="Name", name="Name"),
            dict(id="Price", name="Price",type="numeric",format=money),
            dict(id="Current Price", name="Current Price",type="numeric",format=money),
            dict(id="Unrealised P/L", name="Unrealised P/L",type="numeric",format=money),
            dict(id="Unrealised P/L (%)", name="Unrealised P/L (%)",type="numeric",format=percentage),
            dict(id="Value", name="Value",type="numeric",format=money),
            dict(id="Holdings (days)", name="Holdings (days)"),
            dict(id="% of Portfolio", name="% of Portfolio",type="numeric",format=percentage),
        ],
        data=df_.to_dict('records'),
        sort_action="native",
        style_cell={
        'height': 'auto',
        'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
        'whiteSpace': 'normal'},
        style_table={'overflowX': 'scroll'},
        style_as_list_view=True,
    )

    return table_fig


indicator_fig = generate_indicator(df)
bar_fig = generate_bar(df)
stacked_bar_fig = generate_stacked_bar(df)
table_fig = generate_table(df)

layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(html.H1("Portfolio",className="card-title"))), width={"size":8,"offset":1}, align="center", className="mt-2"),
            dbc.Col(dbc.Button("Add Transaction",color="success",href="/portfolio/add",style=dict(margin=10)),width={"size":3})
        ],align="center"),
        dbc.Row([
            dbc.Col(dcc.Graph(id="indicator_open", figure=indicator_fig), width=4, align="centre"),
            dbc.Col(dcc.Graph(id="bar_open", figure=bar_fig),width=8, align="center")
        ]),
            dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='Breakdown',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-0 mb-4")
            ]),
        dbc.Row([
            dbc.Col(table_fig, width={"size":10,"offset":1})
        ], align="center")
    ])
])