# Import required libraries
import os
import pickle
import copy
import pathlib
import dash
import datetime as dt
import pandas as pd
import numpy as np
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
from get_data import *
from helpers import *




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
stations_options = [
    {"value": str(STATIONS[station]), "label": str(station)} for station in STATIONS
]

app_color = {
    "graph_bg": "#ffffff",
    "graph_gridline": "#EDEDED",
    "graph_line": "#007ACE",
    "transparent": "rgba(255, 255, 255, 0)",
}

layout = dict(
    autosize=True,
    automargin=False,
    margin=dict(l=40, r=10, b=40, t=40),
    hovermode="closest",
    plot_bgcolor=app_color["graph_bg"],
    paper_bgcolor=app_color["graph_bg"],
    legend=dict(font=dict(size=10), orientation="h"),
)

# Create app layout
app.layout = html.Div(
    id="wrapper",
    className="wrapper",
    children=[
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        dcc.Interval(
            id="update-interval",
            interval=int(GRAPH_INTERVAL),
            n_intervals=0,
        ),
        # Header
        html.Div(
            id="header",
            className="header",
            children=[
                html.H1(
                    className="header__title",
                    id="header__title",
                ),
                # Controller
                html.Div(
                    className="station-switcher",
                    children=[
                        dcc.RadioItems(
                            className="station-switcher__options",
                            id="station-switcher__options",
                            options=stations_options,
                            value="mythenquai",
                        ),
                    ],
                ),
            ],
        ),
        # Main
        html.Div(
            className="main",
            children=[
                # Box: Windkühle & Lufttemp.
                html.Div(
                    className="box air-temperature-and-windchill",
                    children=[
                        html.Div(
                            className="box__header",
                            children=[
                                html.H1(
                                    className="box__title",
                                    children=["Windkühle & Lufttemperatur"],
                                ),
                            ],
                        ),
                        html.Div(
                            className="box__inner air-temperature-and-windchill__inner",
                            children=[
                                html.Div(
                                    className="air-temperature-and-windchill__graph-wrapper",
                                    children=[
                                        dcc.Graph(
                                            id="air_temperature_and_windchill",
                                            className="air-temperature-and-windchill__graph graph",
                                            figure=dict(
                                                layout=dict(
                                                    plot_bgcolor=app_color["graph_bg"],
                                                    paper_bgcolor=app_color["graph_bg"],
                                                )
                                            ),
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="air-temperature-and-windchill__values",
                                    children=[
                                        html.Div(
                                            className="air-temperature-and-windchill__last-values",
                                            children=[
                                                html.H2(
                                                    className="box__subtitle",
                                                    children=["Aktuelle Werte"],
                                                ),
                                                html.Div(
                                                    className="air-temperature-and-windchill__last-values-grid",
                                                    children=[
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Windkühle"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure figure--windchill-last",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="windchill_last_value",
                                                                                className="value value--windchill-last"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),

                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Lufttemp."],
                                                                ),
                                                                html.Figure(
                                                                    className="figure figure--air-temperature-last",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_last_value",
                                                                                className="value value--air-temperature-last"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                                html.Div(
                                                    className="last-values__text",
                                                    children=[
                                                        html.P(
                                                            id="last-values__text",
                                                            className="paragraph"
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="air-temperature-and-windchill__predicted-values",
                                            children=[
                                                html.H2(
                                                    className="box__subtitle",
                                                    children=["Prognose für die Lufttemperatur"],
                                                ),
                                                html.Div(
                                                    className="air-temperature-and-windchill__predicted-values-grid",
                                                    children=[
                                                        html.Div(
                                                            className="value-box value-box--with-title",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["In zwei Stunden"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_forecast_2h_value",
                                                                                className="value value--air-temperature-forecast"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["In fünf Stunden"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_forecast_5h_value",
                                                                                className="value value--air-temperature-forecast"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Min/Max"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_forecast_minmax_value",
                                                                                className="value value--air-temperature-forecast"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                                html.Div(
                                                    className="predicted-values__text",
                                                    children=[
                                                        html.P(
                                                            id="predicted-values__text",
                                                            className="paragraph",
                                                            children=[
                                                                """Da sist ein Text, der auch etwas länger sein 
                                                                kann und was er auch soll, damit man das etwas spürt,
                                                                wie sich längerer Text verhält und so."""
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="air-temperature-and-windchill__historical-values",
                                            children=[
                                                html.H2(
                                                    className="box__subtitle",
                                                    children=["Historische Werte"],
                                                ),
                                                html.Div(
                                                    className="air-temperature-and-windchill__historical-values-grid",
                                                    children=[
                                                        dcc.Graph(
                                                            className="graph graph--bled-off graph--historical-air-temperature",
                                                            id="historical-air-temperature",
                                                        ),
                                                    ],
                                                ),
                                                html.Div(
                                                    className="historical-values__text",
                                                    children=[
                                                        html.P(
                                                            id="historical-values__text",
                                                            className="paragraph",
                                                            children=["Das ist der Text, der die historischen Werte umschreibt"]
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),

                # Box: Windgeschwindigkeit etc.
                html.Div(
                    className="box wind-speed-gust-and-force",
                    children=[
                        html.H1(
                            children=["Windgeschwindigkeit, -spitzen,-richtung & -stärke"],
                            className="box__title",
                        ),
                        html.Div(
                            className="box__inner wind-speed-gust-and-force__inner",
                            children=[
                                html.Div(
                                    className="wind-speed-gust-and-force__graph-wrapper",
                                    children=[
                                        html.Div(
                                            className="wind-speed-gust-and-force__graph-wrapper-grid",
                                            children=[
                                                dcc.Graph(
                                                    className="air-temperature-and-windchill__graph graph",
                                                    id="wind-speed",
                                                    figure=dict(
                                                        layout=dict(
                                                            plot_bgcolor=app_color["graph_bg"],
                                                            paper_bgcolor=app_color["graph_bg"],
                                                        )
                                                    ),
                                                ),
                                                dcc.Graph(
                                                    className="air-temperature-and-windchill__graph graph",
                                                    id="wind-direction",
                                                    figure=dict(
                                                        layout=dict(
                                                            plot_bgcolor=app_color["graph_bg"],
                                                            paper_bgcolor=app_color["graph_bg"],
                                                        )
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="wind-speed-gust-and-force__values",
                                    children=[
                                        html.Div(
                                            className="wind-speed-gust-and-force__last-values",
                                            children=[
                                                html.H2(
                                                    className="box__subtitle",
                                                    children=["Aktuelle Werte"],
                                                ),
                                                html.Div(
                                                    className="wind-speed-gust-and-force__last-values-grid",
                                                    children=[
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Windgeschw."],
                                                                ),
                                                                html.Figure(
                                                                    className="figure figure--wind-speed-last",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="wind_speed_last_value",
                                                                                className="value value--wind-speed-last"),
                                                                            html.Span(["m/s"], className="unit"),
                                                                        ]),

                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Windspitzen"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure figure--wind-gust-last",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="wind_gust_last_value",
                                                                                className="value value--wind-gust-last"),
                                                                            html.Span(["m/s"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Windstärke"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure figure--wind-force-last",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="wind_force_last_value",
                                                                                className="value value--wind-force-last"),
                                                                            html.Span(["Bft"], className="unit"),
                                                                        ]),

                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                                html.Div(
                                                    className="last-values__text",
                                                    children=[
                                                        html.P(
                                                            id="wind-speed-gust-and-force-last-values__text",
                                                            className="paragraph"
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="wind-speed-gust-and-force__predicted-values",
                                            children=[
                                                html.H2(
                                                    className="box__subtitle",
                                                    children=["Warnungen"],
                                                ),
                                                html.Div(
                                                    className="predicted-values-grid",
                                                    children=[
                                                        # html.Div(
                                                        #     className="value-box value-box--with-title",
                                                        #     children=[
                                                        #         html.H3(
                                                        #             className="box__smalltitle",
                                                        #             children=["In zwei Stunden"],
                                                        #         ),
                                                        #         html.Figure(
                                                        #             className="figure",
                                                        #             children=[
                                                        #                 html.Div([
                                                        #                     html.Span(
                                                        #                         id="wind-speed-gust-and-force_forecast_2h_value",
                                                        #                         className="value value--wind-speed-gust-and-force-forecast"),
                                                        #                     html.Span(["°C"], className="unit"),
                                                        #                 ]),
                                                        #             ],
                                                        #         ),
                                                        #     ],
                                                        # ),
                                                        # html.Div(
                                                        #     className="value-box",
                                                        #     children=[
                                                        #         html.H3(
                                                        #             className="box__smalltitle",
                                                        #             children=["In fünf Stunden"],
                                                        #         ),
                                                        #         html.Figure(
                                                        #             className="figure",
                                                        #             children=[
                                                        #                 html.Div([
                                                        #                     html.Span(
                                                        #                         id="wind-speed-gust-and-force_forecast_5h_value",
                                                        #                         className="value value--wind-speed-gust-and-force-forecast"),
                                                        #                     html.Span(["°C"], className="unit"),
                                                        #                 ]),
                                                        #             ],
                                                        #         ),
                                                        #     ],
                                                        # ),
                                                    ],
                                                ),
                                                html.Div(
                                                    className="predicted-values__text",
                                                    children=[
                                                        html.P(
                                                            id="wind-speed-gust-and-force__predicted-values__text",
                                                            className="paragraph",
                                                            children=[
                                                                """Da sist ein Text, der auch etwas länger sein 
                                                                kann und was er auch soll, damit man das etwas spürt,
                                                                wie sich längerer Text verhält."""
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),

                # Box: Regen
                html.Div(
                    className="box precipitation",
                    children=[
                        html.H1(
                            children=["Regen"],
                            className="box__title",
                        ),
                        html.Div(
                            className="box__inner precipitation__inner",
                            children=[
                                html.Div(
                                    className="precipitation__graph-wrapper",
                                    children=[
                                        dcc.Graph(
                                            className="precipitation__graph graph",
                                            id="precipitation__graph",
                                        ),
                                    ],
                                ),
                                # html.Div(
                                #     className="wind-speed-gust-and-force__values",
                                #     children=[
                                #         html.Div(
                                #             className="wind-speed-gust-and-force__last-values",
                                #             children=[
                                #                 html.H2(
                                #                     className="box__subtitle",
                                #                     children=["Aktuelle Werte"],
                                #                 ),
                                #                 html.Div(
                                #                     className="wind-speed-gust-and-force__last-values-grid",
                                #                     children=[
                                #                         html.Div(
                                #                             className="value-box",
                                #                             children=[
                                #                                 html.H3(
                                #                                     className="box__smalltitle",
                                #                                     children=["Windgeschw."],
                                #                                 ),
                                #                                 html.Figure(
                                #                                     className="figure figure--wind-speed-last",
                                #                                     children=[
                                #                                         html.Div([
                                #                                             html.Span(
                                #                                                 id="wind_speed_last_value",
                                #                                                 className="value value--wind-speed-last"),
                                #                                             html.Span(["m/s"], className="unit"),
                                #                                         ]),
                                #
                                #                                     ],
                                #                                 ),
                                #                             ],
                                #                         ),
                                #                         html.Div(
                                #                             className="value-box",
                                #                             children=[
                                #                                 html.H3(
                                #                                     className="box__smalltitle",
                                #                                     children=["Windspitzen"],
                                #                                 ),
                                #                                 html.Figure(
                                #                                     className="figure figure--wind-gust-last",
                                #                                     children=[
                                #                                         html.Div([
                                #                                             html.Span(
                                #                                                 id="wind_gust_last_value",
                                #                                                 className="value value--wind-gust-last"),
                                #                                             html.Span(["m/s"], className="unit"),
                                #                                         ]),
                                #                                     ],
                                #                                 ),
                                #                             ],
                                #                         ),
                                #                         html.Div(
                                #                             className="value-box",
                                #                             children=[
                                #                                 html.H3(
                                #                                     className="box__smalltitle",
                                #                                     children=["Windstärke"],
                                #                                 ),
                                #                                 html.Figure(
                                #                                     className="figure figure--wind-force-last",
                                #                                     children=[
                                #                                         html.Div([
                                #                                             html.Span(
                                #                                                 id="wind_force_last_value",
                                #                                                 className="value value--wind-force-last"),
                                #                                             html.Span(["Bft"], className="unit"),
                                #                                         ]),
                                #
                                #                                     ],
                                #                                 ),
                                #                             ],
                                #                         ),
                                #                     ],
                                #                 ),
                                #                 html.Div(
                                #                     className="last-values__text",
                                #                     children=[
                                #                         html.P(
                                #                             id="wind-speed-gust-and-force-last-values__text",
                                #                             className="paragraph"
                                #                         ),
                                #                     ],
                                #                 ),
                                #             ],
                                #         ),
                                #         html.Div(
                                #             className="wind-speed-gust-and-force__predicted-values",
                                #             children=[
                                #                 html.H2(
                                #                     className="box__subtitle",
                                #                     children=["Warnungen"],
                                #                 ),
                                #                 html.Div(
                                #                     className="predicted-values-grid",
                                #                     children=[
                                #                     ],
                                #                 ),
                                #                 html.Div(
                                #                     className="predicted-values__text",
                                #                     children=[
                                #                         html.P(
                                #                             id="wind-speed-gust-and-force__predicted-values__text",
                                #                             className="paragraph",
                                #                             children=[
                                #                                 """Da sist ein Text, der auch etwas länger sein
                                #                                 kann und was er auch soll, damit man das etwas spürt,
                                #                                 wie sich längerer Text verhält."""
                                #                             ],
                                #                         ),
                                #                     ],
                                #                 ),
                                #             ],
                                #         ),
                                #     ],
                                # ),
                            ],
                        ),
                    ],
                ),
                # Box: Global radiation
                html.Div(
                    className="box global-radiation",
                    children=[
                        html.H1(
                            children=["Globalstrahlung"],
                            className="box__title",
                        ),
                        html.Div(
                            className="box__inner global-radiation__inner",
                            children=[
                                html.Div(
                                    className="global-radiation__graph-wrapper",
                                    children=[
                                        dcc.Graph(
                                            className="global-radiation__graph graph",
                                            id="global-radiation__graph",
                                            figure=dict(
                                                layout=dict(
                                                    plot_bgcolor=app_color["graph_bg"],
                                                    paper_bgcolor=app_color["graph_bg"],
                                                )
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),



                # Box: Weiteres
                html.Div(
                    className="box more",
                    children=[
                        html.Div(
                            className="box__header",
                            children=[
                                html.H1(
                                    className="box__title",
                                    children=["Weitere Messdaten"],
                                ),
                            ],
                        ),
                        html.Div(
                            className="box__inner more__inner",
                            children=[
                                html.Div(
                                    className="more__values",
                                    children=[
                                        html.Div(
                                            className="more__last-values",
                                            children=[
                                                html.H2(
                                                    className="box__subtitle",
                                                    children=["Aktuelle Werte"],
                                                ),
                                                html.Div(
                                                    className="more__last-values-grid",
                                                    children=[
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Luftdruck QFE"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure figure--barometric-pressure-qfe",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="barometric_pressure_qfe_last_value",
                                                                                className="value value--barometric-pressure-qfe-last"),
                                                                            html.Span(["hPa"], className="unit"),
                                                                        ]),

                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Luftfeuchte"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure figure--humidity-last",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="humidity_last_value",
                                                                                className="value value--humidity-last"),
                                                                            html.Span(["%"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Pegel"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure figure--water-level-last",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="water_level_last_value",
                                                                                className="value value--water-level-last"),
                                                                            html.Span(["m"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Taupunkt"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure figure--dew-point-last",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="dew_point_last_value",
                                                                                className="value value--dew-point-last"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Wassertemp."],
                                                                ),
                                                                html.Figure(
                                                                    className="figure figure--water-temperature-last",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="water_temperature_last_value",
                                                                                className="value value--water-temperature-last"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)






# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
)





# Get all historic data
#dataframeli = get_all_historic_data("mythenquai")


@app.callback(
    Output("header__title", "children"), [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def update_intro_text(interval, station_name):

    return "«Hallo stürmischer Tag!», meint die Station {}".format(station_name)


@app.callback(
    [
        Output("air_temperature_forecast_2h_value", "children"),
        Output("air_temperature_forecast_5h_value", "children"),
        Output("air_temperature_forecast_minmax_value", "children"),
    ], [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def update_air_temperature_forecast_values_and_texts(interval, station_name):

    # get last entry as current air temperature
    #df_at = dataframeli["mean_air_temperature"]
    #air_temperature_last = df_at.tail(1)
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
    ], [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def update_last_windchill_and_air_temperature_values_and_texts(interval, station_name):

    df = get_last_data(station_name)

    air_temperature_last_value = float(df["last_air_temperature"].values)
    windchill_last_value = float(df["last_windchill"].values)
    dew_point_last_value = float(df["last_dew_point"].values)
    barometric_pressure_qfe_last_value = int(round_up(float(df["last_barometric_pressure_qfe"].values), 0))
    humidity_last_value = float(df["last_humidity"].values)
    water_temperature_last_value = float(df["last_water_temperature"].values)

    df_last_air_temperature_entry_timestamp = get_last_timestamp_of_entry(station_name, "air_temperature")

    # calculate difference between mean of last week and current air temperature
    df_compare = get_mean_value_of_last_week_between_time(
        station_name,
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
        last_values_text += """{}° Celsius tiefer als """
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


@app.callback(
    [
        Output("wind_speed_last_value", "children"),
        Output("wind_gust_last_value", "children"),
        Output("wind_force_last_value", "children"),
    ], [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def update_last_wind_values_and_texts(interval, station_name):

    df = get_last_data(station_name)

    wind_speed_last_value = float(df["last_wind_speed_avg_10min"].values)
    wind_gust_last_value = float(df["last_wind_gust_max_10min"].values)
    wind_force_last_value = float(df["last_wind_force_avg_10min"].values)

    return str(wind_speed_last_value),\
           str(wind_gust_last_value), \
           str(wind_force_last_value)



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
    Output("air_temperature_and_windchill", "figure"),
    [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def gen_air_temperature_and_windchill_graph(interval, station_name):
    """
    Generate the air temperature and windchill graph.
    :params interval: update the graph based on an interval
    """

    df_at = get_single_column(station_name, "air_temperature", "420m")
    df_wc = get_single_column(station_name, "windchill", "420m")

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
        margin=dict(l=0, r=20, b=10, t=30),
        hoverinfo='x+y',
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
            "fixedrange": False, # True
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
    Output("historical-air-temperature", "figure"),
    [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def gen_historical_air_temperature_graph(interval, station_name):
    """
    Generate the historical air temperature graph.
    :params interval: update the graph based on an interval
    """

    # Generate 3 weeks (2 in past, 1 into future) frame
    # create 3 weeks span (go two weeks back and 1 into the future)
    x = [dt.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(days=-14)]
    for d in range(21):
        x.append(x[0] + dt.timedelta(days=d))
    x = sorted(x)

    past_dayofyear = x[0].timetuple().tm_yday
    future_dayofyear = x[-1].timetuple().tm_yday

    df_h = get_daily_value_of_past(station_name, "air_temperature")
    # Calculate daily mean air temperature grouped by month and day
    gb_h = df_h.groupby([df_h.index.month, df_h.index.day]).mean().reset_index()
    # only grab needed date frame
    df_h = gb_h.loc[(gb_h.index > past_dayofyear) | (gb_h.index < future_dayofyear)]
    #df_h = df_h.rolling(window=2, min_periods=1, axis=0).mean()

    df = get_daily_value_of_last_two_weeks(station_name, "air_temperature")

    trace_historical_air_temperature = dict(
        type="scatter",
        y=df_h["mean"].values,
        x=x,
        line=dict(
            color="#000",
            width=1,
            smoothing=2,
        ),
        hoverinfo="skip",
        mode="lines",
        name="Historische Lufttemp.",
        line_shape='linear',
    )

    trace_air_temperature = dict(
        type="scatter",
        y=df["mean"].values,
        x=df.index,
        hoverinfo="skip",
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(255, 119, 161, 0.2)",
        name="Aktuelle Lufttemp.",
        line={"width": 0}
    )

    layout = dict(
        plot_bgcolor=app_color["transparent"],
        paper_bgcolor=app_color["transparent"],
        margin=dict(l=0, r=20, b=40, t=20),
        hoverinfo='x+y',
        showlegend=True,
        legend=dict(
            yanchor='bottom',
            xanchor='center',
            y=-0.5,
            x=0.5,
            orientation="h",
        ),
        height=120,
        font=dict(
            family="Dosis, Arial",
            size=12,
            color="#7f7f7f"
        ),
        # xaxis={
        #     "showgrid": False,
        #     "zeroline": False,
        #     "tickformat": "%b %d",
        #     "side": "top",
        #     "fixedrange": False,
        # },
        xaxis={
            "type": "date",
            "showgrid": False,
            "side": "top",
            "zeroline": False,
            "tickformat": "%e. %b",
            'tick0': x[0],
            "dtick": 86400000.0 * 7,
        },
        yaxis={
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "side": "right",
        },
    )

    return dict(data=[trace_historical_air_temperature, trace_air_temperature], layout=layout)


@app.callback(
    Output("wind-speed", "figure"),
    [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def gen_wind_speed(interval, station_name):
    """
    Generate the wind speed graph.
    :params interval: update the graph based on an interval
    """

    df = get_wind_data(station_name, "4h")
    max_wind_speed_in_serie = df["wind_speed_avg_10min"].max()
    max_wind_gust_in_serie = df["wind_gust_max_10min"].max()

    trace_speed = dict(
        type="scatter",
        y=df["wind_speed_avg_10min"],
        line=dict(
            color="#069dce",
            width=2,
            smoothing=2,
        ),
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
        line={"color": "#0275a0"},
        hoverinfo="skip",
        # error_y={
        #     "type": "data",
        #     "array": df["wind_gust_max_10min"],
        #     "thickness": 1.5,
        #     "width": 2,
        #     "color": "#B4E8FC",
        # },
        mode="markers",
        opacity=0.5,
    )

    layout = dict(
        plot_bgcolor=app_color["transparent"],
        paper_bgcolor=app_color["transparent"],
        margin=dict(l=0, r=20, b=10, t=30),
        hovermode="closest",
        showlegend=False,
        height=120,
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

    df = get_wind_data("mythenquai", "4h")
    max_wind_speed_in_serie = df["wind_speed_avg_10min"].max()

    val = df["wind_speed_avg_10min"].iloc[-1]
    direction = [0, (df["wind_direction"][0] - 20), (df["wind_direction"][0] + 20), 0]



    traces_scatterpolar = [
        {"r": [0, val, val, 0], "fillcolor": "#084E8A"},
        {"r": [0, val * 0.65, val * 0.65, 0], "fillcolor": "blue"},
        {"r": [0, val * 0.3, val * 0.3, 0], "fillcolor": "yellow"},
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
        height=120,
        margin=dict(l=10, r=10, b=30, t=30),
        hovermode="closest",
        legend=dict(font=dict(size=10), orientation="v"),
        showlegend=False,
        plot_bgcolor=app_color["transparent"],
        paper_bgcolor=app_color["transparent"],
        font=dict(
            family="Dosis, Arial",
            size=12,
            color="#7f7f7f"
        ),
        autosize=False,
        polar={
            "bgcolor": app_color["transparent"],
            "radialaxis": {"range": [0, max_wind_speed_in_serie], "angle": 45, "dtick": 10},
            "angularaxis": {"showline": False, "tickcolor": app_color["transparent"]},
        },
    )

    return dict(data=data, layout=layout)


@app.callback(
    Output("precipitation__graph", "figure"),
    [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def gen_historical_precipitation_graph(interval, station_name):
    """
    Generate the historical air temperature graph.
    :params interval: update the graph based on an interval
    """

    # Generate 3 weeks (2 in past, 1 into future) frame
    # create 3 weeks span (go two weeks back and 1 into the future)
    x = [dt.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(days=-14)]
    for d in range(21):
        x.append(x[0] + dt.timedelta(days=d))
    x = sorted(x)

    past_dayofyear = x[0].timetuple().tm_yday
    future_dayofyear = x[-1].timetuple().tm_yday

    try:

        df_h = get_daily_value_of_past(station_name, "precipitation")
        # Calculate daily mean air temperature grouped by month and day
        gb_h = df_h.groupby([df_h.index.month, df_h.index.day]).mean().reset_index()
        # only grab needed date frame
        df_h = gb_h.loc[(gb_h.index > past_dayofyear) | (gb_h.index < future_dayofyear)]
        #df_h = df_h.rolling(window=2, min_periods=1, axis=0).mean()

        df = get_daily_value_of_last_two_weeks(station_name, "precipitation")

        trace_historical_air_temperature = dict(
            type="scatter",
            y=df_h["mean"].values,
            x=x,
            line=dict(
                color="#000",
                width=1,
                smoothing=2,
            ),
            hoverinfo="skip",
            mode="lines",
            name="Historische Regenmenge",
            line_shape='linear',
        )

        trace_air_temperature = dict(
            type="scatter",
            y=df["mean"].values,
            x=df.index,
            hoverinfo="skip",
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(255, 119, 161, 0.2)",
            name="Aktuelle Regenmenge",
            line={"width": 0}
        )

        layout = dict(
            plot_bgcolor=app_color["transparent"],
            paper_bgcolor=app_color["transparent"],
            margin=dict(l=0, r=20, b=40, t=0),
            hoverinfo='x+y',
            showlegend=True,
            legend=dict(
                yanchor='top',
                xanchor='center',
                y=1.5,
                x=0.5,
                orientation="h",
            ),
            height=120,
            font=dict(
                family="Dosis, Arial",
                size=12,
                color="#7f7f7f"
            ),
            # xaxis={
            #     "showgrid": False,
            #     "zeroline": False,
            #     "tickformat": "%b %d",
            #     "side": "top",
            #     "fixedrange": False,
            # },
            xaxis={
                "type": "date",
                "showgrid": False,
                "zeroline": False,
                "tickformat": "%e. %b",
                'tick0': x[0],
                "dtick": 86400000.0 * 7,

            },
            yaxis={
                "showgrid": False,
                "showline": False,
                "zeroline": False,
                "side": "right",
            },
        )

        return dict(data=[trace_historical_air_temperature, trace_air_temperature], layout=layout)

    except KeyError:



        layout = dict(
            plot_bgcolor=app_color["transparent"],
            paper_bgcolor=app_color["transparent"],
            annotation=
            {
                "text": "No matching data found",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {
                    "size": 28
                }
            }
        )

        return dict(layout=layout)


@app.callback(
    Output("global-radiation__graph", "figure"),
    [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def gen_historical_global_radiation_graph(interval, station_name):
    """
    Generate the historical air temperature graph.
    :params interval: update the graph based on an interval
    """

    # Generate 3 weeks (2 in past, 1 into future) frame
    # create 3 weeks span (go two weeks back and 1 into the future)
    x = [dt.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(days=-14)]
    for d in range(21):
        x.append(x[0] + dt.timedelta(days=d))
    x = sorted(x)

    past_dayofyear = x[0].timetuple().tm_yday
    future_dayofyear = x[-1].timetuple().tm_yday

    try:
        df_h = get_daily_value_of_past(station_name, "global_radiation")

        # Calculate daily mean air temperature grouped by month and day
        gb_h = df_h.groupby([df_h.index.month, df_h.index.day]).mean().reset_index()
        # only grab needed date frame
        df_h = gb_h.loc[(gb_h.index > past_dayofyear) | (gb_h.index < future_dayofyear)]
        #df_h = df_h.rolling(window=2, min_periods=1, axis=0).mean()

        df = get_daily_value_of_last_two_weeks(station_name, "global_radiation")

        trace_historical_air_temperature = dict(
            type="scatter",
            y=df_h["mean"].values,
            x=x,
            line=dict(
                color="#000",
                width=1,
                smoothing=2,
            ),
            hoverinfo="skip",
            mode="lines",
            name="Historische Regenmenge",
            line_shape='linear',
        )

        trace_air_temperature = dict(
            type="scatter",
            y=df["mean"].values,
            x=df.index,
            hoverinfo="skip",
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(255, 119, 161, 0.2)",
            name="Aktuelle Regenmenge",
            line={"width": 0}
        )

        layout = dict(
            plot_bgcolor=app_color["transparent"],
            paper_bgcolor=app_color["transparent"],
            margin=dict(l=0, r=20, b=40, t=0),
            hoverinfo='x+y',
            showlegend=True,
            legend=dict(
                yanchor='top',
                xanchor='center',
                y=1.5,
                x=0.5,
                orientation="h",
            ),
            height=120,
            font=dict(
                family="Dosis, Arial",
                size=12,
                color="#7f7f7f"
            ),
            # xaxis={
            #     "showgrid": False,
            #     "zeroline": False,
            #     "tickformat": "%b %d",
            #     "side": "top",
            #     "fixedrange": False,
            # },
            xaxis={
                "type": "date",
                "showgrid": False,
                "zeroline": False,
                "tickformat": "%e. %b",
                'tick0': x[0],
                "dtick": 86400000.0 * 7,

            },
            yaxis={
                "showgrid": False,
                "showline": False,
                "zeroline": False,
                "side": "right",
            },
        )

        return dict(data=[trace_historical_air_temperature, trace_air_temperature], layout=layout)

    except KeyError:

        layout = dict(
            plot_bgcolor=app_color["transparent"],
            paper_bgcolor=app_color["transparent"],
        )

        return dict(data=[], layout=layout)




# Main
if __name__ == "__main__":
    app.run_server(debug=True)
