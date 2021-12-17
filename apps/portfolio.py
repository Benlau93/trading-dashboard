from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output
from dash import dash_table
from app import app
import math

# read in open position
df = pd.read_excel("Transaction Data.xlsx", sheet_name="Open Position", parse_dates=["Date"])


# define template used
TEMPLATE = "plotly_white"

# total portfolio value
current_value = df["Value (SGD)"].sum()
buy_in_amount = df["Amount (SGD)"].sum()

main_indicator = go.Figure()
main_indicator.add_trace(
    go.Indicator(mode="number+delta", title="Total Portfolio Value",value=current_value, number = dict(valueformat="$,.2f"),delta={"reference":buy_in_amount,"position":"bottom","valueformat":"$,.2f"})
)

main_indicator.update_layout(
        height=300,
        template=TEMPLATE
)

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


def generate_bar_line(df):
    pl_by_name = df.sort_values("Date")[["Name","P/L (SGD)","P/L (%)"]].rename({"P/L (SGD)":"P/L"}, axis=1)

    pl_by_name["P/L"] = pl_by_name["P/L"].map(lambda x: round(x,2))
    pl_by_name["TEXT"] = pl_by_name["P/L"].map(lambda x:  "-$" + str(abs(x)) if x<0 else "$" + str((x)))
    pl_by_name["P/L (%)"] = pl_by_name["P/L (%)"].map(lambda x: round(x*100,2))
    pl_by_name["TEXT_%"] = pl_by_name["P/L (%)"].map(lambda x:  "-" + str(abs(x)) + "%" if x<0 else str(x)+ "%")

    bar_line_fig = make_subplots(specs=[[{"secondary_y": True}]])
    bar_line_fig.add_trace(
        go.Bar(x=pl_by_name["Name"],y=pl_by_name["P/L"], text=pl_by_name["TEXT"], textposition="inside", yaxis="y1",name="P/L")
    )

    bar_line_fig.add_trace(
        go.Scatter(x=pl_by_name["Name"],y=pl_by_name["P/L (%)"], text=pl_by_name["TEXT_%)"], name="P/L (%)",mode="lines+markers+text",textposition="bottom left",yaxis="y2"),
        secondary_y=True
    )
    # handle axis
    GRIDLINES = 4
    
    y1_min = pl_by_name["P/L"].min()
    y1_max = pl_by_name["P/L"].max()

    if y1_min < 0:
        y1_range = y1_max - y1_min
    else:
        y1_range = y1_max

    y1_range = y1_range * 1000 
    y1_len = len(str(math.floor(y1_range)))

    y1_pow10_divisor = math.pow(10, y1_len - 1)
    y1_firstdigit = math.floor(y1_range / y1_pow10_divisor)
    y1_max_base = y1_pow10_divisor * y1_firstdigit / 1000

    y1_dtick = y1_max_base / GRIDLINES

    y1_pow10_divisor = math.pow(10, y1_len - 1) / 1000 
    y1_range = y1_range / 1000


    y2_min = pl_by_name["P/L (%)"].min()
    y2_max = pl_by_name["P/L (%)"].max()

    if y2_min < 0:
        y2_range = y2_max - y2_min
    else:
        y2_range = y2_max

    y2_range = y2_range * 1000
    y2_len = len(str(math.floor(y2_range)))

    y2_pow10_divisor = math.pow(10, y2_len - 1)
    y2_firstdigit = math.floor(y2_range / y2_pow10_divisor)
    y2_max_base = y2_pow10_divisor * y2_firstdigit / 1000  

    y2_dtick = y2_max_base / GRIDLINES

    y2_pow10_divisor = math.pow(10, y2_len - 1) / 1000 
    y2_range = y2_range / 1000


    y1_dtick_ratio = y1_range / y1_dtick
    y2_dtick_ratio = y2_range / y2_dtick

    global_dtick_ratio = max(y1_dtick_ratio, y2_dtick_ratio)


    negative = False

    if y1_min < 0:
        negative = True
        y1_negative_ratio = abs(y1_min / y1_range) * global_dtick_ratio
    else:
        y1_negative_ratio = 0

    if y2_min < 0:
        negative = True
        y2_negative_ratio = abs(y2_min / y2_range) * global_dtick_ratio
    else:
        y2_negative_ratio = 0

    global_negative_ratio = max(y1_negative_ratio, y2_negative_ratio) + 0.1

    if negative:
        y1_range_min = (global_negative_ratio) * y1_dtick * -1
        y2_range_min = (global_negative_ratio) * y2_dtick * -1
    else:
        y1_range_min = 0
        y2_range_min = 0

    y1_positive_ratio = abs(y1_max / y1_range) * global_dtick_ratio
    y2_positive_ratio = abs(y2_max / y2_range) * global_dtick_ratio

    global_positive_ratio = max(y1_positive_ratio, y2_positive_ratio) + 0.1

    y1_range_max = (global_positive_ratio) * y1_dtick
    y2_range_max = (global_positive_ratio) * y2_dtick


    bar_line_fig.update_layout(
                        xaxis=dict(showgrid=False),
                        margin=dict(t=0),
                        legend=dict(x=0.02,y=0.95),
                        template=TEMPLATE                 
    )
    bar_line_fig.update_yaxes(secondary_y=True, showgrid=False, zeroline=False, showticklabels=False, range=[y2_range_min, y2_range_max])
    bar_line_fig.update_yaxes(secondary_y=False, showgrid=False, zeroline=True, showticklabels=False, zerolinecolor="black", range=[y1_range_min, y1_range_max])


    return bar_line_fig

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

def generate_treemap(df):
    value_by_name = df[["Type","Name","Value (SGD)","P/L (SGD)"]].rename({"P/L (SGD)":"P/L","Value (SGD)":"Value"}, axis=1)
    for col in ["Value","P/L"]:
        value_by_name[col] = value_by_name[col]
    value_by_name[col] = value_by_name[col].map(lambda x: round(x,2))


    treemap_fig = px.treemap(value_by_name, path=[px.Constant("Holdings"),"Type","Name"], values="Value", color="P/L" ,
                                                    color_continuous_scale="RdBu",
                                                    range_color = [value_by_name["P/L"].min(), value_by_name["P/L"].max()],
                                                    hover_data = {"Name":True,"P/L":True,"Value":True})
    treemap_fig.update_layout(margin = dict(t=0), template=TEMPLATE)


    return treemap_fig


def generate_table(df):
    df_ = df.copy()
    df_ = df_.rename({"Previous Close":"Current Price",
                    "Avg Price":"Price",
                    "Value (SGD)":"Value",
                    "P/L (SGD)":"Unrealised P/L",
                    "P/L (%)":"Unrealised P/L (%)",
                    "Weightage":"% of Portfolio",
                    "Shares":"Qty"}, axis=1)
    df_ = df_[["Name","Date","Qty","Price","Current Price","Unrealised P/L","Unrealised P/L (%)","Value","Holdings (days)","% of Portfolio"]].sort_values(["Unrealised P/L"])
    
    # formatting
    df_["Date"] = df_["Date"].dt.date
    money = dash_table.FormatTemplate.money(2)
    percentage = dash_table.FormatTemplate.percentage(2)

    table_fig = dash_table.DataTable(
        id="table",
        columns = [
            dict(id="Name", name="Name"),
            dict(id="Date", name="Date"),
            dict(id="Qty", name="Qty"),
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
bar_line_fig = generate_bar_line(df)
stacked_bar_fig = generate_stacked_bar(df)
table_fig = generate_table(df)
treemap_fig = generate_treemap(df)

layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(dcc.Graph(id="main-indicator",figure=main_indicator), width={"size":6,"offset":3}),
            dbc.Col(dbc.Button("Add Transaction",color="success",href="/portfolio/add",style=dict(margin=10)),width={"size":3}, align="start")
        ],align="center"),

        dbc.Row([
            dbc.Col(dcc.Graph(id="indicator_open", figure=indicator_fig), width=4, align="centre"),
            dbc.Col(dcc.Graph(id="bar_open", figure=bar_line_fig),width=8, align="center")
        ]),
        dbc.Row([
            dbc.Col(html.H5(children='Holdings by Value', className="text-center"),
                            width={"size":4,"offset":4}, className="mt-4"),
            # dbc.Col(html.H5(children='No. of P/L Position by Asset Types', className="text-center"), width=8, className="mt-4"),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id="treemap_open",figure=treemap_fig), width={"size":8,"offset":2})
            # dbc.Col(dcc.Graph(id="stacked_bar_open", figure=stacked_bar_fig), width=4)
        ]),
            dbc.Row([
                dbc.Col(dbc.Card(html.H3(children='Table',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-0 mb-4")
            ]),
        dbc.Row([
            dbc.Col(table_fig, width={"size":10,"offset":1})
        ], align="center")
    ])
])
