import warnings
import influxdb
import numpy as np
import pandas as pd
import scipy.stats as st
import datetime as dt
from config import *
from helpers import *

# [x] air_temperature(float)
# [x] barometric_pressure_qfe(float)
# [x] dew_point(float)
# [x] global_radiation(float)
# [x] humidity(float)
# [x] precipitation(float)
# [ ] water_level(float)
# [x] water_temperature(float)
# [x] wind_direction(float)
# [x] wind_force_avg_10min(float)
# [x] wind_gust_max_10min(float)
# [x] wind_speed_avg_10min(float)
# [x] windchill(float)

client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)


def get_wind_data(station_name, time_back):
    """
    Query wind data
    :params time_back: define time span (till now)
    :returns: pandas dataframe object
    """

    query = """SELECT 
                wind_direction,
                wind_force_avg_10min,
                wind_gust_max_10min,
                wind_speed_avg_10min,
                windchill
                FROM "meteorology"."autogen"."{}" WHERE time >= now() - {}""".format(station_name, time_back)

    df = pd.DataFrame(client.query(query)[station_name])
    return df


def get_daily_value_of_past(station_name, column_name):
    """
    Query mean value of column of all data per
    :params station_name: station to query data from
    :params column_name: column_name to query
    :returns: pandas dataframe object
    """

    query = """SELECT 
                mean({})
                FROM "meteorology"."autogen"."{}"
                WHERE time < now()
                GROUP BY time(24h)""".format(column_name, station_name)

    df = pd.DataFrame(client.query(query)[station_name])
    return df


def get_daily_value_of_last_two_weeks(station_name, column_name):
    """
    Query mean value of column of two week old data till now
    :params station_name: station to query data from
    :params column_name: column_name to query
    :returns: pandas dataframe object
    """

    query = """SELECT 
                mean({})
                FROM "meteorology"."autogen"."{}"
                WHERE time > now() - 14d
                GROUP BY time(24h)""".format(column_name, station_name)

    df = pd.DataFrame(client.query(query)[station_name])
    return df


def get_3_hours_mean_value_of_last_five_days(station_name, column_name):
    """
    Query mean value of column of five days old data till now
    :params station_name: station to query data from
    :params column_name: column_name to query
    :returns: pandas dataframe object
    """

    query = """SELECT 
                mean({})
                FROM "meteorology"."autogen"."{}"
                WHERE time > now() - 5d
                GROUP BY time(3h)""".format(column_name, station_name)

    df = pd.DataFrame(client.query(query)[station_name])
    return df


def get_single_column(station_name, column_name, back_from_now):
    """
    Query single column
    :params station_name: station to query data from
    :params column_name: column_name to query
    :params back_from_now: define time span for historic data
    :returns: pandas dataframe object
    """

    query = """SELECT 
                {}
                FROM "meteorology"."autogen"."{}"
                WHERE time >= now() - {}""".format(column_name, station_name, back_from_now)

    df = pd.DataFrame(client.query(query)[station_name])
    return df


def get_mean_value_of_last_week_between_time(station_name, column_name, back_from_now, time_start, time_end):
    """
    Get the mean value for the last week in specific time frame
    :params station_name: station to query data from
    :params column_name: column_name to query
    :params back_from_now: define time span for historic data
    :params time_start: hour and minutes (and seconds), e.g. "11:00" or "12:20:00"
    :params time_end: hour and minutes (and seconds), e.g. "15:00" or "17:20:00"
    :returns: pandas dataframe object with one row
    """

    df = get_single_column(station_name, column_name, back_from_now)
    df = df.between_time(time_start, time_end)
    df = df.mean()

    return df


def get_last_timestamp_of_entry(station_name, column_name):
    """
    Get last timestamp of single entry
    :params station_name: station to query data from
    :params column_name: column_name to query
    :returns: pandas dataframe object with one row
    """

    query = """SELECT
                last({}), time
                FROM "meteorology"."autogen"."{}" """.format(column_name, station_name)

    df = pd.DataFrame(client.query(query)[station_name])
    return df


def get_last_data(station_name):
    """
    Get last data as single row of pandas dataframe
    :params station_name: station to query data from
    :returns: pandas dataframe object with one row
    """
    query = """SELECT
                last(*)
                FROM "meteorology"."autogen"."{}" """.format(station_name)

    df = pd.DataFrame(client.query(query)[station_name])
    return df


def get_data_for_wind_warnings(station_name):
    """
    Get wind data and calculate possibility of storm warning
    :params station_name: station to query data from
    :returns: possibility of wind and storm warning probability
    """

    # Create models from data
    def best_fit_distribution(data, bins=200):

        global best_distribution

        # """Model data by finding best fit distribution to data"""
        # Get histogram of original data
        y, x = np.histogram(data.values, bins=bins, density=True)
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
    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT
                wind_gust_max_10min
                FROM "meteorology"."autogen"."{}"
                WHERE time > now() - 6h""".format(station_name)

    df = pd.DataFrame(client.query(query)[station_name])

    # Find best fit distribution
    best_fit_name, best_fit_params = best_fit_distribution(df, 10)
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


def get_data_in_current_time_period(data, days_back, days_forward):
    """
    Get data within current time period independently of year
    :params station_name: station to query data from
    :params days_back: days to go into past
    :params days_forward: days to go into "future"
    :returns: filtered dataframe
    """

    last_entry = data.iloc[-1:]
    month_back = int((last_entry.index[0] + dt.timedelta(days=-days_back)).strftime('%-m'))
    month_forward = int((last_entry.index[0] + dt.timedelta(days=days_forward)).strftime('%-m'))
    day_back = int((last_entry.index[0] + dt.timedelta(days=-days_back)).strftime('%-d'))
    day_forward = int((last_entry.index[0] + dt.timedelta(days=days_forward)).strftime('%-d'))
    # print('month_back: {}'.format(month_back))
    # print('day_back: {}'.format(day_back))
    # print('month_forward: {}'.format(month_forward))
    # print('day_forward: {}'.format(day_forward))

    df_filtered = data[
        ((data.index.month >= month_back) & (data.index.day >= day_back)
         |
         (data.index.month <= month_forward) & (data.index.day <= day_forward))
    ]

    return df_filtered


def get_barometric_pressure_in_current_time_period(station_name):
    """
    Find similar barometric pressure in history with
    similar wind force and returns a corresponding message
    :params station_name: station to query data from
    :returns: message with some predictions of wind force
    """

    try:
        query = """SELECT 
                    mean(barometric_pressure_qfe) AS mean_barometric_pressure_qfe
                    FROM "meteorology"."autogen"."{}"
                    WHERE time > now() - 6h GROUP BY time(1h) fill(previous)""".format(station_name)

        df = pd.DataFrame(client.query(query)[station_name])

        message = """Der {} Luftdruck
                    (aktuell {} hPa) ist {}.
                    Er geht einher mit {} Windstärke.
                    In den kommenden 6 Stunden wird die Windstärke zwischen {} und {} Beaufort liegen."""

        barometric_pressure_value_last = float(df.iloc[-1:].values[0])
        barometric_pressure_value_6h_ago = float(df.iloc[0:].values[0])

        if (barometric_pressure_value_last < barometric_pressure_value_6h_ago):
            string = "sinkende"
            string2 = "durchschnittlich zunehmender"
        elif (barometric_pressure_value_last == barometric_pressure_value_6h_ago):
            string = "gleich bleibende"
            string2 = "gleich bleibender"
        else:
            string = "steigende"
            string2 = "durchschnittlich abnehmender"

        message = message.format(string, "{}", "{}", "{}", "{}", "{}")
        message = message.format(round_up(barometric_pressure_value_last, 0), "{}", "{}", "{}", "{}")

        # Get data for pressure distribution/quantiles
        query = """SELECT 
                    mean(barometric_pressure_qfe) AS mean_barometric_pressure_qfe
                    FROM "meteorology"."autogen"."{}"
                    WHERE time < now() GROUP BY time(5d)""".format(station_name)

        df = pd.DataFrame(client.query(query)[station_name])

        df = remove_outliers(df, "mean_barometric_pressure_qfe")  # Filter outliers and replace them with median
        df_filtered = get_data_in_current_time_period(df, 15, 15)  # Filter for current time period

        if (barometric_pressure_value_last < df_filtered.quantile(0.2).values):
            string = "unterdurchschnittlich tief"
        elif (barometric_pressure_value_last < df_filtered.quantile(0.5).values):
            string = "leicht unterdurchschnittlich tief"
        elif (barometric_pressure_value_last < df_filtered.quantile(0.8).values):
            string = "leicht überdurchschnittlich hoch"
        else:
            string = "überdurchschnittlich hoch"

        message = message.format(string, "{}", "{}", "{}")
        message = message.format(string2, "{}", "{}")

        # Get data for wind force prediction
        query = """SELECT
                last(wind_force_avg_10min) AS last_wind_force_avg_10min,
                last(barometric_pressure_qfe) AS last_barometric_pressure_qfe
                FROM "meteorology"."autogen"."{}" """.format(station_name)

        df_last = pd.DataFrame(client.query(query)[station_name])
        last_barometric_pressure_qfe = float(df_last["last_barometric_pressure_qfe"].values)
        last_wind_force_avg_10min = float(df_last["last_wind_force_avg_10min"].values)

        # find similar conditions, stop if something found
        # "simulate" HAVING clause
        len_of_df = 0
        factor = 0.1
        while len_of_df <= 0:

            query = """SELECT
                    (wind_force_avg_10min),
                    (barometric_pressure_qfe)
                    FROM "meteorology"."autogen"."{}"
                    WHERE
                        (barometric_pressure_qfe > {} AND barometric_pressure_qfe < {})
                        AND
                        (wind_force_avg_10min > {} AND wind_force_avg_10min < {})
                        AND
                        (time < now() - 1d)""".format(
                station_name,
                last_barometric_pressure_qfe - factor * 2,
                last_barometric_pressure_qfe + factor * 2,
                last_wind_force_avg_10min - (factor * 1),
                last_wind_force_avg_10min + (factor * 1))

            df = pd.DataFrame(client.query(query)[station_name])
            len_of_df = len(df)
            factor += 0.1
            if factor == 10:
                break

        # loop in widening day span, break if 20 results are found
        days_span = 10
        df_f = df
        len_of_df_f = len(df_f)

        while len_of_df_f > 20:

            df_f = get_data_in_current_time_period(df, days_span, days_span)  # Filter for current time period

            len_of_df_f = len(df_f)
            days_span -= 1
            if days_span == 1:
                break

        # take first result and use for forecast
        df_final = df.loc[
                   df_f.iloc[0:].index[0] + dt.timedelta(hours=-2)
                   :
                   df_f.iloc[0:].index[0] + dt.timedelta(hours=6)
                   ]

        # go 2 hours back and 6 forward, get min and max values
        datetime_start = (df_f.iloc[0:].index[0] + dt.timedelta(hours=-2)).tz_localize(tz=None)
        datetime_end = (df_f.iloc[0:].index[0] + dt.timedelta(hours=6)).tz_localize(tz=None)

        query = """SELECT
                    (wind_force_avg_10min),
                    (barometric_pressure_qfe)
                    FROM "meteorology"."autogen"."{}"
                    WHERE
                        (time >= '{}' AND time <= '{}')""".format(
            station_name,
            datetime_start,
            datetime_end
        )

        df_final = pd.DataFrame(client.query(query)[station_name])

        message = message.format(
            round_up(df_final["wind_force_avg_10min"].min(), 1),
            round_up(df_final["wind_force_avg_10min"].max(), 1))

        return message

    except:

        return """Fehler aufgetreten. Es liegen womöglich keine aktuellen
        Luftdruck- oder Windstärkedaten vor."""


def remove_outliers(df_in, col_name):
    """
    Removes outliers within dataframe
    :params df_in: dataframe to remove outliers
    :params col_name: column name to be modified
    :returns: dataframe without outliers in specific column
    """

    q1 = df_in[col_name].quantile(0.25)
    q3 = df_in[col_name].quantile(0.75)
    iqr = q3 - q1  # Interquartile range
    fence_low = q1 - 1.5 * iqr
    fence_high = q3 + 1.5 * iqr
    df_out = df_in.loc[(df_in[col_name] > fence_low) & (df_in[col_name] < fence_high)]

    return df_out
