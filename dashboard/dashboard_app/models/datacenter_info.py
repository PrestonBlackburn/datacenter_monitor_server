# Source SQL - 
# create table if not exists app.datacenter_info (
#     datacenter_id   text not null,
#     created_time    timestamptz not null,
#     updated_time    timestamptz not null,
#     lat             DOUBLE PRECISION,
#     long            DOUBLE PRECISION,
#     name            text,
#     status          text,
#     description     text
# );

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import math
import logging

import psycopg

_logger = logging.getLogger(__name__)

@dataclass
class DatacenterInfo:
    datacenter_id: str
    created_time: datetime
    updated_time: datetime
    lat: Optional[float] = None
    long: Optional[float] = None
    name: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None

    async def insert(self, conn: psycopg.AsyncConnection) -> None:
        sql = """INSERT INTO app.datacenter_info
            (
                datacenter_id,
                created_time,
                updated_time,
                lat,
                long,
                name,
                status,
                description
            )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        async with conn.cursor() as cur:
            await cur.execute(sql, (
                self.datacenter_id,
                self.created_time,
                self.updated_time,
                self.lat,
                self.long,
                self.name,
                self.status,
                self.description
            ))
            await conn.commit()

async def get_clostest_datacenter(
        lat: float,
        long: float,
        conn: psycopg.AsyncConnection
) -> DatacenterInfo | None:
    sql = """SELECT
        datacenter_id,
        created_time, 
        updated_time, 
        lat, 
        long,
        name,
        status, 
        description
    FROM app.datacenter_info
    WHERE lat is not null and long is not null
    ORDER BY (lat - %s)^2 + (long - %s)^2
    LIMIT 1
    """
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, (lat, long))
            row = await cur.fetchone()

            if row is None:
                return None

            datacenter_info = DatacenterInfo(
                datacenter_id = row['datacenter_id'],
                created_time = row['created_time'],
                updated_time = row['updated_time'],
                lat = row['lat'],
                long = row['long'],
                name=row["name"],
                status=row["status"],
                description=row["description"]
            )
    except Exception as e:
        _logger.error(f"Error getting closest datacetner: {e}")
        return None
    
    return datacenter_info

async def get_datacenters_in_range(
        lat: float,
        long: float,
        conn: psycopg.AsyncConnection,
        max_distance_mi: float = 10.0
) -> list[DatacenterInfo]:
    sql = """SELECT
        datacenter_id,
        created_time, 
        updated_time, 
        lat, 
        long,
        name,
        status, 
        description
    FROM app.datacenter_info
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
    datacenters_in_range = []
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
                datacenter_info = DatacenterInfo(
                    datacenter_id = row['datacenter_id'],
                    created_time = row['created_time'],
                    updated_time = row['updated_time'],
                    lat = row['lat'],
                    long = row['long'],
                    name=row["name"],
                    status=row["status"],
                    description=row["description"]
                )
                datacenters_in_range.append(datacenter_info)
    except Exception as e:
        _logger.error(f"Error getting closest datacetner: {e}")
    
    return datacenters_in_range
    

def get_datacenters(
        conn: psycopg.Connection
) -> list[DatacenterInfo]:
    sql = """SELECT
        datacenter_id,
        created_time, 
        updated_time, 
        lat, 
        long,
        name,
        status, 
        description
    FROM app.datacenter_info
    """
    datacenters = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            rows = cur.fetchall()

            for row in rows:
                datacenter_info = DatacenterInfo(
                    datacenter_id = row['datacenter_id'],
                    created_time = row['created_time'],
                    updated_time = row['updated_time'],
                    lat = row['lat'],
                    long = row['long'],
                    name=row["name"],
                    status=row["status"],
                    description=row["description"]
                )
                datacenters.append(datacenter_info)
    except Exception as e:
        _logger.error(f"Error getting closest datacetner: {e}")
    
    return datacenters
    
    
def get_datacenter_by_name(
        datacenter_name:str, 
        conn: psycopg.Connection
    ) -> DatacenterInfo: 
    # in the case there are two we'll raise a warning and choose one
    sql = """SELECT
        datacenter_id,
        created_time, 
        updated_time, 
        lat, 
        long,
        name,
        status, 
        description
    FROM app.datacenter_info
    WHERE name ilike %s
    """
    datacenters = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (datacenter_name,))
            conn.commit()
            rows = cur.fetchall()

            for row in rows:
                datacenter_info = DatacenterInfo(
                    datacenter_id = row['datacenter_id'],
                    created_time = row['created_time'],
                    updated_time = row['updated_time'],
                    lat = row['lat'],
                    long = row['long'],
                    name=row["name"],
                    status=row["status"],
                    description=row["description"]
                )
                datacenters.append(datacenter_info)
    except Exception as e:
        _logger.error(f"Error getting closest datacetner: {e}")

    if len(datacenters) > 1:
        _logger.warning(f"multiple datacenters found: {[datacenter.name for datacenter in datacenters]}. \nUsing: {datacenters[0].name}")
    
    datacenter = datacenters[0]
    
    return datacenter