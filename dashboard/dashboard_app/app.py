from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
import datetime
import logging

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
    get_datacenter_by_name,
    get_datacenters,
    get_datacenter_by_id
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

_logger = logging.getLogger(__name__)

@get("/health")
async def health_check() -> dict[str,str]:
    return {"status": "ok"}

@get("/")
async def dashboard() -> Template:  # noqa: UP006
    context = {}
    return Template(template_name="pages/dashboard.html", context = context)


@get("/datacenter/nearest")
async def get_nearest_datacenter_endpoint(
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

@get("/datacenter/nearest/map")
async def get_nearest_datacenter_map() -> Template:
    async with pool.connection() as conn:
        default_lat = 38.894509
        default_long = -104.858705
        datacenter: DatacenterInfo = await get_clostest_datacenter(
            default_lat,
            default_long,
            conn
        )
        sensors: list[SensorInfo] = await get_sensors_by_datacenter(
            datacenter, 
            conn
        )

    map = Template(        
        template_name="components/dashboard/map.html",
        context={"datacenter": datacenter, "sensors": sensors}
    )
    
    return map


@get("/datacenters")
async def get_datacenters_endpoint(
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


@get("/sensors/by-datacenter/{datacenter_id:str}")
async def get_datacenter_available_sensors(
    datacenter_id: str,
) -> Template:
    async with pool.connection() as conn:
        datacenter: DatacenterInfo = await get_datacenter_by_id(datacenter_id, conn)
        sensors: list[SensorInfo] = await get_sensors_by_datacenter(datacenter, conn)
        _logger.info(f"Got Datacenter Sensors: {sensors}")
    return Template(
        template_name="components/dashboard/sensor_charts.html",
        context={"sensors": sensors},
    )

@get("/sensors/nearest-datacenter")
async def get_sensors_for_nearest_datacenter() -> Template:
    async with pool.connection() as conn:
        default_lat = 38.894509
        default_long = -104.858705
        datacenter: DatacenterInfo = await get_clostest_datacenter(
            default_lat,
            default_long,
            conn
        )
        sensors: list[SensorInfo] = await get_sensors_by_datacenter(datacenter, conn)
        _logger.info(f"Got Nearby Sensors: {sensors}")

    return Template(
        template_name="components/dashboard/sensor_charts.html",
        context={"sensors": sensors},
    )

@get("/sensors/data/latest/{datacenter_id:str}")
async def get_latest_datacenter_sensors_data(
    datacenter_id:str
) -> list[SensorData]:
    # will return a lot of data
    # 1. Sensor assocaited with the datacenter
    # 2. Available frequencies
    # 3. actual datapoints per frequency over time
    async with pool.connection() as conn:
        datacenter: DatacenterInfo = await get_datacenter_by_id(datacenter_id, conn)
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
) -> Template:
    # 1. Available frequencies
    # 2. actual datapoints per frequency over time
    async with pool.connection() as conn:
        sensor: SensorInfo = await get_sensor_by_name(sensor_id, conn)
        _logger.debug(f"Getting Info For Sensor: {sensor_id}")

        # start with all time data
        sensor_datasets: list[dict] = []
        start = datetime.datetime(1990, 1, 1, 0, 0, 0, 0, None)
        stop = datetime.datetime.now()
        selected_frequencies = get_default_frequency_ranges()
        for hz in selected_frequencies:
            _logger.debug(f"Getting sensor data for: {sensor_id} at {hz} hz")
            measurements: list[AudioMeasurement] = await get_sensor_data_by_range(
                sensor,
                start,
                stop,
                hz,
                conn
            )
            _logger.debug(f"Got measurements:\n{measurements}")
            if measurements == [] or measurements == None:
                _logger.warning(f"No sensor info for {sensor.sensor_id}")
                continue
            sensor_datasets.append({
                "label": f"{hz} Hz",
                "timestamps": [m.received_time.isoformat() for m in measurements],
                "values": [m.dbfs for m in measurements],
            })

    template = Template(
        template_name = "components/dashboard/sensor_chart_content.html",
        context = {"sensor": sensor, "series": sensor_datasets}
    )
    return template


@get("/sensor/{sensor_id:str}/data/latest")
async def get_latest_sensor_data(
    sensor_id: str,
) -> list[dict]:
    # 1. Available frequencies
    # 2. actual datapoints per frequency over time
    async with pool.connection() as conn:
        sensor: SensorInfo = await get_sensor_by_name(sensor_id, conn)
        _logger.debug(f"Getting latest info for sensor: {sensor_id}")

        # start with all time data
        sensor_datasets: list[dict] = []
        start = datetime.datetime.now() - datetime.timedelta(seconds=60)
        stop = datetime.datetime.now(datetime.timezone.utc)
        selected_frequencies = get_default_frequency_ranges()
        for hz in selected_frequencies:
            _logger.debug(f"Getting latest sensor data for: {sensor_id} at {hz} hz")
            measurements: list[AudioMeasurement] = await get_sensor_data_by_range(
                sensor,
                start,
                stop,
                hz,
                conn
            )
            _logger.debug(f"Got measurements:\n{measurements}")
            if measurements == [] or measurements == None:
                _logger.warning(f"No sensor info for {sensor.sensor_id}")
                continue
            sensor_datasets.append({
                "label": f"{hz} Hz",
                "timestamps": [m.received_time.isoformat() for m in measurements],
                "values": [m.dbfs for m in measurements],
            })

    return sensor_datasets


app = Litestar(
    route_handlers=[
        health_check, 
        dashboard, 
        get_nearest_datacenter_map,
        get_nearest_datacenter_endpoint,
        get_datacenters_endpoint,
        get_datacenter_sensors_data,
        get_latest_datacenter_sensors_data,
        get_sensor_data,
        get_latest_sensor_data,
        get_datacenter_available_sensors,
        get_sensors_for_nearest_datacenter,
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