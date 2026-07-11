Handles reading from Chripstack MQTT Broker and writing to TimescaleDB

For testing mqtt sub
```bash
kubectl port-forward -n chirp svc/chirpstack-mosquitto-svc 1883:1883
```

Test
```bash
python consumer.py
```

```bash
docker build -t sensor-consumer:latest . --no-cache
# assuming other services are already port forwareded:
docker run --name sensor-consumer --rm --add-host=host.docker.internal:host-gateway --env-file=.env sensor-consumer:latest
```

Example required env vars:
```env
TOPIC_FILTER=application/+/device/+/event/up
TOPIC_RE='^application/[^/]+/device/([0-9a-fA-F]+)/event/up$'
QOS=0
HOST=localhost
PORT=1883
POSTGRES_DB=sensors
SENSOR_SVC_PASSWORD=...
SENSOR_SVC_USER=...
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```