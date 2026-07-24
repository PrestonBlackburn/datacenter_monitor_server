from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
import datetime

from litestar import Litestar, get, Router
from litestar.response import Template
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from litestar.static_files import StaticFilesConfig
from litestar.params import FromQuery
from litestar.di import Provide

from dashboard_app.models.datacenter_info import (
    DatacenterInfo, 
    get_clostest_datacenter,
    get_datacenter_by_name
)
from dashboard_app.models.sensor_info import (
    SensorInfo,
    get_sensors_by_datacenter,
    get_sensor_by_name,
)
from dashboard_app.models.sensor import (
    AudioMeasurement,
    get_sensor_data_by_range,
)
from dashboard_app.config import (
    get_default_frequency_ranges,
    open_pg_pool,
    close_pg_pool,
    pool
)


@get("/health")
async def health_check() -> dict[str,str]:
    return {"status": "ok"}

@get("/")
async def dashboard() -> Template:  # noqa: UP006
    context = {}
    return Template(template_name="pages/dashboard.html", context = context)

@get("/datacenter/nearest")
async def get_nearest_datacenter(
    lat: FromQuery[float],
    long: FromQuery[float]
) -> DatacenterInfo:
    async with pool.connection() as conn:
        datacenter: DatacenterInfo = await get_clostest_datacenter(
            lat,
            long,
            conn
        )
    return datacenter

@get("/datacenters")
async def get_datacenters(
) -> list[DatacenterInfo]:
    async with pool.connection() as conn:
        datacenters: list[DatacenterInfo] = await get_datacenters(conn)
    return datacenters

# helper class
@dataclass
class SensorData:
    sensor: SensorInfo
    frequency_hz: float
    data: list[AudioMeasurement]

@get("/sensors/data/all/{datacenter_id:str}")
async def get_datacenter_sensors_data(
    datacenter_id:str
) -> list[SensorData]:
    # will return a lot of data
    # 1. Sensor assocaited with the datacenter
    # 2. Available frequencies
    # 3. actual datapoints per frequency over time
    async with pool.connection() as conn:
        datacenter: DatacenterInfo = await get_datacenter_by_name(datacenter_id, conn)
        sensors: list[SensorInfo] = await get_sensors_by_datacenter(datacenter, conn)

        # start with all time data
        sensor_datasets: list[SensorData] = []
        start = datetime.datetime(1990, 1, 1, 0, 0, 0, 0, None)
        stop = datetime.datetime.now()
        selected_frequencies = get_default_frequency_ranges()
        for sensor in sensors:
            for hz in selected_frequencies:
                measurements: list[AudioMeasurement] = await get_sensor_data_by_range(
                    sensor,
                    start,
                    stop,
                    hz,
                    conn
                )
                sensor_datasets.append(
                    SensorData(
                        sensor = sensor,
                        frequency_hz=hz,
                        data = measurements
                    )
                )
    return sensor_datasets


@get("/sensors/data/latest/{datacenter_id:str}")
async def get_latest_datacenter_sensors_data(
    datacenter_id:str
) -> list[SensorData]:
    # will return a lot of data
    # 1. Sensor assocaited with the datacenter
    # 2. Available frequencies
    # 3. actual datapoints per frequency over time
    async with pool.connection() as conn:
        datacenter: DatacenterInfo = await get_datacenter_by_name(datacenter_id, conn)
        sensors: list[SensorInfo] = await get_sensors_by_datacenter(datacenter, conn)

        # start with all time data
        sensor_datasets: list[SensorData] = []
        start = datetime.datetime.now() - datetime.timedelta(seconds=60)
        stop = datetime.datetime.now()
        selected_frequencies = get_default_frequency_ranges()

        # possibly might want this async for
        for sensor in sensors:
            for hz in selected_frequencies:
                measurements: list[AudioMeasurement] = await get_sensor_data_by_range(
                    sensor,
                    start,
                    stop,
                    hz,
                    conn
                )
                sensor_datasets.append(
                    SensorData(
                        sensor = sensor,
                        frequency_hz=hz,
                        data = measurements
                    )
                )
        return sensor_datasets


@get("/sensor/{sensor_id:str}/data/all")
async def get_sensor_data(
    sensor_id: str,
) -> list[SensorData]:
    # 1. Available frequencies
    # 2. actual datapoints per frequency over time
    async with pool.connection() as conn:
        sensor: SensorInfo = await get_sensor_by_name(sensor_id, conn)

        # start with all time data
        sensor_datasets: list[SensorData] = []
        start = datetime.datetime(1990, 1, 1, 0, 0, 0, 0, None)
        stop = datetime.datetime.now()
        selected_frequencies = get_default_frequency_ranges()
        for hz in selected_frequencies:
            measurements: list[AudioMeasurement] = await get_sensor_data_by_range(
                sensor,
                start,
                stop,
                hz,
                conn
            )
            sensor_datasets.append(
                SensorData(
                    sensor = sensor,
                    frequency_hz=hz,
                    data = measurements
                )
            )
    return sensor_datasets


@get("/sensor/{sensor_id:str}/data/latest")
async def get_latest_sensor_data(
    sensor_id: str,
) -> list[SensorData]:
    # 1. Available frequencies
    # 2. actual datapoints per frequency over time
    async with pool.connection() as conn:
        sensor: SensorInfo = await get_sensor_by_name(sensor_id, conn)

        # start with all time data
        sensor_datasets: list[SensorData] = []
        start = datetime.datetime.now() - datetime.timedelta(seconds=60)
        stop = datetime.datetime.now()
        selected_frequencies = get_default_frequency_ranges()
        for hz in selected_frequencies:
            measurements: list[AudioMeasurement] = await get_sensor_data_by_range(
                sensor,
                start,
                stop,
                hz,
                conn
            )
            sensor_datasets.append(
                SensorData(
                    sensor = sensor,
                    frequency_hz=hz,
                    data = measurements
                )
            )
    return sensor_datasets



app = Litestar(
    route_handlers=[
        health_check, 
        dashboard, 
        get_nearest_datacenter,
        get_datacenters,
        get_datacenter_sensors_data,
        get_latest_datacenter_sensors_data,
        get_sensor_data,
        get_latest_sensor_data,
        ],
    template_config=TemplateConfig(
        directory=Path("dashboard_app/templates"),
        engine=JinjaTemplateEngine,
    ),
    static_files_config=[
        StaticFilesConfig(
            directories=["dashboard_app/static"],
            path="/static",
        )
    ],
    on_startup = [open_pg_pool],
    on_shutdown = [close_pg_pool]
)