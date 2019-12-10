# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import seaborn as sns
import warnings
import numpy as np
import scipy.stats as st
import plotly.express as px
import plotly.graph_objects as go
import dash_daq as daq
import datetime
from dash.dependencies import Input, Output
sns.set()


myth = pd.read_csv('data/messwerte_mythenquai_2019.csv', sep=',')
myth.timestamp_cet = pd.to_datetime(myth.timestamp_cet, infer_datetime_format=True)
tief = pd.read_csv('data/messwerte_tiefenbrunnen_2019.csv', sep=',')
tief.timestamp_cet = pd.to_datetime(tief.timestamp_cet, infer_datetime_format=True)

wind = px.data.wind()


# calculate probability of a storm warning (returns: prob_strong_wind, prob_sturm_wind)
def wind_prob(data):
    # Create models from data
    def best_fit_distribution(data, bins=200):
        global best_distribution
        """Model data by finding best fit distribution to data"""
        # Get histogram of original data
        y, x = np.histogram(data, bins=bins, density=True)
        x = (x + np.roll(x, -1))[:-1] / 2.0

        # Distributions to check
        DISTRIBUTIONS = [
            st.dgamma, st.expon, st.exponnorm, st.gamma, st.gengamma, st.invgamma, st.invgauss,
            st.invweibull, st.johnsonsb, st.laplace, st.logistic, st.loggamma, st.loglaplace,
            st.lognorm, st.norm, st.weibull_min, st.weibull_max
        ]

        # Best holders
        best_distribution = st.norm
        best_params = (0.0, 1.0)
        best_sse = np.inf

        # Estimate distribution parameters from data
        for distribution in DISTRIBUTIONS:

            # Try to fit the distribution
            try:
                # Ignore warnings from data that can't be fit
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore')

                    # fit dist to data
                    params = distribution.fit(data)

                    # Separate parts of parameters
                    arg = params[:-2]
                    loc = params[-2]
                    scale = params[-1]

                    # Calculate fitted PDF and error with fit in distribution
                    pdf = distribution.pdf(x, loc=loc, scale=scale, *arg)
                    sse = np.sum(np.power(y - pdf, 2.0))

                    # identify if this distribution is better
                    if best_sse > sse > 0:
                        best_distribution = distribution
                        best_params = params
                        best_sse = sse

            except Exception:
                pass

        return (best_distribution.name, best_params)

    def make_pdf(dist, params, size=10000):
        """Generate distributions's Probability Distribution Function """

        # Separate parts of parameters
        arg = params[:-2]
        loc = params[-2]
        scale = params[-1]

        # Get sane start and end points of distribution
        start = dist.ppf(0.01, *arg, loc=loc, scale=scale) if arg else dist.ppf(0.01, loc=loc, scale=scale)
        end = dist.ppf(0.99, *arg, loc=loc, scale=scale) if arg else dist.ppf(0.99, loc=loc, scale=scale)

        # Build PDF and turn into pandas Series
        x = np.linspace(start, end, size)
        y = dist.cdf(x, loc=loc, scale=scale, *arg)
        pdf = pd.Series(y, x)

        return pdf

    # Load data from statsmodels datasets
    data = data.set_index('timestamp_cet')
    data = data.wind_gust_max_10min

    # Find best fit distribution
    best_fit_name, best_fit_params = best_fit_distribution(data, 10)
    best_dist = getattr(st, best_fit_name)

    # Make PDF with best params
    pdf = make_pdf(best_dist, best_fit_params)
    pdf = pdf.to_frame()

    try:
        values_above_12 = pdf[pdf.index > 12.7]
        val = values_above_12.iloc[0][0]
        prob_strong_wind = (1 - val) * 100
    except:
        prob_strong_wind = 0

    try:
        values_above_12 = pdf[pdf.index > 16.9]
        val = values_above_12.iloc[0][0]
        prob_sturm_wind = (1 - val) * 100
    except:
        prob_sturm_wind = 0

    return prob_strong_wind, prob_sturm_wind


def query_percipitation(data):
    now = datetime.datetime.now()
    result = data.set_index(data.timestamp_cet)
    result = data[(data['timestamp_cet'].dt.month == now.month) & (data['timestamp_cet'].dt.day == now.day)]
    grouped = result.groupby(by=result['timestamp_cet'].dt.date).sum()
    rain = 0
    years = len(grouped)
    for x in grouped['precipitation']:
        if x > 0:
            rain += 1
    return rain, years


def wind_heading(direction):
    wind = []
    heading = ['N', 'NNO', 'NO', 'ONO', 'O', 'OSO', 'SO', 'SSO', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    val = int((direction % 22.5) + 0.5)
    print('direction: {}'.format(direction))
    print('val: {}'.format(val))
    if val == 16:
        val = 0
    wind.append(heading[val])
    return wind


def query_max_mean_min(data, column):
    now = datetime.datetime.now()
    result = data.set_index(data.timestamp_cet)
    result = data[(data['timestamp_cet'].dt.month == now.month) & (data['timestamp_cet'].dt.day == now.day) & (
            data['timestamp_cet'].dt.year == now.year)]
    mean_grouped = result.groupby(by=result['timestamp_cet'].dt.date).mean()
    max_grouped = result.groupby(by=result['timestamp_cet'].dt.date).max()
    min_grouped = result.groupby(by=result['timestamp_cet'].dt.date).min()
    column_mean = mean_grouped[column]
    column_max = max_grouped[column]
    column_min = min_grouped[column]

    return column_mean, column_max, column_min


data = myth
wind_data = wind_prob(data)
percipiation_data = query_percipitation(data)
wind_direction = wind_heading(data['wind_direction'].iloc[-1])
wind_direction_mean_day = query_max_mean_min(data, 'wind_direction')
print('wind_direction_mean_day: {}'.format(wind_direction_mean_day))
max_wind_gust = query_max_mean_min(data, 'wind_gust_max_10min')
top_temp = query_max_mean_min(data, 'air_temperature')
min_temp = query_max_mean_min(data, 'air_temperature')

now = datetime.datetime.now()

Stations = ['Tiefenbrunnen', 'Mythenquai']

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

app.layout = html.Div([
    # header
    html.Div(
        className="row",
        children=[
            html.Div(
                className="four columns",
                children=[
                    html.Div(
                        className="six columns",
                        children=[
                            html.H2(children="Wettermonitor"),
                        ]),
                    html.Div(
                        className="six columns",
                        id='station',
                        children=[
                            dcc.Dropdown(
                                id="stations_dropdown",
                                options=[
                                    {'label': 'Mythenquai', 'value': 'mythenquai'},
                                    {'label': 'Tiefenbrunnen', 'value': 'tiefenbrunnen'}
                                ],
                                value='mythenquai',
                                placeholder="Select a Station"
                            ),
                        ]),
                ]),
            html.Div(
                className="four columns",
                id='live-update-text',
                style={'font-size': '10px'},
                children=[

                    dcc.Interval(
                        id='interval-component',
                        interval=1 * 1000,  # in milliseconds
                        n_intervals=0
                    )
                ]),
            html.Div(
                className="four columns",
                children=[
                    # Time of last Update
                ]),
        ]),

    # info
    html.Div(
        className="row",
        children=[
            html.Div(
                className="four columns",
                children=[
                    html.H3(children="Wind"),
                ]),
            html.Div(
                className="four columns",
                children=[
                    html.H3(children="Temperatur"),
                ]),
            html.Div(
                className="four columns",
                children=[
                    html.H3(children="Diverses"),
                ]),
        ]),

    # graphs
    html.Div(
        className="row",
        children=[
            html.Div(
                className="four columns",
                children=[
                    html.Div(
                        className='six columns',
                        children=[
                            dcc.Graph(
                                id="wind_dir",
                                figure=go.Figure(go.Barpolar(
                                    r=[1],
                                    theta=[data['wind_direction'].iloc[-1]],
                                    width=[22.5],
                                    marker_color="#E4FF87",
                                    marker_line_width=2,
                                    opacity=0.8,
                                )
                                )
                            )
                        ]),
                    html.Div(
                        className='six columns',
                        children=[
                            daq.Gauge(
                                color={"gradient": True,
                                       "ranges": {"green": [0, 10], "yellow": [10, 15], "red": [15, 30]}},
                                value=data['wind_speed_avg_10min'].iloc[-1],
                                showCurrentValue=True,
                                units="m/s",
                                label='Windgeschwindigkeit',
                                max=30,
                                min=0,
                            )
                        ]),
                ]),
            html.Div(
                className="two columns",
                children=[
                    daq.Thermometer(
                        min=-10,
                        max=40,
                        value=data['air_temperature'].iloc[-1],
                        showCurrentValue=True,
                        label='Lufttemperatur',
                        units="°C"
                    )
                ]),
            html.Div(
                className="two columns",
                children=[
                    daq.Thermometer(
                        min=-10,
                        max=40,
                        value=data['windchill'].iloc[-1],
                        showCurrentValue=True,
                        label='Gefühlte Temperatur',
                        units="°C"
                    )
                ]),
            html.Div(
                className="two columns",
                children=[
                    dcc.Markdown('''
                    ###### Placeholder
                    In den letzten {} Jahren hat es {} von {} Mal an diesem Tag geregnet. 
                    '''.format(percipiation_data[1], percipiation_data[0], percipiation_data[1]))
                ]),
            html.Div(
                className="two columns",
                children=[
                    dcc.Markdown('''
                    ###### Niederschlag
                    In den letzten {} Jahren hat es {} von {} Mal an diesem Tag geregnet. 
                    '''.format(percipiation_data[1], percipiation_data[0], percipiation_data[1]))
                ]),
        ]),

    # Informations
    html.Div(
        className="row",
        children=[
            html.Div(
                className="four columns",
                children=[
                    html.Div(
                        className="row",
                        children=[
                            html.Div(
                                className='six columns',
                                children=[
                                    dcc.Graph(
                                        id="current_wind",
                                        figure=go.Figure(go.Indicator(
                                            mode="number",
                                            value=data['wind_direction'].iloc[-1],
                                            title={'text': "Windrichtung"},
                                            number={'suffix': "°"}
                                        )
                                        )
                                    )
                                ]),
                            html.Div(
                                className='six columns',
                                children=[
                                    dcc.Graph(
                                        id="wind_force",
                                        figure=go.Figure(go.Indicator(
                                            mode="number",
                                            value=data['wind_force_avg_10min'].iloc[-1],
                                            title={'text': "Windstärke"},
                                            number={'suffix': "bft"}
                                        )
                                        )
                                    )
                                ]),
                        ]),
                    html.Div(
                        className="row",
                        children=[
                            html.Div(
                                className='six columns',
                                children=[
                                    dcc.Graph(
                                        id="mean_wind",
                                        figure=go.Figure(go.Indicator(
                                            mode="number",
                                            #value=int(wind_direction_mean_day[0]),
                                            title={'text': "Ø Windrichtung"},
                                            number={'suffix': "°"}
                                        )
                                        )
                                    )
                                ]),
                            html.Div(
                                className='six columns',
                                children=[
                                    dcc.Graph(
                                        id="max_force",
                                        figure=go.Figure(go.Indicator(
                                            mode="number",
                                            #value=int(max_wind_gust[1]),
                                            title={'text': "Max. Windböen"},
                                            number={'suffix': "m/s"}
                                        )
                                        )
                                    )
                                ]),
                        ]),
                ]),
            html.Div(
                className="two columns",
                children=[

                ]),
            html.Div(
                className="two columns",
                children=[

                ]),
            html.Div(
                className="two columns",
                children=[
                    dcc.Graph(
                        id="dew_point",
                        figure=go.Figure(go.Indicator(
                            mode="number",
                            value=int(data['dew_point'].iloc[-1]),
                            number={'suffix': "°C"},
                            title={'text': "Taupunkt"}
                        )
                        )
                    )
                ]),
            html.Div(
                className="two columns",
                children=[
                    dcc.Graph(
                        id="humidity",
                        figure=go.Figure(go.Indicator(
                            mode="number",
                            value=int(data['humidity'].iloc[-1]),
                            number={'suffix': "%"},
                            title={'text': "Luftfeuchtigkeit"}
                        )
                        )
                    )
                ]),
        ]),
    html.Div(
        className="row",
        children=[
            html.Div(
                className="two columns",
                children=[
                    dcc.Graph(
                        id="stark",
                        figure=go.Figure(go.Indicator(
                            mode="number",
                            value=int(wind_data[0]),
                            number={'suffix': "%"},
                            title={'text': "Starkwindwarnung"}
                        )
                        )
                    )
                ]),
            html.Div(
                className="two columns",
                children=[
                    dcc.Graph(
                        id="storm",
                        figure=go.Figure(go.Indicator(
                            mode="number",
                            value=int(wind_data[1]),
                            number={'suffix': "%"},
                            title={'text': "Sturmwarnung"}

                        )
                        )
                    )
                ]),
            html.Div(
                className="two columns",
                children=[
                    dcc.Graph(
                        id="max_temp_hist",
                        figure=go.Figure(go.Indicator(
                            mode="number",
                            #value=int(top_temp[1]),
                            title={'text': "Rekordhoch"},
                            number={'suffix': "°C"}
                        )
                        )
                    )
                ]),
            html.Div(
                className="two columns",
                children=[
                    dcc.Graph(
                        id="min_temp_hist",
                        figure=go.Figure(go.Indicator(
                            mode="number",
                            #value=int(min_temp[2]),
                            title={'text': "Rekordtief"},
                            number={'suffix': "°C"}
                        )
                        )
                    )
                ]),
            html.Div(
                className="four columns",
                children=[
                    dcc.Graph(
                        id="pressure",
                        figure=go.Figure(go.Indicator(
                            mode="number",
                            value=int(data['barometric_pressure_qfe'].iloc[-1]),
                            title={'text': "Luftdruck"},
                            number={'suffix': " hPa"}
                        )
                        )
                    )
                ]),
        ]),
    html.Div(
        className="row",
        children=[
            html.Div(
                className="four columns",
                children=[

                ]),
            html.Div(
                className="four columns",
                children=[

                ]),
            html.Div(
                className="four columns",
                children=[

                ]),
        ]),

])


@app.callback(Output('live-update-text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_date(n):
    return [html.P('Uhrzeit: ' + str(datetime.datetime.now()))]


if __name__ == '__main__':
    app.run_server(debug=True)
