#!/usr/bin/env python
# coding: utf-8

import numpy as np
from influxdb import DataFrameClient
import requests
import json
import pandas as pd
from pandas.io.json import json_normalize
import signal
import sys
import datetime
import tzlocal
import pytz
from time import sleep
import os
import threading


class Config:
    db_host = 'localhost'
    db_port = 8086
    db_name = 'meteorology'
    stations_all = ['mythenquai', 'tiefenbrunnen']
    __stations_recorded = list(stations_all)
    stations_force_query_last_entry = False
    stations_last_entries = {}
    keys_mapping = {
        "values.air_temperature.value": "air_temperature",
        "values.barometric_pressure_qfe.value": "barometric_pressure_qfe",
        "values.dew_point.value": "dew_point",
        "values.global_radiation.value": "global_radiation",
        "values.humidity.value": "humidity",
        "values.precipitation.value": "precipitation",
        "values.timestamp_cet.value": "timestamp_cet",
        "values.water_temperature.value": "water_temperature",
        "values.wind_direction.value": "wind_direction",
        "values.wind_force_avg_10min.value": "wind_force_avg_10min",
        "values.wind_gust_max_10min.value": "wind_gust_max_10min",
        "values.wind_speed_avg_10min.value": "wind_speed_avg_10min",
        "values.windchill.value": "windchill"
    }
    historic_data_folder = '.' + os.sep + 'data'
    historic_data_chunksize = 10000
    historic_data_sleep_sec = 0
    client = None
    lock = threading.RLock()

    def get_stations(self):
        return self.stations_all

    def get_stations_recorded(self):
        recorded = None
        with self.lock:
            recorded = list(self.__stations_recorded)

        return recorded

    def add_station(self, station):
        if station in self.stations_all:
            with self.lock:
                self.__stations_recorded.append(station)
        else:
            raise Exception('{} is not part of the pre-configured collection of possible stations {}'.format(station,
                                                                                                             self.stations_all))

    def remove_station(self, station):
        with self.lock:
            self.__stations_recorded.remove(station)


def __set_last_db_entry(config, station, entry):
    current_last_time = __extract_last_db_day(config.stations_last_entries.get(station, None), station, None)
    entry_time = __extract_last_db_day(entry, station, None)

    if current_last_time is None and entry_time is not None:
        config.stations_last_entries[station] = entry
    elif current_last_time is not None and entry_time is not None and current_last_time < entry_time:
        config.stations_last_entries[station] = entry


def __get_last_db_entry(config, station):
    last_entry = None
    if not config.stations_force_query_last_entry:
        # speedup for Raspberry Pi - last entry query takes > 2 Sec.!
        last_entry = config.stations_last_entries.get(station, None)

    if last_entry is None:
        try:
            # we are only interested in time, however need to provide any field to make query work
            query = "SELECT last(air_temperature) FROM \"{}\"".format(station)
            last_entry = config.client.query(query)
        except:
            # There are influxDB versions which have an issue with above "last" query
            print(
                "An exception occurred while querying last entry from DB for " + station + ". Try alternative approach.")
            query = "SELECT * FROM \"{}\" ORDER BY time DESC LIMIT 1".format(station)
            last_entry = config.client.query(query)

    __set_last_db_entry(config, station, last_entry)
    return last_entry


def __extract_last_db_day(last_entry, station, default_last_db_day):
    if last_entry is not None:
        val = None
        if isinstance(last_entry, pd.DataFrame):
            val = last_entry
        elif isinstance(last_entry, dict):
            val = last_entry.get(station, None)

        if val is not None:
            if not val.index.empty:
                return val.index[0]

    return default_last_db_day


def __get_data_of_day(day, station):
    # convert to local time of station
    day = day.tz_convert('Europe/Zurich')
    base_url = 'https://tecdottir.herokuapp.com/measurements/{}'
    day_str = day.strftime("%Y-%m-%d")
    print("Query " + station + " at " + day_str)
    payload = {'startDate': day_str, 'endDate': day_str}
    url = base_url.format(station)
    response = requests.get(url, params=payload)
    if (response.ok):
        # print(response.json())
        jData = json.loads(response.content)
        return jData
    else:
        response.raise_for_status()


def __define_types(data, date_format, utc=False):
    data['timestamp_cet'] = pd.to_datetime(data['timestamp_cet'], format=date_format, utc=utc)
    if not data.empty and data['timestamp_cet'].iloc[0].tzinfo is None:
        data['timestamp_cet'] = data['timestamp_cet'].dt.tz_localize('Europe/Zurich', ambiguous=True).dt.tz_convert(
            'UTC')
    data.set_index('timestamp_cet', inplace=True)

    for column in data.columns[0:]:
        data[column] = data[column].astype(np.float64)

    return data


def __clean_data(config, data_of_last_day, last_db_entry, date_format, station):
    normalized = json_normalize(data_of_last_day['result'])

    for column in normalized.columns[0:]:
        mapping = config.keys_mapping.get(column, None)
        if mapping is not None:
            normalized[mapping] = normalized[column]

        normalized.drop(columns=column, inplace=True)

    # make sure types/index are correct
    normalized = __define_types(normalized, date_format)

    # print("Normalized index "+str(normalized.index))
    # print("Last db index "+str(lastDBEntry[station].index))

    # remove all entries older than last element
    last_db_entry_time = None
    if isinstance(last_db_entry, pd.DataFrame):
        last_db_entry_time = last_db_entry
    elif isinstance(last_db_entry, dict):
        last_db_entry_time = last_db_entry.get(station, None)
    last_db_entry_time = last_db_entry_time.index[0]  # .replace(tzinfo=None)
    # print("Last "+str(last_db_entry_time) +" elements "+str(normalized.index[0]) +" - "+str(normalized.index[-1]))
    normalized.drop(normalized[normalized.index <= last_db_entry_time].index, inplace=True)

    return normalized


def __add_data_to_db(config, data, station):
    config.client.write_points(data, station, time_precision='s', database=config.db_name)
    __set_last_db_entry(config, station, data.tail(1))


def __append_df_to_csv(data, csv_file_path, sep=","):
    header = False
    if not os.path.isfile(csv_file_path):
        header = True

    data.to_csv(csv_file_path, mode='a', sep=sep, header=header)


def __signal_handler(sig, frame):
    sys.exit(0)

def connect_db(config):
    """Connects to the database and initializes the client

    Parameters:
    config (Config): The Config containing the DB connection info

   """
    if config.client is None:
        # https://www.influxdata.com/blog/getting-started-python-influxdb/
        config.client = DataFrameClient(host=config.db_host, port=config.db_port, database=config.db_name)
        config.client.switch_database(config.db_name)



def clean_db(config):
    """Reads the historic data of the Wasserschutzpolizei Zurich from CSV files

    Parameters:
    config (Config): The Config containing the DB connection info and CSV folder info

   """
    config.client.drop_database(config.db_name)
    config.client.create_database(config.db_name)
    config.stations_last_entries.clear()


def import_historic_data(config):
    """Reads the historic data of the Wasserschutzpolizei Zurich from CSV files

    Parameters:
    config (Config): The Config containing the DB connection info and CSV folder info

   """
    # read historic data from files
    stations = config.get_stations_recorded()

    for station in stations:
        last_entry = __get_last_db_entry(config, station)

        if last_entry is None or not last_entry:
            print("Load historic data for " + station + " ...")

            file_name = os.path.join(config.historic_data_folder, "messwerte_" + station + "_2007-2018.csv")
            if os.path.isfile(file_name):
                print("\tLoad " + file_name)
                for chunk in pd.read_csv(file_name, delimiter=',', chunksize=config.historic_data_chunksize):
                    chunk = __define_types(chunk, '%Y-%m-%dT%H:%M:%S')
                    print("Add " + station + " from " + str(chunk.index[0]) + " to " + str(chunk.index[-1]))
                    __add_data_to_db(config, chunk, station)

                    if config.historic_data_sleep_sec > 0:
                        sleep(config.historic_data_sleep_sec)
            else:
                print(file_name + " does not seem to exist.")

            current_time = datetime.datetime.now(tzlocal.get_localzone())
            running_year = 2019
            while running_year <= current_time.year:
                file_name = os.path.join(config.historic_data_folder,
                                         "messwerte_" + station + "_" + str(running_year) + ".csv")
                if os.path.isfile(file_name):
                    print("\tLoad " + file_name)
                    for chunk in pd.read_csv(file_name, delimiter=',', chunksize=config.historic_data_chunksize):
                        chunk = __define_types(chunk, '%Y-%m-%d %H:%M:%S', utc=True)
                        print("Add " + station + " from " + str(chunk.index[0]) + " to " + str(chunk.index[-1]))
                        __add_data_to_db(config, chunk, station)

                        if config.historic_data_sleep_sec > 0:
                            sleep(config.historic_data_sleep_sec)
                else:
                    print(file_name + " does not seem to exist.")
                running_year += 1
        else:
            print("There is already data for " + station + ". No historic data will be imported.")

        print("Historic data for " + station + " loaded.")


def import_latest_data(config, append_to_csv=False, periodic_read=False):
    """Reads the latest data from the Wasserschutzpolizei Zurich weather API

    Parameters:
    config (Config): The Config containing the DB connection info and CSV folder info
    append_to_csv (bool): Defines if the data should be appended to a CSV file
    periodic_read (bool): Defines if the function should keep reading after it imported the latest data (blocking through a sleep)

   """
    stations = config.get_stations_recorded()

    # access API for current data
    current_time = datetime.datetime.now(pytz.utc)
    #current_time = datetime.datetime.now(pytz.timezone("Europe/Zurich"))
    current_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    last_db_days = [current_day] * len(stations)
    new_data_received = True

    for idx, station in enumerate(stations):
        last_db_entry = __get_last_db_entry(config, station)
        last_db_days[idx] = __extract_last_db_day(last_db_entry, station, last_db_days[idx])

    if periodic_read:
        signal.signal(signal.SIGINT, __signal_handler)
        print("\nPress Ctrl+C to stop!\n")

    while True:
        current_time = datetime.datetime.now(pytz.utc)
        #current_time = datetime.datetime.now(pytz.timezone("Europe/Zurich"))

        # check if all historic data (retrieved from API) has been processed
        last_db_day = max(last_db_days)
        if periodic_read and last_db_day >= current_day:
            # once every 10 Min
            sleep_until = current_time + datetime.timedelta(minutes=10)
            # once per day
            # sleep_until = current_time + datetime.timedelta(days=1)
            # sleep_until = sleep_until.replace(hour=6, minute=0, second=0, microsecond=0)
            sleep_sec = (sleep_until - current_time).total_seconds()

            print("Sleep for " + str(sleep_sec) + "s (from " + str(current_time) + " until " + str(
                sleep_until) + ") when next data will be queried.")
            sleep(sleep_sec)
            current_time = datetime.datetime.now(pytz.utc)
            #current_time = datetime.datetime.now(pytz.timezone("Europe/Zurich"))
            current_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif not periodic_read and not new_data_received:
            # stop here
            return;

        new_data_received = False
        for idx, station in enumerate(stations):
            last_db_entry = __get_last_db_entry(config, station)
            last_db_days[idx] = __extract_last_db_day(last_db_entry, station, last_db_days[idx])
            data_of_last_db_day = __get_data_of_day(last_db_days[idx], station)

            normalized_data = __clean_data(config, data_of_last_db_day, last_db_entry, '%d.%m.%Y %H:%M:%S', station)

            if normalized_data.size > 0:
                new_data_received = True
                __add_data_to_db(config, normalized_data, station)
                if append_to_csv:
                    __append_df_to_csv(normalized_data, os.path.join(config.historic_data_folder,
                                                                     "messwerte_" + station + "_" + str(
                                                                         current_time.year) + ".csv"))
                print("Handle " + station + " from " + str(normalized_data.index[0]) + " to " + str(
                    normalized_data.index[-1]))
            else:
                print("No new data received for " + station)


if __name__ == '__main__':

    # DB and CSV config
    config = Config()
    # define CSV path
    config.historic_data_folder = '.' + os.sep + 'data'
    # set batch size for DB inserts (decrease for raspberry pi)
    config.historic_data_chunksize = 10000
    # define DB host
    config.db_host = '127.0.0.1'
    # define port of host
    config.db_post = '8086'

    # connect to DB
    print('Conntect to database')
    connect_db(config)

    # clean DB
    clean_db(config)
    # import historic data
    import_historic_data(config)
    # Read the latest data from the Wasserschutzpolizei Zurich weather API
    # import latest data (delta between last data point in DB and current time)
    print('Import API data, rerun every 600 seconds')
    import_latest_data(config, False, True)

