import os
import pathlib

# Update interval
GRAPH_INTERVAL = os.environ.get("GRAPH_INTERVAL", 20000) # 20 seconds TODO: change to 60seconds
WEBAPP_TITLE = "Wetterstation für SeglerInnen"

# InfluxDB
DB_HOST = 'localhost'
DB_PORT = 8086
DB_NAME = 'meteorology'
DB_USER = 'root'
DB_PASSWORD = 'root'


# Station names to gather information from
STATIONS = {
    "mythenquai": "Mythenquai",
    "tiefenbrunnen": "Tiefenbrunnen",
}


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()