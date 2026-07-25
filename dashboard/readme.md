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
litestar --app=dashboard_app:app run --reload --debug
```

```sh
docker build -t sensor-dashboard:latest . --no-cache

# run with env vars
docker run --name sensor-dashboard -d -p 8000:8000 \
  -e POSTGRES_DB="sensors" \
  -e POSTGRES_USER="admin" \
  -e POSTGRES_PASSWORD="admin" \
  -e SENSOR_SVC_PASSWORD="default" \
  -e SENSOR_SVC_USER="sensor_svc" \
  sensor-dashboard:latest
#or
# assumes pg in another container
docker run --name sensor-dashboard --rm -p 8000:8000 --add-host=host.docker.internal:host-gateway --env-file=.env_cluster sensor-dashboard:latest
```

