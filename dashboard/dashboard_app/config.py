# get pg env/session + env vars
from psycopg_pool import AsyncConnectionPool
import psycopg
import logging
from functools import lru_cache
import os

_logger = logging.getLogger(__name__)

def get_default_frequency_ranges() -> list:
    default_frequencies = [110, 440, 1000, 4000]
    return default_frequencies

@lru_cache(maxsize=1)
def get_env() -> dict:

    database = os.getenv("POSTGRES_DB", "sensors")
    password = os.getenv("SENSOR_SVC_PASSWORD", "default")
    user = os.getenv("SENSOR_SVC_USER", "sensor_svc")
    host = os.getenv("POSTGRES_HOST", "host.docker.internal")
    port = os.getenv("POSTGRES_PORT", "5432")

    env = {
        "dbname": database,
        "password": password,
        "user": user,
        "host": host,
        "port": port
    }

    return env

def conn_str() -> str:
    env = get_env()
    return (
        f"host={env['host']} port={env['port']} "
        f"dbname={env['dbname']} user={env['user']} password={env['password']}"
    )

pool = AsyncConnectionPool(
    conninfo = conn_str(),
    min_size=2,
    max_size=10,
    open=False
)

async def open_pg_pool():
    _logger.info("opening async pg connection pool")
    await pool.open()

async def close_pg_pool():
    _logger.info("closing async pg connection pool")
    await pool.close()
