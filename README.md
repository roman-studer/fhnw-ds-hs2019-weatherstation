# Wetterstation für Segler

## Getting Started

### Die App lokal installieren

First create a virtual environment with conda or venv inside a temp folder, then activate it.

```
virtualenv venv

# Windows
venv\Scripts\activate
# Or Linux
source venv/bin/activate
```

Clone the git repo, then install the requirements with pip

```
git clone https://github.com/fabianjordi/fhnw-ds-hs2019-weatherstation
cd fhnw-ds-has2019-weatherstation
pip install -r requirements.txt
```

Import the data from the CSVs and the API into influxDB

```
python import_data.py
```

Wait till the import sleeps for 600 seconds. Then run the app with 

```
python app.py
```

in another terminal.

## About the app

This app displays weather data from the "Mythenquai" and the "Tiefenbrunnen" weather stations.
There is a station switcher at the top right of the app to update the graphs below.
By selecting or hovering over data in one plot will update the other plots ('cross-filtering').

## Built With

- [Dash](https://dash.plot.ly/) - Main server and interactive components
