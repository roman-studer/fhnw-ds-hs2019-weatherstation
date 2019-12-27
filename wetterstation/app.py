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
#from config import *
from get_data import *
from helpers import *
#from sklearn import preprocessing TODO: remove

from controls import COUNTIES, WELL_STATUSES, WELL_TYPES, WELL_COLORS


# DEBUGGER
import pdb



# get relative data folder


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
GRAPH_INTERVAL = os.environ.get("GRAPH_INTERVAL", 10000)

external_stylesheets = ["https://fonts.googleapis.com/css?family=Dosis:400,700&display=swap"]

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
        # Section (Header)
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
                                html.Div(
                                    [
                                        html.H1(
                                            ["Windkühle und Lufttemperatur"],
                                            className="box__title",
                                        ),
                                        dcc.Graph(
                                            id="air_temperature",
                                            figure=dict(
                                                layout=dict(
                                                    plot_bgcolor=app_color["graph_bg"],
                                                    paper_bgcolor=app_color["graph_bg"],
                                                )
                                            ),
                                        ),
                                    ],
                                    className="box__inner box__inner--title-and-graph box__inner--temperature-graphs",
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H2(
                                                    ["Aktuelle Werte"],
                                                    className="box__subtitle",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Div(
                                                            [
                                                                html.H3(
                                                                    ["Windkühle"],
                                                                    className="box__smalltitle",
                                                                ),
                                                                html.Figure(
                                                                    [
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="windchill_last_value",
                                                                                className="value value--windchill-last"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),

                                                                    ],
                                                                    className="figure figure--windchill-last",
                                                                ),
                                                            ],
                                                            className="value-box value-box--with-title"
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.H3(
                                                                    ["Lufttemp."],
                                                                    className="box__smalltitle",
                                                                ),
                                                                html.Figure(
                                                                    [
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_last_value",
                                                                                className="value value--air-temperature-last"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                    className="figure figure--air-temperature-last",
                                                                ),
                                                            ],
                                                            className="value-box value-box--with-title",
                                                        ),
                                                    ],
                                                    className="last-values__grid"
                                                ),
                                                html.Div(
                                                    [
                                                        html.P(
                                                            id="last-values__text",
                                                            className="paragraph"
                                                        ),
                                                    ],
                                                    className="last-values__text"
                                                ),
                                            ],
                                            className="last-values",
                                        ),
                                        html.Div(
                                            [
                                                html.H2(
                                                    ["Prognose für die Lufttemperatur"],
                                                    className="box__subtitle",
                                                ),

                                                html.Div(
                                                    [
                                                        html.Div(
                                                            [
                                                                html.H3(
                                                                    ["In zwei Stunden"],
                                                                    className="box__smalltitle",
                                                                ),
                                                                html.Figure(
                                                                    [
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_forecast_2h_value",
                                                                                className="value value--air-temperature-forecast"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                    className="figure",
                                                                ),
                                                            ],
                                                            className="value-box value-box--with-title",
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.H3(
                                                                    ["In fünf Stunden"],
                                                                    className="box__smalltitle",
                                                                ),
                                                                html.Figure(
                                                                    [
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_forecast_5h_value",
                                                                                className="value value--air-temperature-forecast"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                    className="figure",
                                                                ),
                                                            ],
                                                            className="value-box value-box--with-title",
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.H3(
                                                                    ["Min/Max"],
                                                                    className="box__smalltitle",
                                                                ),
                                                                html.Figure(
                                                                    [
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_forecast_minmax_value",
                                                                                className="value value--air-temperature-forecast"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                    className="figure",
                                                                ),
                                                            ],
                                                            className="value-box value-box--with-title",
                                                        ),
                                                    ],
                                                    className="predicted-values__grid",
                                                ),
                                                html.Div(
                                                    [
                                                        html.P(
                                                            [
                                                                """Da sist ein Text, der auch etwas länger sein 
                                                                kann und was er auch soll, damit man das etwas spürt,
                                                                wie sich längerer Text verhält und so."""
                                                            ],
                                                            id="predicted-values__text",
                                                            className="paragraph"
                                                        ),
                                                    ],
                                                    className="predicted-values__text"
                                                ),
                                            ],
                                            className="predicted-values",
                                        ),
                                    ],
                                    className="box__inner box__inner--values",
                                ),
                            ],
                            className="box box--temperature-and-wind",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H1(
                                            ["Windgeschwindigkeit und Windspitzen"],
                                            className="box__title",
                                        ),
                                        html.Div(
                                            [
                                                dcc.Graph(
                                                    id="wind-speed",
                                                    figure=dict(
                                                        layout=dict(
                                                            plot_bgcolor=app_color["graph_bg"],
                                                            paper_bgcolor=app_color["graph_bg"],
                                                        )
                                                    ),
                                                    className="graph graph--wind-speed"
                                                ),
                                                dcc.Graph(
                                                    id="wind-direction",
                                                    figure=dict(
                                                        layout=dict(
                                                            plot_bgcolor=app_color["graph_bg"],
                                                            paper_bgcolor=app_color["graph_bg"],
                                                        )
                                                    ),
                                                    className="graph graph--wind-direction"
                                                ),
                                            ],
                                            className="wind-graphs",
                                        ),
                                    ],
                                    className="box__inner box__inner--title-and-graph box__inner--wind-graphs",
                                ),
                            ],
                            className="box box--temperature-and-wind",
                        ),
                    ],
                    className="section__inner section__inner--temperature-and-wind"
                ),
            ],
            className="section section--general"
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Figure(
                                    [
                                        html.Div([
                                            html.Span(id="barometric_pressure_qfe_last_value", className="value"),
                                            html.Span(["hPa"], className="unit"),
                                        ]),
                                        html.Figcaption(["Luftdruck"], className="figcaption"),
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
                                            html.Span(id="water_temperature_last_value", className="value"),
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
                                            html.Span(id="humidity_last_value", className="value"),
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
                                            html.Span(id="dew_point_last_value", className="value"),
                                            html.Span(["°C"], className="unit"),
                                        ]),
                                        html.Figcaption(["Taupunkt"], className="figcaption"),
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
    ],
    id="main",
    className="main",
)






# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
)





# Get all historic data
dataframeli = get_all_historic_data("mythenquai")





@app.callback(
    [
        Output("air_temperature_forecast_2h_value", "children"),
        Output("air_temperature_forecast_5h_value", "children"),
        Output("air_temperature_forecast_minmax_value", "children"),
    ],
    [Input("update-interval", "n_intervals")],
)
def update_air_temperature_forecast_values_and_texts(interval):

    # get last entry as current air temperature
    df_at = dataframeli["mean_air_temperature"]
    air_temperature_last = df_at.tail(1)
    #air_temperature_last_update_text = "Heute, {}".format((air_temperature_last.index[0]).strftime('%H:%M Uhr'))

    # Forecast air temperature with historic data
    # Forecast the air temperature for 1 hour, 2 hours and 4 hours
    air_temperature_forecast = np.array(["n/a", "n/a", "n/a"])




    return air_temperature_forecast[0],\
           air_temperature_forecast[1],\
           air_temperature_forecast[2]




@app.callback(
    [
        Output("air_temperature_last_value", "children"),
        Output("windchill_last_value", "children"),
        Output("last-values__text", "children"),
        Output("barometric_pressure_qfe_last_value", "children"),
        Output("dew_point_last_value", "children"),
        Output("humidity_last_value", "children"),
        Output("water_temperature_last_value", "children"),
    ],
    [Input("update-interval", "n_intervals")],
)
def update_last_values_and_texts(interval):

    df = get_last_data("mythenquai")

    air_temperature_last_value = float(df["last_air_temperature"].values)
    windchill_last_value = float(df["last_windchill"].values)
    dew_point_last_value = float(df["last_dew_point"].values)
    barometric_pressure_qfe_last_value = float(df["last_barometric_pressure_qfe"].values)
    humidity_last_value = float(df["last_humidity"].values)
    water_temperature_last_value = float(df["last_water_temperature"].values)

    df_last_air_temperature_entry_timestamp = get_last_timestamp_of_entry("mythenquai", "air_temperature")

    # calculate difference between mean of last week and current air temperature
    df_compare = get_mean_value_of_last_week_between_time(
        "air_temperature",
        "7d",
        df_last_air_temperature_entry_timestamp.index.time[0],
        df_last_air_temperature_entry_timestamp.index.time[0]
    )
    mean_air_temperature_of_last_week_between_time = float(df_compare.values)
    abs_difference_of_temperatures = abs(mean_air_temperature_of_last_week_between_time - air_temperature_last_value)

    # …show corresponding message
    last_values_text = "Die aktuelle Lufttemperatur ist "
    if (air_temperature_last_value < mean_air_temperature_of_last_week_between_time):
        last_values_text += """{}° Celsius tiefer als"""
    elif (air_temperature_last_value == mean_air_temperature_of_last_week_between_time):
        last_values_text += """gleich wie """
    else:
        last_values_text += """{}° Celsius höher als """
    last_values_text += "in den letzten 7 Tagen zu dieser Tageszeit."
    last_values_text = last_values_text.format(format(abs_difference_of_temperatures, '.1f'))

    return str(air_temperature_last_value),\
           str(windchill_last_value), \
           last_values_text, \
           str(barometric_pressure_qfe_last_value),\
           str(dew_point_last_value),\
           str(humidity_last_value),\
           str(water_temperature_last_value)



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
    Output("air_temperature", "figure"), [Input("update-interval", "n_intervals")]
)
def gen_air_temperature_and_windchill_graph(interval):
    """
    Generate the air temperature and windchill graph.
    :params interval: update the graph based on an interval
    """

    df_at = get_single_column("air_temperature", "420m")
    df_wc = get_single_column("windchill", "420m")

    trace_air_temperature = dict(
        type="scatter",
        y=df_at["air_temperature"].values,
        x=df_at.index,
        line={"color": "#ffa6bd"},
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

    trace_windchill = dict(
        type="scatter",
        y=df_wc["windchill"].values,
        x=df_wc.index,
        line={"color": "#a49ef2"},
        hoverinfo="skip",
        mode="lines+markers",
    )

    layout = dict(
        plot_bgcolor=app_color["transparent"],
        paper_bgcolor=app_color["transparent"],
        margin=dict(l=0, r=20, b=10, t=20),
        hovermode="closest",
        showlegend=False,
        height=120,
        font=dict(
            family="Dosis, Arial",
            size=12,
            color="#7f7f7f"
        ),
        xaxis={
            "showgrid": False,
            "zeroline": False,
            "tickformat": "%H:%M",
            "side": "top",
            "fixedrange": True,
        },
        yaxis={
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "side": "right",
        },
    )

    return dict(data=[trace_air_temperature, trace_windchill], layout=layout)






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
        plot_bgcolor=app_color["transparent"],
        paper_bgcolor=app_color["transparent"],
        margin=dict(l=0, r=20, b=10, t=20),
        hovermode="closest",
        showlegend=False,
        height=150,
        font=dict(
            family="Dosis, Arial",
            size=12,
            color="#7f7f7f"
        ),

        # xaxis={
        #     "range": [0, 24],
        #     "showline": True,
        #     "zeroline": False,
        #     "fixedrange": True,
        #     "tickvals": [0, 6, 12, 18, 24],
        #     "ticktext": ["4", "3", "2", "1", "0"],
        #     "title": "Verstrichene Zeit in Stunden",
        #     #"nticks": 5,
        #     "gridcolor": app_color["graph_gridline"],
        # },
        # yaxis={
        #     "range": [
        #         0,
        #         max(max_wind_gust_in_serie + 1, max_wind_speed_in_serie + 1),
        #     ],
        #     "showgrid": True,
        #     "showline": True,
        #     "fixedrange": False,
        #     "zeroline": False,
        #     "title": "m/s",
        #     "gridcolor": app_color["graph_gridline"],
        #     #"nticks": max(5, round(df["wind_speed_avg_10min"].iloc[-1] / 6)),
        # },

        xaxis = {
            "showgrid": False,
            "zeroline": False,
            "tickformat": "%H:%M",
            "side": "top",
            "fixedrange": True,
        },
        yaxis = {
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "side": "right",
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
        height=200,
        margin=dict(l=10, r=10, b=10, t=10),
        hovermode="closest",
        legend=dict(font=dict(size=10), orientation="v"),
        showlegend=False,
        plot_bgcolor=app_color["transparent"],
        paper_bgcolor=app_color["transparent"],
        font={"color": "#000"},
        autosize=False,
        polar={
            "bgcolor": app_color["graph_line"],
            "radialaxis": {"range": [0, max_wind_speed_in_serie], "angle": 45, "dtick": 10},
            "angularaxis": {"showline": False, "tickcolor": "white"},
        },
    )

    return dict(data=data, layout=layout)





# Main
if __name__ == "__main__":
    app.run_server(debug=True)
