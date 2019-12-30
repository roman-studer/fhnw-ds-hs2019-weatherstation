# Weather station for sailors

## Getting Started

### Installation on a Raspberry Pi

First create a virtual environment with conda or venv inside a temp folder, then activate it.

```
virtualenv venv

# Windows
venv\Scripts\activate
# Or Linux
source venv/bin/activate
```

Make sure that Python 3.6+ is installed on your Raspberry Pi. Follow the instructions on https://medium.com/@isma3il/install-python-3-6-or-3-7-and-pip-on-raspberry-pi-85e657aadb1e

Clone the repo then install the requirements for the weatherstation with pip3

```
git clone https://github.com/fabianjordi/fhnw-ds-hs2019-weatherstation
cd fhnw-ds-has2019-weatherstation
pip3 install -r requirements.txt
```

Import the data from the CSVs and the API into influxDB

```
python3 import_data.py
```

Wait till the import sleeps for 600 seconds.
In another terminal run the app with 

```
python3 app.py
```

## About the app

This app displays weather data from the "Mythenquai" and the "Tiefenbrunnen" weather stations.
There is a station switcher at the top right of the app to update the graphs below.
By selecting or hovering over data in one plot will update the other plots ('cross-filtering').

## Built With

- [Dash](https://dash.plot.ly/) - Main server and interactive components
