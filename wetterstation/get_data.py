import warnings
import influxdb
import numpy as np
import pandas as pd
import scipy.stats as st
from config import *

# [ ] air_temperature(float)
# [x] barometric_pressure_qfe(float)
# [x] dew_point(float)
# [ ] global_radiation(float)
# [x] humidity(float)
# [ ] precipitation(float)
# [ ] water_level(float)
# [ ] water_temperature(float)
# [x] wind_direction(float)
# [x] wind_force_avg_10min(float)
# [x] wind_gust_max_10min(float)
# [x] wind_speed_avg_10min(float)
# [x] windchill(float)




def get_all_data(time_back):
    """
    Query all data
    :params time_back: define time span (till now)
    :returns: pandas dataframe object
    """

    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT
                *
                FROM "meteorology"."autogen"."mythenquai" WHERE time >= now() - {}""".format(time_back)

    df = pd.DataFrame(client.query(query)["mythenquai"])
    return df


def get_wind_data(time_back):
    """
    Query wind data
    :params time_back: define time span (till now)
    :returns: pandas dataframe object
    """

    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT 
                wind_direction,
                wind_force_avg_10min,
                wind_gust_max_10min,
                wind_speed_avg_10min,
                windchill
                FROM "meteorology"."autogen"."mythenquai" WHERE time >= now() - {}""".format(time_back)

    df = pd.DataFrame(client.query(query)["mythenquai"])
    return df



def get_water_temperature(go_back):
    """
    Query water temperature
    :returns: pandas dataframe object
    """

    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT 
                water_temperature
                FROM "meteorology"."autogen"."mythenquai" WHERE time >= now() - {}""".format(go_back)

    df = pd.DataFrame(client.query(query)["mythenquai"])
    return df




def get_air_temperature():
    """
    Query air temperature
    :returns: pandas dataframe object
    """

    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT 
                air_temperature
                FROM "meteorology"."autogen"."mythenquai" WHERE time >= now() - 14d"""

    df = pd.DataFrame(client.query(query)["mythenquai"])
    return df



def get_single_column(column_name, back_from_now):
    """
    Query single column
    :params column_name: column_name to query
    :params back_from_now: define time span for historic data
    :returns: pandas dataframe object
    """

    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT 
                {}
                FROM "meteorology"."autogen"."mythenquai" WHERE time >= now() - {}""".format(column_name, back_from_now)

    df = pd.DataFrame(client.query(query)["mythenquai"])
    return df



def get_last_data():

    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT
                last(*)
                FROM "meteorology"."autogen"."mythenquai" WHERE time > now() - 3h"""

    df = pd.DataFrame(client.query(query)["mythenquai"])
    return df



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