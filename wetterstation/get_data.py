import pandas as pd
import influxdb
from config import *

# [ ] air_temperature(float)
# [ ] barometric_pressure_qfe(float)
# [ ] dew_point(float)
# [ ] global_radiation(float)
# [ ] humidity(float)
# [ ] precipitation(float)
# [ ] water_level(float)
# [ ] water_temperature(float)
# [x] wind_direction(float)
# [x] wind_force_avg_10min(float)
# [x] wind_gust_max_10min(float)
# [x] wind_speed_avg_10min(float)
# [ ] windchill(float)


def get_wind_data(time_back):
    """
    Query wind data
    :params start: start row id TODO: remove line
    :params end: end row id TODO: remove line
    :returns: pandas dataframe object
    """

    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT 
                wind_direction,
                wind_force_avg_10min,
                wind_gust_max_10min,
                wind_speed_avg_10min,
                windchill
                FROM "meteorology"."autogen"."mythenquai" where time >= now() - {}""".format(time_back)

    df = pd.DataFrame(client.query(query)["mythenquai"])
    return df



def get_water_temperature():
    """
    Query water temperature
    :params start: start row id TODO: remove line
    :params end: end row id TODO: remove line
    :returns: pandas dataframe object
    """

    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT 
                water_temperature
                FROM "meteorology"."autogen"."mythenquai" where time >= now() - 14d"""

    df = pd.DataFrame(client.query(query)["mythenquai"])
    return df




def get_air_temperature():
    """
    Query air temperature
    :params start: start row id TODO: remove line
    :params end: end row id TODO: remove line
    :returns: pandas dataframe object
    """

    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT 
                air_temperature
                FROM "meteorology"."autogen"."mythenquai" where time >= now() - 14d"""

    df = pd.DataFrame(client.query(query)["mythenquai"])
    return df


def get_last_data():

    client = influxdb.DataFrameClient(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

    query = """SELECT
                last(*)
                FROM "meteorology"."autogen"."mythenquai" WHERE time > now() - 3h"""

    df = pd.DataFrame(client.query(query)["mythenquai"])
    return df