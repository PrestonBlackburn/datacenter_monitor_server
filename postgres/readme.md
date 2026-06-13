# DB Setup

## Env Vars:
```txt
POSTGRES_DB           <- database to be created
POSTGRES_USER         <- admin user to be created
POSTGRES_PASSWORD     <- admin password to be created
SENSOR_SVC_USER       <- svc user to be created
SENSOR_SVC_PASSWORD   <- svc user password
```

## Build/Setup

```sh
docker build -t sensor-postgres:latest . --no-cache

# run with env vars
docker run --name sensor-postgres -d -p 5432:5432 \
  -e POSTGRES_DB="sensors" \
  -e POSTGRES_USER="admin" \
  -e POSTGRES_PASSWORD="admin" \
  -e SENSOR_SVC_PASSWORD="default" \
  -e SENSOR_SVC_USER="sensor_svc" \
  sensor-postgres:latest
#or
docker run --name sensor-postgres -d -p 5432:5432 --env-file=.env sensor-postgres:latest
docker exec -it sensor-postgres psql -U postgres
```
<br/>

*Note: Just run pgadmin locally + port forward for easy connection*
