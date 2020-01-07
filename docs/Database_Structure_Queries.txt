Documentation Database 'meteorology'

Database Type: InfluxDB v1.7
Database URL: http://localhost:8086
User: root
Passwort: Auf Anfrage
Database: meteorology
Tables:
  mythenquai
  tiefenbrunnen

Table mythenquai:

  Columns:
    Index: timestamp_cet(datetime:  %YY-%MM%-%DD %HH:%MM:%%SS)
    air_temperature (float)
    barometric_pressure_qfe(float)
    dew_point(float)
    global_radiation(float)
    humidity(float)
    precipitation(float)
    water_level(float)
    water_temperature(float)
    wind_direction(float)
    wind_force_avg_10min(float)
    wind_gust_max_10min(float)
    wind_speed_avg_10min(float)
    windchill(float)

Table tiefenbrunnen:

  Columns:
    Index: timestamp_cet(datetime:  %YY-%MM%-%DD %HH:%MM:%%SS)
    air_temperature(float)
    barometric_pressure_qfe(float)
    dew_point(float)
    humidity(float)
    water_temperature(float)
    wind_direction(float)
    wind_force_avg_10min(float)
    wind_gust_max_10min(float)
    wind_speed_avg_10min(float)
    windchill(float)

Queries:
All queries documentented in this document are used in the'weatherstation'-project and
are visible in the code of the project. All queries are in the "get_data.py"-file.
All queries are used to minimize the data and speed up the scripts. Every query is
used to pull data of the database for further processing. No joining of tables or
expensive calculations are done by querying the database.


Query 'get_wind_data'

  Use:  This query is used to get all data in a certain timespan for the following
        columns in a datasets:
        - wind_direction,
        - wind_force_avg_10min,
        - wind_gust_max_10min,
        - wind_speed_avg_10min,
        - windchill
  Query:
        SELECT
          wind_direction,
          wind_force_avg_10min,
          wind_gust_max_10min,
          wind_speed_avg_10min,
          windchill
          FROM "meteorology"."autogen"."{}" WHERE time >= now() - {}
  Comment:
        The query allows to filter the data of the database in a certain time range.
        Using the "time >= xy"-Method we can control the amount of data that gets
        downloaded onto the machine for further processing. Specifing the timespan
        allows us to control the batch size of a query.

        This Query is implemented into the python-function 'get_wind_data' in the
        get_data.py file.


Query 'get_daily_value_of_past'

  Use:  Query the mean of a column of all data in the table, grouped by 24 hours.
  Query:
        SELECT
            mean({})
            FROM "meteorology"."autogen"."{}"
            WHERE time < now()
            GROUP BY time(24h)
  Comment:
        This query groups a column of a table into 24 hours, and returns the mean
        of that range. This can be used to create a graph of the historical data.
        Which only needs the mean value per day.

Query 'get_daily_value_of_last_two_weeks'

  Use:  Query mean value of column of two week old data till now
  Query:
        SELECT
            mean({})
            FROM "meteorology"."autogen"."{}"
            WHERE time > now() - 14d
            GROUP BY time(24h)
  Comment:
        This query makes it possible to query the last two weeks of a certain column and
        table. Then group the data into the mean of each day. This greatly reduces the
        number of datapoints we need to download.


Query 'get_3_hours_mean_value_of_last_five_days'

  Use:  Query mean value of column of five days old data till now
  Query:
        SELECT
            mean({})
            FROM "meteorology"."autogen"."{}"
            WHERE time > now() - 5d
            GROUP BY time(3h)
  Comment:
        Makes it possible to query one work-week in the past.


Query 'get_single_column'

    Use:  Queries a single columns
    Query:
          SELECT
                {}
                FROM "meteorology"."autogen"."{}"
                WHERE time >= now() - {}
    Comment:
          Limits the queried data to a certain column in a table and sets a timespan.


Query 'get_timestamp_of_last_entry'

    Use: Gets the last timestamp of a single entry. Is used to display the
        'last update'-time on the dashboard.
    Query:
        SELECT
              last({}), time
              FROM "meteorology"."autogen"."{}
    Comment:
          Simple solution to get the time of the last update

Query 'get_last_data'

    Use: Gets the latest row of data for a table
    Query:
        SELECT
            last(*)
            FROM "meteorology"."autogen"."{}
    Comment:
        Short Query that is used to get the latest data for every column
        Will be used to display live data.


Query 'get_data_for_wind_warnings'

    Use: Let's us get data of the 'wind_gust_max_10min'-column for the last 6 hours.
    Query:
        SELECT
            wind_gust_max_10min
            FROM "meteorology"."autogen"."{}"
            WHERE time > now() - 6h
    Comment:
        Is used to create a prediction for wind and storm warnings.


Query 'get_barometric_pressure_in_current_time_period'

    Use: Query barometric_pressure_qfe and wind_force_avg_10min
    Query:
        SELECT
            mean(barometric_pressure_qfe) AS mean_barometric_pressure_qfe
            FROM "meteorology"."autogen"."{}"
            WHERE time > now() - 4h GROUP BY time(1h) fill(previous)

    Second_Query:
        SELECT
            mean(barometric_pressure_qfe) AS mean_barometric_pressure_qfe
            FROM "meteorology"."autogen"."{}"
            WHERE time < now() GROUP BY time(5d)
    Third_Query:
        SELECT
            last(wind_force_avg_10min) AS last_wind_force_avg_10min,
            last(barometric_pressure_qfe) AS last_barometric_pressure_qfe
            FROM "meteorology"."autogen"."{}'
    Fourth_Query:
        SELECT
            (wind_force_avg_10min),
            (barometric_pressure_qfe)
            FROM "meteorology"."autogen"."{}"
            WHERE
                (barometric_pressure_qfe > {} AND barometric_pressure_qfe < {})
                AND
                (wind_force_avg_10min > {} AND wind_force_avg_10min < {})
                AND
                (time < now() - 1d)
    Fifth_Query:
        SELECT
            (wind_force_avg_10min),
            (barometric_pressure_qfe)
            FROM "meteorology"."autogen"."{}"
            WHERE
                (time >= '{}' AND time <= '{}')
    Comment:
        #TO DO: Comment on query


Query 'get_air_temperature_forecast_values'

    Use: Queries the last datapoint for the following columns:
      - air_temperature
      - dew_point
      - humidity
      - barometric_pressure_qfe
    Query:
        SELECT
            last(air_temperature) AS last_air_temperature,
            last(dew_point) AS last_dew_point,
            last(humidity) AS last_humidity,
            last(barometric_pressure_qfe) AS last_barometric_pressure_qfe
            FROM "meteorology"."autogen"."{}
    Comment: Limits the datapoints that need to be queried

    Second_Query:
        SELECT
            (air_temperature),
            (dew_point),
            (humidity),
            (barometric_pressure_qfe)
            FROM "meteorology"."autogen"."{}"
            WHERE
                (air_temperature > {} AND air_temperature < {})
                AND
                (dew_point > {} AND dew_point < {})
                AND
                (humidity > {} AND humidity < {})
                AND
                (barometric_pressure_qfe > {} AND barometric_pressure_qfe < {})
                AND
                (time < now() - 3d)
      Comment: Use the information of the first query to search for similar rows
      in the data.

      Third_Query:
          SELECT
            (air_temperature)
            FROM "meteorology"."autogen"."{}"
            WHERE
                (time >= '{}' AND time <= '{}')
