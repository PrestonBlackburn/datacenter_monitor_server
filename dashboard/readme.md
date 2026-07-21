# Sensor Monitor Dashboard
Simple dashboard to show sensor data


### Development
Env Setup
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .
```

Run the server
```bash
litestar run
litestar run --reload --debug
```

# what do we want to show?
By sensor - 
Live - Maybe last 1 hrs (sensors update every 10sec) ~1000 datapoints per sensor
Last week, aggregated to the hour, ~1000 datapoints per sensor
One time - Geo chart with sensor location shown (clickable sensors to see more details)
Should be able to click multiple sensors to overlay
Each sensor data will be dbfs for 100hz, 400hz, 1000hz, and 4khz over time

for map: https://leafletjs.com/ 

future:
query builder for custom charts
