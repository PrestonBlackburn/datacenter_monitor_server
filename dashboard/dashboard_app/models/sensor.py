# create table if not exists app.audio_sensor (
#     received_time    timestamptz not null,
#     sensor_id        text not null,
#     hz               DOUBLE PRECISION,
#     dbfs             DOUBLE PRECISION
# ) WITH (
#     tsdb.hypertable,
#     tsdb.segmentby = 'sensor_id',
#     tsdb.partition_column = 'received_time'
# );

from dataclasses import dataclass
from datetime import datetime
import psycopg

from dashboard_app.models.sensor_info import SensorInfo, get_sensor_by_name

import logging

_logger = logging.getLogger(__name__)

    
@dataclass
class AudioMeasurement:
    received_time: datetime
    sensor_id: str
    hz: int
    dbfs: float

    def insert(self, conn: psycopg.Connection) -> None:
        sql = """INSERT INTO app.audio_sensor
            (
                received_time, 
                sensor_id,
                hz, 
                dbfs
            )
        VALUES (%s, %s, %s, %s)"""
        with conn.cursor() as cur:
            cur.execute(sql, (
                self.received_time,
                self.sensor_id,
                self.hz,
                self.dbfs
            ))
            conn.commit()
    

async def get_sensor_data_by_range(
    sensor: str | SensorInfo,
    start: datetime,
    stop: datetime,
    hz: int,
    conn: psycopg.AsyncConnection
) -> list[AudioMeasurement]:

    if isinstance(sensor, str):
        sensor = get_sensor_by_name(sensor)

    sql = """SELECT
        received_time, 
        sensor_id,
        hz, 
        dbfs
    FROM app.audio_sensor
    WHERE hz = %s
    AND sensor_id = %s
    AND received_time > %s 
    AND received_time < %s  
    ORDER BY received_time
    """

    datapoints = []
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, (hz, sensor.sensor_id, start, stop))
            row = await cur.fetchone()

            if row is None:
                return None

            datapoint = AudioMeasurement(
                received_time = row['received_time'], 
                sensor_id = row['sensor_id'],
                hz = row['hz'], 
                dbfs = row['dbfs']
            )
        datapoints.append(datapoint)
    except Exception as e:
        _logger.error(f"Error getting closest audio measurements: {e}")
        return None
    
    return datapoints


