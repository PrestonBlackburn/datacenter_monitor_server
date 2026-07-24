# sensor info
# create table if not exists app.audio_sensor_info (
#     sensor_id       text not null,
#     created_time    timestamptz not null,
#     updated_time    timestamptz not null,
#     lat             DOUBLE PRECISION,
#     long            DOUBLE PRECISION,
#     geo_time_start  timestamptz,
#     geo_time_stop   timestamptz,
#     tags            JSONB
# );

from dataclasses import dataclass
from datetime import datetime
import math
import logging

import psycopg
from psycopg.types.json import Jsonb

from dashboard_app.models.datacenter_info import get_datacenter_by_name, DatacenterInfo

_logger = logging.getLogger(__name__)

@dataclass
class SensorInfo:
    sensor_id: str
    created_time: datetime
    updated_time: datetime
    lat: float
    long: float
    geo_time_start: datetime
    geo_time_stop: datetime
    tags: dict


    async def insert(self, conn: psycopg.AsyncConnection) -> None:
        sql = """INSERT INTO app.audio_sensor_info
            (
                sensor_id,
                created_time,
                updated_time,
                lat,
                long,
                geo_time_start,
                geo_time_end,
                tags
            )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        async with conn.cursor() as cur:
            await cur.execute(sql, (
                self.sensor_id,
                self.created_time,
                self.updated_time,
                self.lat,
                self.long,
                self.geo_time_start,
                self.geo_time_stop,
                Jsonb(self.tags)
            ))
            await conn.commit()


async def get_sensor_by_name(
    sensor_name: str,
    conn: psycopg.AsyncConnection
) -> SensorInfo | None: 
    sql = """SELECT
        sensor_id,
        created_time,
        updated_time,
        lat,
        long,
        geo_time_start,
        geo_time_end,
        tags
    FROM app.audio_sensor_info
    WHERE sensor_id ilike %s
    """
    sensors = []
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, (sensor_name,))
            rows = await cur.fetchall()

            for row in rows:
                sensor_info = SensorInfo(
                    sensor_id = row['sensor_id'],
                    created_time = row['created_time'],
                    updated_time = row['updated_time'],
                    lat = row['lat'],
                    long = row['long'],
                    geo_time_start=row["geo_time_start"],
                    geo_time_end=row["geo_time_end"],
                    tags=row["tags"]
                )
                sensors.append(sensor_info)
    except Exception as e:
        _logger.error(f"Error getting closest datacetner: {e}")

    if len(sensors) > 1:
        _logger.warning(f"Got multiple sensors for name: {sensor_name}")
    if len(sensors) == 0:
        return None
    
    sensor = sensors[0]
    
    return sensor
    

async def get_sensors_in_range(
    lat: float,
    long: float,
    conn: psycopg.AsyncConnection,
    max_distance_mi: float = 5.0
) -> list[SensorInfo]:
    sql = """SELECT
        sensor_id,
        created_time,
        updated_time,
        lat,
        long,
        geo_time_start,
        geo_time_end,
        tags
    FROM app.audio_sensor_info
    WHERE
        lat BETWEEN %s and %s
        AND long BETWEEN %s and %s
    ORDER BY power(lat - %s, 2) + power((long - %s) * cos(radians(%s)), 2)
    """
    lat_delta = max_distance_mi / 69
    long_delta = max_distance_mi / (69 * math.cos(math.radians(lat)))
    lat_min = lat - lat_delta
    lat_max = lat + lat_delta
    long_min = long - long_delta
    long_max = long + long_delta
    sensors = []
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, (
                lat_min, 
                lat_max, 
                long_min, 
                long_max, 
                lat, 
                long, 
                lat
            ))
            rows = await cur.fetchall()

            for row in rows:
                sensor_info = SensorInfo(
                    sensor_id = row['sensor_id'],
                    created_time = row['created_time'],
                    updated_time = row['updated_time'],
                    lat = row['lat'],
                    long = row['long'],
                    geo_time_start=row["geo_time_start"],
                    geo_time_end=row["geo_time_end"],
                    tags=row["tags"]
                )
            sensors.append(sensor_info)
    except Exception as e:
        _logger.error(f"Error getting closest datacetner: {e}")
    
    return sensors

    

async def get_sensors_by_datacenter(
    datacenter: str | DatacenterInfo,
    conn: psycopg.AsyncConnection,
    max_distance_mi: float = 5.0
) -> list[SensorInfo]: 
    if isinstance(datacenter, str):
        datacenter: DatacenterInfo = await get_datacenter_by_name(datacenter)

    sql = """SELECT
        sensor_id,
        created_time,
        updated_time,
        lat,
        long,
        geo_time_start,
        geo_time_end,
        tags
    FROM app.audio_sensor_info
    WHERE
        lat BETWEEN %s and %s
        AND long BETWEEN %s and %s
    ORDER BY power(lat - %s, 2) + power((long - %s) * cos(radians(%s)), 2)
    """
    lat_delta = max_distance_mi / 69
    long_delta = max_distance_mi / (69 * math.cos(math.radians(datacenter.lat)))
    lat_min = datacenter.lat - lat_delta
    lat_max = datacenter.lat + lat_delta
    long_min = datacenter.long - long_delta
    long_max = datacenter.long + long_delta
    sensors = []
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, (
                lat_min, 
                lat_max, 
                long_min, 
                long_max, 
                datacenter.lat, 
                datacenter.long, 
                datacenter.lat
            ))
            rows = await cur.fetchall()

            for row in rows:
                sensor_info = SensorInfo(
                    sensor_id = row['sensor_id'],
                    created_time = row['created_time'],
                    updated_time = row['updated_time'],
                    lat = row['lat'],
                    long = row['long'],
                    geo_time_start=row["geo_time_start"],
                    geo_time_end=row["geo_time_end"],
                    tags=row["tags"]
                )
            sensors.append(sensor_info)
    except Exception as e:
        _logger.error(f"Error getting sensor info for datacenter: {datacenter.name} \n Error: {e}")
    
    return sensors