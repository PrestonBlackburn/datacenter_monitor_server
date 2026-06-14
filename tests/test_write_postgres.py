from datetime import datetime
from typing import Any, Optional
import time
import logging
from dataclasses import dataclass, field
import json
import psycopg
import os


def get_db_conn_params() -> dict:

    conn_parameters = {
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
        "dbname": os.getenv("POSTGRES_DB"),
        "autocommit": True,
    }
    if conn_parameters['dbname'] is None:
        raise ValueError(f"Missing Env Vars For Database - Check Env Vars")
    
    return conn_parameters

@dataclass
class AudioMeasurement:
    created_time: datetime = field(default_factory=lambda: None)
    hz_110_dbfs: float = field(default_factory=lambda: None)
    hz_440_dbfs: float = field(default_factory=lambda: None)
    hz_1000_dbfs: float = field(default_factory=lambda: None)
    hz_4000_dbfs: float = field(default_factory=lambda: None)
    recieved_time: datetime = field(default_factory=lambda: datetime.now())
    device_model: str = field(default_factory=lambda: "SPH0645LM4H")


def get_test_measurement() -> AudioMeasurement:

    audio_measurement = AudioMeasurement(
        created_time = datetime.now(),
        hz_110_dbfs = -95.10393,
        hz_440_dbfs = -92.0123,
        hz_1000_dbfs = -94.2934,
        hz_4000_dbfs = -98.111
    )
    return audio_measurement


def test_write(audio_measurement: AudioMeasurement):
    conn_params = get_db_conn_params()
    with psycopg.connect(**conn_params) as conn:

        with conn.cursor() as cur:
            
            cur.execute(
                """INSERT INTO app.audio_sensor (
                created_time, recieved_time, device_model, hz_4000_dbfs, hz_1000_dbfs, hz_440_dbfs, hz_110_dbfs
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )""",
                (
                    audio_measurement.created_time,
                    audio_measurement.recieved_time,
                    audio_measurement.device_model,
                    audio_measurement.hz_4000_dbfs,
                    audio_measurement.hz_1000_dbfs,
                    audio_measurement.hz_440_dbfs,
                    audio_measurement.hz_110_dbfs
                )
            )
        conn.commit()

if __name__ == "__main__":

    meaure = get_test_measurement()
    test_write(meaure)
    