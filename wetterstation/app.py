# Import required libraries
import os
import pickle
import copy
import pathlib
import dash
import datetime as dt
import pandas as pd
import numpy as np
from dash.exceptions import PreventUpdate # TODO: remove
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
from scipy.stats import rayleigh
from config import *
from get_data import *
from helpers import *

from controls import COUNTIES, WELL_STATUSES, WELL_TYPES, WELL_COLORS


# DEBUGGER
import pdb



# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
GRAPH_INTERVAL = os.environ.get("GRAPH_INTERVAL", 5000)


external_stylesheets = ["https://fonts.googleapis.com/css?family=Montserrat:300,400,500,600,700,800,900&display=swap"]

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    external_stylesheets=external_stylesheets,
)
#server = app.server


app.title = "Wetterstation für Segler"
app.index_string = """
<!DOCTYPE html>
<html lang="de-CH">
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer class="footer">
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

# Create controls
# county_options = [
#     {"label": str(COUNTIES[county]), "value": str(county)}
#         for county in COUNTIES
# ]





app_color = {
    "graph_bg": "#ffffff",
    "graph_gridline": "#EDEDED",
    "graph_line": "#007ACE",
    "transparent": "rgba(255, 255, 255, 0)",
}

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=40, r=10, b=40, t=40),
    hovermode="closest",
    plot_bgcolor=app_color["graph_bg"],
    paper_bgcolor=app_color["graph_bg"],
    legend=dict(font=dict(size=10), orientation="h"),
    #title="Satellite Overview",
    # mapbox=dict(
    #     accesstoken=mapbox_access_token,
    #     style="light",
    #     center=dict(lon=-78.05, lat=42.54),
    #     zoom=7,
    # ),
)

# Create app layout
app.layout = html.Div(
    [
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        dcc.Interval(
            id="update-interval",
            interval=int(GRAPH_INTERVAL),
            n_intervals=0,
        ),

        # Weather icon
        html.Div(
            [
                html.Img(src="assets/images/sunny.svg"),
            ],
            className="weather-icon",
        ),

        # Section (Intro)
        html.Div(
            [
                # Header
                html.Div(
                    [
                        html.Div(
                            [
                                html.H1(
                                    "Hallo stürmischer Tag!",
                                ),
                            ],
                            className="header__title",
                            id="header-title",
                        ),
                        # Controller
                        html.Div(
                            [
                                dcc.RadioItems(
                                    id="station_selector",
                                    options=[
                                        {"label": "Mythenquai ", "value": "mythenquai"},
                                        {"label": "Tiefenbrunnen ", "value": "tiefenbrunnen"},
                                    ],
                                    value="mythenquai",
                                    labelStyle={"display": "inline-block"},
                                    className="station_controller",
                                ),
                                # dcc.Dropdown(
                                #     id="well_types",
                                #     options=well_type_options,
                                #     multi=True,
                                #     value=list(WELL_TYPES.keys()),
                                #     className="dcc_control",
                                # ),
                            ],
                            className="controller",
                            id="cross-filter-options",
                        ),
                    ],
                    id="header",
                    className="header"
                ),

            ],
            className="section section--intro"
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Graph(
                                    id="air_temperature",
                                    figure=dict(
                                        layout=dict(
                                            plot_bgcolor=app_color["graph_bg"],
                                            paper_bgcolor=app_color["graph_bg"],
                                        )
                                    ),
                                ),
                                html.Figure(
                                    [
                                        html.Div([
                                            html.Span(id="mean_air_temperature_text", className="value"),
                                            html.Span(["°C"], className="unit"),
                                        ]),
                                        html.Figcaption(["Lufttemperatur"], className="figcaption"),
                                    ],
                                    className="figure figure--mean-air-temperature",
                                ),
                                html.Figure(
                                    [
                                        html.Div([
                                            html.Span(id="air_temperature_text", className="value"),
                                            html.Span(["°C"], className="unit"),
                                        ]),
                                        html.Figcaption(["Lufttemperatur"], className="figcaption"),
                                    ],
                                    className="figure figure--last-air-temperature",
                                ),
                            ],
                            className="box box--general",
                        ),
                        html.Div(
                            [
                                html.Figure(
                                    [
                                        html.Div([
                                            html.Span(id="windchill_text", className="value"),
                                            html.Span(id="windchill_past_text", className="past-value"),
                                            html.Span(["°C"], className="unit"),
                                        ]),
                                        html.Figcaption(["Windchill"], className="figcaption"),
                                    ],
                                    className="figure figure--last-windchill",
                                ),
                            ],
                            className="box box--general",
                        ),
                        html.Div(
                            [
                                html.Figure(
                                    [
                                        html.Div([
                                            html.Span(id="water_temperature_text", className="value"),
                                            html.Span(["°C"], className="unit"),
                                        ]),
                                        html.Figcaption(["Wassertemperatur"], className="figcaption"),
                                    ],
                                    className="figure figure--last-water-temperature",
                                ),
                            ],
                            className="box box--general",
                        ),
                        html.Div(
                            [
                                html.Figure(
                                    [
                                        html.Div([
                                            html.Span(id="humidity_text", className="value"),
                                            html.Span(["%"], className="unit"),
                                        ]),
                                        html.Figcaption(["Luftfeuchtigkeit"], className="figcaption"),
                                    ],
                                    className="figure figure--last-humidity",
                                ),
                            ],
                            className="box box--general",
                        ),
                        html.Div(
                            [
                                html.Figure(
                                    [
                                        html.Div([
                                            html.Span(id="dew_point_text", className="value"),
                                            html.Span(["°C"], className="unit"),
                                        ]),
                                        html.Figcaption(["Taupunkt"], className="figcaption"),
                                    ],
                                    className="figure figure--dew-point",
                                ),
                            ],
                            className="box box--general",
                        ),
                        html.Div(
                            [
                                html.Figure(
                                    [
                                        html.Div([
                                            html.Span(id="barometric_pressure_qfe_text", className="value"),
                                            html.Span(["hPa"], className="unit"),
                                        ]),
                                        html.Figcaption(["Luftdruck"], className="figcaption"),
                                    ],
                                    className="figure figure--dew-point",
                                ),
                            ],
                            className="box box--general",
                        ),
                    ],
                    className="section__inner section__inner--general"
                ),
            ],
            className="section section--general"
        ),
        html.Div(
            [
                # Prosa
                html.Div(
                    [
                        # Text about …
                        html.Div(
                            [
                                html.H3("Titel 1"),
                                html.P("Das ist der Prosa-Text, der sich dann anpassen lässt und auch etwas länger sein wird, weil er eine Progrnosse macht"),
                                html.Ul(
                                    [
                                        html.Li("Windgeschwindigkeit"),
                                        html.Li("Böenspitzen"),
                                        html.Li("Lufttemperatur"),
                                    ],
                                    className="prosa__list",
                                ),
                            ],
                            className="box box--prosa",
                        ),
                        # Text about …
                        html.Div(
                            [
                                html.H3("Titel der auch"),
                                html.P("Das ist der Prosa-Text, der sich dann anpassen lässt und auch etwas länger sein wird, weil er eine Progrnosse macht"),
                                html.Ul(
                                    [
                                        html.Li("Böenspitzen"),
                                    ],
                                    className="prosa__list",
                                ),
                            ],
                            className="box box--prosa",
                        ),
                        html.Div(
                            [
                                html.H3("Starkwindwarnung"),
                                html.P(id="strong_wind_warning_text"),
                                # Das ist der Prosa-Text, der sich dann anpassen lässt und auch etwas länger sein wird, weil er eine Progrnosse macht
                                html.Ul(
                                    [
                                        html.Li("Windgeschwindigkeit"),
                                        html.Li("Böenspitzen"),
                                    ],
                                    className="prosa__list",
                                ),
                            ]
                        ),
                    ],
                    className="section__inner section__inner--prosa",
                    id="prosa",
                ),
            ],
            className="section section--prosa",
        ),
        html.Div(
            [
                html.Div(
                    [
                        # Wind speed
                        html.Div(
                            [
                                # html.Div(
                                #     [
                                #         html.Div("WIND SPEED (MPH)",
                                #             className="graph__title")
                                #     ]
                                # ),
                                dcc.Graph(
                                    id="wind-speed",
                                    figure=dict(
                                        layout=dict(
                                            plot_bgcolor=app_color["graph_bg"],
                                            paper_bgcolor=app_color["graph_bg"],
                                        )
                                    ),
                                ),
                                # dcc.Interval(
                                #     id="wind-speed-update",
                                #     interval=int(GRAPH_INTERVAL),
                                #     n_intervals=0,
                                # ),
                            ],
                            className="figure figure--wind-speed",
                        ),
                        # Wind histogramm
                        html.Div(
                            [
                                dcc.Graph(
                                    id="wind-histogram",
                                    figure=dict(
                                        layout=dict(
                                            plot_bgcolor=app_color["graph_bg"],
                                            paper_bgcolor=app_color["graph_bg"],
                                        )
                                    ),
                                ),
                            ],
                            id="windGraphContainer",
                            className="figure figure--wind-histogram",
                        ),
                        # Wind speed rose
                        html.Div(
                            [
                                dcc.Graph(
                                    id="wind-direction",
                                    figure=dict(
                                        layout=dict(
                                            plot_bgcolor=app_color["graph_bg"],
                                            paper_bgcolor=app_color["graph_bg"],
                                        )
                                    ),
                                ),
                            ],
                            id="gustGraphContainer",
                            className="figure figure--wind-rose",
                        ),
                    ],
                    className="section__inner section__inner--wind"
                ),
            ],
            className="section section--wind",
        ),
    ],
    id="main",
    className="main",
)















# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
)





@app.callback(
    Output("air_temperature_text", "children"), [Input("update-interval", "n_intervals")],
)
def update_air_temperature_text(interval):

    df = get_last_data()
    last_air_temperature = df["last_air_temperature"]

    return last_air_temperature



@app.callback(
    Output("mean_air_temperature_text", "children"), [Input("update-interval", "n_intervals")],
)
def update_mean_air_temperature_text(interval):

    df = get_all_data("7d")
    mean_air_temperature = round(df["air_temperature"].mean(), 2)

    return mean_air_temperature


#
# @app.callback(
#     [Output("windchill_text", "children")],
#     [Input("update-interval", "n_intervals")],
# )
# def update_windchill_text(interval):
#
#     df = get_last_data()
#     last_windchill = df["last_windchill"]
#
#     return last_windchill
#




@app.callback(
    [
        Output("windchill_text", "children"),
        Output("windchill_past_text", "children"),
    ],
    [Input("update-interval", "n_intervals")],
)
def update_windchill_texts(interval):

    df = get_last_data()
    last_windchill = df["last_windchill"]

    return last_windchill, "guguseli"



@app.callback(
    Output("water_temperature_text", "children"), [Input("update-interval", "n_intervals")],
)
def update_water_temperature_text(interval):

    df = get_last_data()
    last_water_temperature = df["last_water_temperature"]

    return last_water_temperature




@app.callback(
    Output("humidity_text", "children"), [Input("update-interval", "n_intervals")],
)
def update_humidity_text(interval):

    df = get_last_data()
    last_humidity = df["last_humidity"]

    return last_humidity




@app.callback(
    Output("dew_point_text", "children"), [Input("update-interval", "n_intervals")],
)
def update_dew_point_text(interval):

    df = get_last_data()
    last_dew_point = df["last_dew_point"]

    return last_dew_point





@app.callback(
    Output("barometric_pressure_qfe_text", "children"), [Input("update-interval", "n_intervals")],
)
def update_barometric_pressure_qfe_text(interval):

    df = get_last_data()
    last_barometric_pressure_qfe = df["last_barometric_pressure_qfe"]

    return last_barometric_pressure_qfe






# Selectors -> air temperature graph
# @app.callback(
#     Output("air_temperature_graph", "figure")
# )
# def make_air_temperature_figure():
#
#     layout_count = copy.deepcopy(layout)
#
#     dataframeli = get_air_temperature()
#     x = dataframeli["air_temperature"].index
#     # y0 = dataframeli["air_temperature"].index
#     y1 = dataframeli["air_temperature"]
#
#     trace_air_temperature = dict(
#         type="box",
#         y=y1,
#         x=x,
#         name='',
#         marker_color='#FF4136'
#     )
#
#     data = [trace_air_temperature]
#
#     # return {
#     #     'data': data,
#     #     'layout': go.Layout(
#     #         title='Lufttemperatur in Celsius'
#     #     )
#     # }
#
#     return dict(data=data, layout=layout_count)
#
# # Selectors -> water temperature graph
# @app.callback(
#     Output("water_temperature_graph", "figure")
# )
# def make_water_temperature_figure():
#
#     layout_count = copy.deepcopy(layout)
#     dataframeli = get_water_temperature()
#
#     # colors = []
#     # for i in range(1960, 2018):
#     #     if i >= int(year_slider[0]) and i < int(year_slider[1]):
#     #         colors.append("rgb(123, 199, 255)")
#     #     else:
#     #         colors.append("rgba(123, 199, 255, 0.2)")
#
#     data = [
#         dict(
#             type="scatter",
#             mode="lines",
#             #x=df_air_temperature.index,
#             #y=df_air_temperature["air_temperature"],
#             x=dataframeli.index,
#             y=dataframeli["water_temperature"],
#             name="Wassertemperatur in Celsius",
#             line=dict(shape="spline", smoothing=2, width=1, color="#fac1b7"),
#             marker=dict(color=colors),
#         ),
#         # dict(
#         #     # type="bar",
#         #     # mode="lines",
#         #     x=decomp_air_temperature.trend.index,
#         #     y=decomp_air_temperature.trend,
#         #     # name="Lufttemperatur in Celsius",
#         #     # line=dict(shape="spline", smoothing=2, width=1, color="#fac1b7"),
#         #     marker=dict(color=colors),
#         # ),
#         # dict(
#         #     type="scatter",
#         #     mode="lines",
#         #     x=df_water_temperature.index,
#         #     y=df_water_temperature["water_temperature"],
#         #     name="Wassertemperatur in Celsius",
#         #     marker=dict(color=colors),
#         # )
#     ]
#
#     layout_count["title"] = "Wassertemperatur in Celsius"
#     layout_count["dragmode"] = "select"
#     layout_count["showlegend"] = False
#     layout_count["autosize"] = True
#
#     figure = dict(data=data, layout=layout_count)
#     return figure
#
#



@app.callback(
    Output("strong_wind_warning_text", "children"), [Input("update-interval", "n_intervals")],
)
def update_strong_wind_warning_text(interval):

    #df = get_last_data()
    #last_barometric_pressure_qfe = df["strong_wind_warning_text"]

    return dt.datetime.now()








@app.callback(
    Output("air_temperature", "figure"), [Input("update-interval", "n_intervals")]
)
def gen_air_temperature(interval):
    """
    Generate the wind speed graph.
    :params interval: update the graph based on an interval
    """

    df = get_single_column("air_temperature", "6h")

    trace_speed = dict(
        type="scatter",
        y=df["air_temperature"].values,
        x=df.index,
        line={"color": "#42C4F7"},
        hoverinfo="skip",
        # error_y={
        #     "type": "data",
        #     "array": df["wind_gust_max_10min"],
        #     "thickness": 1.5,
        #     "width": 2,
        #     "color": "#B4E8FC",
        # },
        mode="lines+markers",
    )

    layout = dict(
        plot_bgcolor=app_color["transparent"],
        paper_bgcolor=app_color["transparent"],
        margin=dict(l=0, r=10, b=40, t=20),
        hovermode="closest",
        showlegend=False,
        height=160,

        xaxis={
            "showgrid": False,
            "zeroline": False,
            "gridcolor": app_color["graph_gridline"],
            "tickformat": "%H:%M",
            "side": "top",
        },
        yaxis={
            "showgrid": False,
            "showline": True,
            "fixedrange": False,
            "zeroline": False,
            "title": "m/s",
            "gridcolor": app_color["graph_gridline"],
            #"nticks": max(5, round(df["wind_speed_avg_10min"].iloc[-1] / 6)),
        },
    )

    return dict(data=[trace_speed], layout=layout)






@app.callback(
    Output("wind-speed", "figure"), [Input("update-interval", "n_intervals")]
)
def gen_wind_speed(interval):
    """
    Generate the wind speed graph.
    :params interval: update the graph based on an interval
    """

    df = get_wind_data("4h")
    max_wind_speed_in_serie = df["wind_speed_avg_10min"].max()
    max_wind_gust_in_serie = df["wind_gust_max_10min"].max()

    trace_speed = dict(
        type="scatter",
        y=df["wind_speed_avg_10min"],
        line={"color": "#42C4F7"},
        hoverinfo="skip",
        # error_y={
        #     "type": "data",
        #     "array": df["wind_gust_max_10min"],
        #     "thickness": 1.5,
        #     "width": 2,
        #     "color": "#B4E8FC",
        # },
        mode="lines",
    )

    trace_gust = dict(
        type="scatter",
        y=df["wind_gust_max_10min"],
        line={"color": "#42C4F7"},
        hoverinfo="skip",
        # error_y={
        #     "type": "data",
        #     "array": df["wind_gust_max_10min"],
        #     "thickness": 1.5,
        #     "width": 2,
        #     "color": "#B4E8FC",
        # },
        mode="lines",
        opacity=0.5,
    )

    layout = dict(
        plot_bgcolor=app_color["graph_bg"],
        paper_bgcolor=app_color["graph_bg"],
        #font={"color": "#000000"},


        #autosize=True,
        #automargin=True,
        margin=dict(l=40, r=10, b=40, t=20),
        hovermode="closest",
        #legend=dict(font=dict(size=10), orientation="v"),
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "xanchor": "center",
            "y": 1,
            "x": 0.5,
        },
        #showlegend=False,
        height=350,
        #width='100%',
        #title="Windgeschwindigkeit in Metern pro Sekunde",

        #showticklabels=True,

        xaxis={
            "range": [0, 24],
            "showline": True,
            "zeroline": False,
            "fixedrange": True,
            "tickvals": [0, 6, 12, 18, 24],
            "ticktext": ["4", "3", "2", "1", "0"],
            "title": "Verstrichene Zeit in Stunden",
            #"nticks": 5,
            "gridcolor": app_color["graph_gridline"],
        },
        yaxis={
            "range": [
                0,
                max(max_wind_gust_in_serie + 1, max_wind_speed_in_serie + 1),
            ],
            "showgrid": True,
            "showline": True,
            "fixedrange": False,
            "zeroline": False,
            "title": "m/s",
            "gridcolor": app_color["graph_gridline"],
            #"nticks": max(5, round(df["wind_speed_avg_10min"].iloc[-1] / 6)),
        },
    )

    return dict(data=[trace_speed, trace_gust], layout=layout)



@app.callback(
    Output("wind-direction", "figure"), [Input("update-interval", "n_intervals")]
)
def gen_wind_direction(interval):
    """
    Generate the wind direction graph.
    :params interval: update the graph based on an interval
    """

    df = get_wind_data("4h")
    max_wind_speed_in_serie = df["wind_speed_avg_10min"].max()

    val = df["wind_speed_avg_10min"].iloc[-1]
    direction = [0, (df["wind_direction"][0] - 20), (df["wind_direction"][0] + 20), 0]



    traces_scatterpolar = [
        {"r": [0, val, val, 0], "fillcolor": "#084E8A"},
        {"r": [0, val * 0.65, val * 0.65, 0], "fillcolor": "#B4E1FA"},
        {"r": [0, val * 0.3, val * 0.3, 0], "fillcolor": "#EBF5FA"},
    ]

    data = [
        dict(
            type="scatterpolar",
            r=traces["r"],
            theta=direction,
            mode="lines",
            fill="toself",
            fillcolor=traces["fillcolor"],
            line={"color": "rgba(32, 32, 32, .6)", "width": 1},
        )
        for traces in traces_scatterpolar
    ]

    layout = dict(
        height=300,
        margin=dict(l=40, r=10, b=40, t=20),
        hovermode="closest",
        legend=dict(font=dict(size=10), orientation="v"),
        showlegend=False,
        plot_bgcolor=app_color["graph_bg"],
        paper_bgcolor=app_color["graph_bg"],
        font={"color": "#000"},
        autosize=False,
        polar={
            "bgcolor": app_color["graph_line"],
            "radialaxis": {"range": [0, max_wind_speed_in_serie], "angle": 45, "dtick": 10},
            "angularaxis": {"showline": False, "tickcolor": "white"},
        },
    )

    return dict(data=data, layout=layout)






@app.callback(
    Output("wind-histogram", "figure"),
    [Input("update-interval", "n_intervals")],
    [
        State("wind-speed", "figure"),
    ],
)
def gen_wind_histogram(interval, wind_speed_figure):
    """ TODO: check comment
    Genererate wind histogram graph.
    :params interval: upadte the graph based on an interval
    :params wind_speed_figure: current wind speed graph
    :params slider_value: current slider value
    :params auto_state: current auto state
    """

    wind_val = []

    try:
        # Check to see whether wind-speed has been plotted yet
        if wind_speed_figure is not None:
            wind_val = wind_speed_figure["data"][0]["y"]
        # if "Auto" in auto_state:
        #     bin_val = np.histogram(
        #         wind_val,
        #         bins=range(int(round(min(wind_val))), int(round(max(wind_val)))),
        #     )
        # else:
        #     bin_val = np.histogram(wind_val, bins=slider_value)
        #     print('bin_val: {}'.format(bin_val))

        bin_val = np.histogram(
            wind_val,
            #bins=range(int(round(min(wind_val))), int(round(max(wind_val)))),
        )

    except Exception as error:
        raise PreventUpdate

    #
    # dataframeli = get_wind_data("72h")
    # wind_vals = dataframeli["wind_force_avg_10min"].values
    #
    # print(wind_val)
    # print(wind_val[0])
    #
    # print(wind_vals)
    # print(wind_vals[0])

    avg_val = float(sum(wind_val)) / len(wind_val)
    median_val = np.median(wind_val)

    pdf_fitted = rayleigh.pdf(
        bin_val[1], loc=(avg_val) * 0.55, scale=(bin_val[1][-1] - bin_val[1][0]) / 3
    )

    y_val = (pdf_fitted * max(bin_val[0]) * 20,)
    y_val = (pdf_fitted * max(bin_val[0]), 0)
    #print('y_val: {}'.format(y_val))
    y_val_max = max(y_val[0])
    bin_val_max = max(bin_val[0])

    trace = dict(
        type="bar",
        x=bin_val[1],
        y=bin_val[0],
        marker={"color": app_color["graph_line"]},
        showlegend=True,
        hoverinfo="x+y",
    )

    traces_scatter = [
        {"line_dash": "dash", "line_color": "#2E5266", "name": "Average"},
        {"line_dash": "dot", "line_color": "#BD9391", "name": "Median"},
    ]

    scatter_data = [
        dict(
            type="scatter",
            x=[bin_val[int(len(bin_val) / 2)]],
            y=[0],
            mode="lines",
            line={"dash": traces["line_dash"], "color": traces["line_color"]},
            marker={"opacity": 0},
            visible=True,
            name=traces["name"],
        )
        for traces in traces_scatter
    ]

    trace3 = dict(
        type="scatter",
        mode="lines",
        line={"color": "#42C4F7"},
        y=y_val[0],
        x=bin_val[1][: len(bin_val[1])],
        name="Rayleigh Fit",
    )
    layout = dict(
        height=350,
        margin=dict(l=40, r=0, b=40, t=20),
        plot_bgcolor=app_color["graph_bg"],
        paper_bgcolor=app_color["graph_bg"],
        font={"color": "#000"},
        xaxis={
            "title": "Windgeschwindigkeit (m/s)",
            "showgrid": False,
            "showline": False,
            "fixedrange": True,
        },
        yaxis={
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "title": "Number of Samples",
            "fixedrange": True,
        },
        #autosize=True,
        bargap=0.01,
        bargroupgap=0,
        hovermode="closest",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "xanchor": "center",
            "y": 1,
            "x": 0.5,
        },
        shapes=[
            {
                "xref": "x",
                "yref": "y",
                "y1": int(max(bin_val_max, y_val_max)) + 0.5,
                "y0": 0,
                "x0": avg_val,
                "x1": avg_val,
                "type": "line",
                "line": {"dash": "dash", "color": "#2E5266", "width": 5},
            },
            {
                "xref": "x",
                "yref": "y",
                "y1": int(max(bin_val_max, y_val_max)) + 0.5,
                "y0": 0,
                "x0": median_val,
                "x1": median_val,
                "type": "line",
                "line": {"dash": "dot", "color": "#BD9391", "width": 5},
            },
        ],
    )
    return dict(data=[trace, scatter_data[0], scatter_data[1], trace3], layout=layout)





# Main
if __name__ == "__main__":
    app.run_server(debug=True)
