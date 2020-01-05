#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import required libraries
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
from config import *


# Dash app settings and layout
external_stylesheets = ["https://fonts.googleapis.com/css?family=Dosis:400,700&display=swap"]

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    external_stylesheets=external_stylesheets,
)
app.title = WEBAPP_TITLE
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
    {"label": str(STATIONS[station]), "value": str(station)} for station in STATIONS
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
                    children=[
                        html.Span("«Hallo Segler*in» "),
                        html.Span(
                            className="header__subtitle",
                            id="header__subtitle",
                        ),
                    ]
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
                                                    children=["Aktuelle Temperaturwerte"],
                                                ),
                                                html.Div(
                                                    className="air-temperature-and-windchill__last-values-grid",
                                                    children=[
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Kühle"],
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
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.P(
                                                                    className="air-temperature-and-windchill__historical-values-text",
                                                                    id="air-temperature-and-windchill__historical-text",
                                                                ),
                                                            ],
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
                                                                    children=["In 2 Stunden"],
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
                                                                    children=["In 4 Stunden"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_forecast_4h_value",
                                                                                className="value value--air-temperature-forecast"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                        # html.Div(
                                                                        #     className="figure__additional",
                                                                        #     children=[
                                                                        #         html.Span(["±"], className="additional"),
                                                                        #         html.Span(
                                                                        #             id="air_temperature_forecast_4h_additional_value",
                                                                        #             className="value-additional"),
                                                                        #     ]
                                                                        # ),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["In 8 Stunden"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_forecast_8h_value",
                                                                                className="value value--air-temperature-forecast"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box value-box--with-title",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Morgen mittag"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_forecast_1d_value",
                                                                                className="value value--air-temperature-forecast"),
                                                                            html.Span(["°C"], className="unit"),
                                                                        ]),
                                                                        # html.Div(
                                                                        #     className="figure__additional",
                                                                        #     children=[
                                                                        #         html.Span(["Min./Max."],
                                                                        #                   className="additional"),
                                                                        #         html.Span(
                                                                        #             id="air_temperature_forecast_1d_minmax_value",
                                                                        #             className="value-additional"),
                                                                        #     ]
                                                                        # ),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            className="value-box value-box--with-title",
                                                            children=[
                                                                html.H3(
                                                                    className="box__smalltitle",
                                                                    children=["Übermorgen mittag"],
                                                                ),
                                                                html.Figure(
                                                                    className="figure",
                                                                    children=[
                                                                        html.Div([
                                                                            html.Span(
                                                                                id="air_temperature_forecast_2d_value",
                                                                                className="value value--air-temperature-forecast"),
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
                                        html.Div(
                                            className="air-temperature-and-windchill__historical-values",
                                            children=[
                                                html.H2(
                                                    className="box__subtitle",
                                                    children=["Historische Lufttemp. im Vergleich"],
                                                ),
                                                html.Div(
                                                    className="air-temperature-and-windchill__historical-values-grid",
                                                    children=[
                                                        dcc.Graph(
                                                            className="graph graph--bled-off-right graph--historical-air-temperature",
                                                            id="historical-air-temperature",
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
                            children=["Winddaten & Luftdruck"],
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
                                                    children=["Aktuelle Windwerte"],
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
                                                    className="predicted-values__text",
                                                    children=[
                                                        html.P(
                                                            id="wind-speed-gust-and-force__warnings__text",
                                                            className="paragraph",
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="barometric-pressure__historical-values",
                                            children=[
                                                html.H2(
                                                    className="box__subtitle",
                                                    children=["Luftdruck der letzten Tage"],
                                                ),
                                                html.Div(
                                                    className="barometric-pressure__historical-values-grid",
                                                    children=[
                                                        dcc.Graph(
                                                            className="graph graph--bled-off-right graph--historical-barometric-pressure",
                                                            id="historical-barometric-pressure",
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="barometric-pressure__predicted-values",
                                            children=[
                                                html.H2(
                                                    className="box__subtitle",
                                                    children=["Windentwicklung"],
                                                ),
                                                html.Div(
                                                    className="predicted-wind-values__text",
                                                    children=[
                                                        html.P(
                                                            id="wind-speed-gust-and-force__predicted__text",
                                                            className="paragraph",
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

                # Box: Niederschlag
                html.Div(
                    className="box precipitation",
                    children=[
                        html.H1(
                            children=["Niederschlag"],
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
                                html.Div(
                                    className="precipitation__values",
                                    children=[
                                        html.Div(
                                            className="precipitation__last-values",
                                            children=[
                                                # html.H2(
                                                #     className="box__subtitle",
                                                #     children=["Aktuelle Werte"],
                                                # ),
                                                html.Div(
                                                    className="last-values__text",
                                                    children=[
                                                        html.P(
                                                            id="precipitation__text",
                                                            className="paragraph",
                                                            children=[
                                                                "Das ist ein kurzer Text zum Regen."
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
                                html.Div(
                                    className="global-radiation__values",
                                    children=[
                                        html.Div(
                                            className="global-radiation__last-values",
                                            children=[
                                                # html.H2(
                                                #     className="box__subtitle",
                                                #     children=["Aktuelle Werte"],
                                                # ),
                                                html.Div(
                                                    className="last-values__text",
                                                    children=[
                                                        html.P(
                                                            id="global-radiation__text",
                                                            className="paragraph",
                                                            children=[
                                                                "Das ist ein kurzer Text zur Sonnenstrahlung."
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
                            className="box__inner box__inner--simple more__inner",
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
