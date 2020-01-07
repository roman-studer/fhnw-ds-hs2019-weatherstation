#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import required libraries
import pickle
import copy
import dash
import datetime as dt
import pandas as pd
import numpy as np
from get_data import *
from helpers import *
from config import *
from app_layout import *




@app.callback(
    Output("header__subtitle", "children"), [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def update_intro_text(interval, station_name):

    says_who = ""
    if station_name in STATIONS:
        says_who = "sagt die Station {}".format(STATIONS[station_name])
    else:
        says_who = "sagt niemand"

    return says_who


@app.callback(
    [
        Output("air_temperature_forecast_2h_value", "children"),
        Output("air_temperature_forecast_4h_value", "children"),
        Output("air_temperature_forecast_8h_value", "children"),
        Output("air_temperature_forecast_1d_value", "children"),
        Output("air_temperature_forecast_2d_value", "children"),
    ], [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def update_air_temperature_forecast_values_and_texts(interval, station_name):

    values = get_air_temperature_forecast_values(station_name)

    return values[0], values[1], values[2], values[3], values[4]


@app.callback(
    [
        Output("air_temperature_last_value", "children"),
        Output("windchill_last_value", "children"),
        Output("air-temperature-and-windchill__historical-text", "children"),
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
    humidity_last_value = float(df["last_humidity"].values)
    water_temperature_last_value = float(df["last_water_temperature"].values)

    df_last_air_temperature_entry_timestamp = get_timestamp_of_last_entry(station_name, "air_temperature")

    # calculate difference between mean of last week and current air temperature
    df_compare = get_mean_value_of_last_week_between_time(
        station_name,
        "air_temperature",
        "7d",
        df_last_air_temperature_entry_timestamp.time[0],
        df_last_air_temperature_entry_timestamp.time[0]
    )
    mean_air_temperature_of_last_week_between_time = float(df_compare.values)
    abs_difference_of_temperatures = abs(mean_air_temperature_of_last_week_between_time - air_temperature_last_value)

    # …show corresponding message
    last_values_text = "Die Lufttemp. ist "
    if (air_temperature_last_value < mean_air_temperature_of_last_week_between_time):
        last_values_text += """{}°C tiefer als """
    elif (air_temperature_last_value == mean_air_temperature_of_last_week_between_time):
        last_values_text += """gleich wie """
    else:
        last_values_text += """{}°C höher als """
    last_values_text += "in den letzten 7 Tagen zu dieser Zeit."
    last_values_text = last_values_text.format(format(abs_difference_of_temperatures, '.1f'))

    return str(air_temperature_last_value),\
           str(windchill_last_value), \
           last_values_text, \
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


@app.callback(

    Output("wind-speed-gust-and-force__warnings__text", "children"), [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def update_wind_warnings_texts(interval, station_name):

    warnings = get_data_for_wind_warnings(station_name)

    return """Die Wahrscheinlichkeit von hohen Windgeschwindigkeiten beträgt {}%, 
     jene von Sturmwinden beträgt {}%.""".format(round_up(warnings[0], 0), round_up(warnings[1], 0))


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
        mode="lines+markers",
        name="Aktuelle Lufttemp.",
    )

    trace_windchill = dict(
        type="scatter",
        y=df_wc["windchill"].values,
        x=df_wc.index,
        line={"color": "#a49ef2"},
        hoverinfo="skip",
        mode="lines+markers",
        name="Windkühle",
    )

    layout = dict(
        plot_bgcolor=app_color["transparent"],
        paper_bgcolor=app_color["transparent"],
        margin=dict(l=0, r=30, b=10, t=25),
        hoverinfo='x+y',
        showlegend=True,
        legend=dict(
            yanchor='bottom',
            xanchor='center',
            y=-0.1,
            x=0.5,
            orientation="h",
        ),
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
            "ticksuffix": "h",
        },
        yaxis={
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "side": "right",
            "ticksuffix": " °C",
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
        margin=dict(l=0, r=30, b=10, t=20),
        hoverinfo='x+y',
        showlegend=True,
        legend=dict(
            yanchor='bottom',
            xanchor='center',
            y=-0.5,
            x=0.5,
            orientation="h",
        ),
        height=70,
        font=dict(
            family="Dosis, Arial",
            size=11,
            color="#7f7f7f"
        ),
        xaxis={
            "type": "date",
            "showgrid": False,
            "side": "top",
            "zeroline": False,
            "tickformat": "%e. %b",
            'tick0': x[0],
            "dtick": 86400000.0 * 5,
        },
        yaxis={
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "side": "right",
            "ticksuffix": " °C",
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
    # max_wind_speed_in_serie = df["wind_speed_avg_10min"].max()
    # max_wind_gust_in_serie = df["wind_gust_max_10min"].max()

    trace_speed = dict(
        type="scatter",
        y=df["wind_speed_avg_10min"],
        line=dict(
            color="#069dce",
            width=2,
            smoothing=2,
        ),
        hoverinfo="skip",
        mode="lines",
        name="Windgeschw.",
    )

    trace_gust = dict(
        type="scatter",
        y=df["wind_gust_max_10min"],
        line={"color": "#0275a0"},
        hoverinfo="skip",
        mode="markers",
        opacity=0.5,
        name="Windspitzen",
    )

    layout = dict(
        plot_bgcolor=app_color["transparent"],
        paper_bgcolor=app_color["transparent"],
        margin=dict(l=0, r=40, b=10, t=25),
        hovermode="closest",
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
            "ticksuffix": " m/s",
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
        margin=dict(l=10, r=10, b=25, t=25),
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
    Output("historical-barometric-pressure", "figure"),
    [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def gen_historical_barometric_pressure_graph(interval, station_name):
    """
    Generate the barometric pressure graph.
    :params interval: update the graph based on an interval
    """

    df = get_3_hours_mean_value_of_last_five_days(station_name, "barometric_pressure_qfe")

    trace_historical_barometric_pressure = dict(
        type="scatter",
        y=df["mean"].values,
        x=df.index,
        line=dict(
            color="#000",
            width=1,
            smoothing=2,
        ),
        hoverinfo="skip",
        mode="lines",
        name="Luftdruckentwicklung",
        line_shape='linear',
    )

    layout = dict(
        plot_bgcolor=app_color["transparent"],
        paper_bgcolor=app_color["transparent"],
        margin=dict(l=0, r=50, b=10, t=15),
        hoverinfo='x+y',
        showlegend=False,
        legend=dict(
            yanchor='bottom',
            xanchor='center',
            y=-0.5,
            x=0.5,
            orientation="h",
        ),
        height=70,
        font=dict(
            family="Dosis, Arial",
            size=12,
            color="#7f7f7f"
        ),
        xaxis={
            "type": "date",
            "showgrid": False,
            "side": "top",
            "zeroline": False,
            "tickformat": "%e. %b",
            "dtick": 86400000.0 * 1,
        },
        yaxis={
            "showgrid": True,
            "showline": False,
            "zeroline": False,
            "side": "right",
            "ticksuffix": " hPa",
            "dtick": 3,
        },
    )

    return dict(data=[trace_historical_barometric_pressure], layout=layout)


@app.callback(

    Output("wind-speed-gust-and-force__predicted__text", "children"), [
        Input("update-interval", "n_intervals"),
        Input("station-switcher__options", "value")
    ],
)
def update_barometric_pressure_texts(interval, station_name):

    return get_barometric_pressure_in_current_time_period(station_name)


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
            name="Historischer Nierschlag",
            line_shape='linear',
        )

        trace_air_temperature = dict(
            type="scatter",
            y=df["mean"].values,
            x=df.index,
            hoverinfo="skip",
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(77, 150, 186, 0.2)",
            name="Aktueller Niederschlag",
            line={"width": 0}
        )

        layout = dict(
            plot_bgcolor=app_color["transparent"],
            paper_bgcolor=app_color["transparent"],
            margin=dict(l=0, r=45, b=10, t=25),
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
            xaxis={
                "type": "date",
                "showgrid": False,
                "side": "top",
                "zeroline": False,
                "tickformat": "%e. %b",
                'tick0': x[0],
                "dtick": 86400000.0 * 5,
            },
            yaxis={
                "showgrid": False,
                "showline": False,
                "zeroline": False,
                "side": "right",
                "ticksuffix": " mm",
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
            name="Historische Globalstrahlung",
            line_shape='linear',
        )

        trace_air_temperature = dict(
            type="scatter",
            y=df["mean"].values,
            x=df.index,
            hoverinfo="skip",
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(255, 245, 0, 0.3)",
            name="Aktuelle Globalstrahlung",
            line={"width": 0}
        )

        layout = dict(
            plot_bgcolor=app_color["transparent"],
            paper_bgcolor=app_color["transparent"],
            margin=dict(l=0, r=50, b=10, t=25),
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
            xaxis={
                "type": "date",
                "showgrid": False,
                "side": "top",
                "zeroline": False,
                "tickformat": "%e. %b",
                'tick0': x[0],
                "dtick": 86400000.0 * 5,
            },
            yaxis={
                "showgrid": False,
                "showline": False,
                "zeroline": False,
                "side": "right",
                "ticksuffix": " W/m2",
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
