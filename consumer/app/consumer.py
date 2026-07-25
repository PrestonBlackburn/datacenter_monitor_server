import base64
import json
import signal
import sys
import struct
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
import re
import os
from functools import lru_cache

import paho.mqtt.client as mqtt
from psycopg.types.json import Jsonb
import psycopg


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
_logger = logging.getLogger("audio-sensor-consumer")
_conn: psycopg.Connection | None = None

@lru_cache(maxsize=1)
def get_env() -> dict:
    
    required = ["SENSOR_SVC_USER", "SENSOR_SVC_PASSWORD"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        _logger.error("Missing required env vars: %s", ", ".join(missing))
        sys.exit(1)

    # expected env vars
    env = {
        "topic_filter": os.getenv("TOPIC_FILTER", "application/+/device/+/event/up"),
        "topic_regex": re.compile(os.getenv("TOPIC_RE", r"^application/[^/]+/device/([0-9a-fA-F]+)/event/up$")),
        "qos": int(os.getenv("QOS", 0)),
        "mqtt_host": os.getenv("MQTT_BROKER_HOST", "localhost"),
        "mqtt_port": int(os.getenv("MQTT_BROKER_PORT", 1883)),
        "db": os.getenv("POSTGRES_DB", "sensors"),
        "db_host": os.getenv("POSTGRES_HOST", "localhost"),
        "db_port": int(os.getenv("POSTGRES_PORT", 5432)),
        "svc_pass": os.getenv("SENSOR_SVC_PASSWORD", "default"),
        "svc_user": os.getenv("SENSOR_SVC_USER", "sensor_svc"),
    }
    return env

def get_conn() -> psycopg.Connection:
    global _conn
    if _conn is not None and not _conn.closed:
        return _conn
    env = get_env()
    _conn = psycopg.connect(
        host = env['db_host'],
        port = env["db_port"],
        dbname = env["db"],
        user = env['svc_user'],
        password = env['svc_pass'],
        autocommit = False
    )
    _logger.info(f"Connected to TimescaleDB at {env['db_host']}:{env['db_port']}")
    return _conn

def invalidate_conn(conn: psycopg.Connection) -> None:
    # To handle failed inserts
    global _conn
    try:
        conn.rollback()
    except Exception:
        pass
    try:
        conn.close()
    except Exception:
        pass
    _conn = None


@dataclass
class AudioSensorMessage:
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

@dataclass
class AudioSensorError:
    created_time: datetime
    received_time: datetime
    sensor_id: str
    data_b64: str | None
    object: Jsonb

    def insert(self, conn: psycopg.Connection) -> None:
        sql = """INSERT INTO app.audio_sensor_errors
                (created_time, recieved_time, sensor_id, data_b64, object)
            VALUES (%s, %s, %s, %s, %s)"""
        with conn.cursor() as cur:
            cur.execute(sql, (
                self.created_time,
                self.received_time,
                self.sensor_id,
                self.data_b64,
                self.object
            ))
            conn.commit()


def decode_uplink(raw: bytes) -> str:
    # Device Message Info -> for now this won't change
    MSG_VERSION = 1
    MSG_TYPE = 1
    NUM_BANDS = 4
    EXPECTED_LEN = 3 + NUM_BANDS * 2

    if len(raw) < 3:
        raise ValueError(f"payload too short for header: {len(raw)} bytes")
    version, msg_type, declared_len = struct.unpack_from("<BBB", raw, 0)

    if version != MSG_VERSION:
        raise ValueError(f"unsupported message version: {version}")
    if msg_type != MSG_TYPE:
        raise ValueError(f"unsupported message type: {msg_type}")
    if declared_len != len(raw):
        raise ValueError(f"declared length {declared_len} != actual payload length {len(raw)}")
    if len(raw) != EXPECTED_LEN:
        raise ValueError(f"unexpected payload length: {len(raw)} (want {EXPECTED_LEN})")
    
    band_0, band_1, band_2, band_3 = struct.unpack_from("<4h", raw, 3)
    # band[0]=110Hz, band[1]=440Hz, band[2]=1000Hz, band[3]=4000Hz
    return {
        "hz_110_dbfs":  band_0 / 10.0,
        "hz_440_dbfs":  band_1 / 10.0,
        "hz_1000_dbfs": band_2 / 10.0,
        "hz_4000_dbfs": band_3 / 10.0,
    }

def parse_chirpstack_time(value) -> datetime:
    """Parse ChirpStack's RFC3339 'time' field; fall back to now() on failure."""
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def extract_dev_eui(topic: str, topic_re: re.Pattern) -> str:
    m = topic_re.match(topic)
    return m.group(1) if m else "unknown"

def create_record(payload:dict, received_time: datetime) -> list[AudioSensorMessage]:
    device_info = payload.get("deviceInfo", {})
    dev_eui = device_info.get("devEui", "unknown")
    device_name = device_info.get("deviceName", "unknown")
    f_port = payload.get("fPort")
    f_cnt = payload.get("fCnt")
    created_time = parse_chirpstack_time(payload.get("time"))

    data_b64 = payload.get("data")
    if data_b64 is None:
        raise ValueError("message has no 'data' field")
    
    raw = base64.b64decode(data_b64)


    rx_info = payload.get("rxInfo") or [{}]
    rssi = rx_info[0].get("rssi")
    snr = rx_info[0].get("snr")
    
    _logger.debug(f"[{received_time}] {device_name} ({dev_eui})  fPort={f_port} fCnt={f_cnt}  rssi={rssi} snr={snr}")
    _logger.debug(decode_uplink(raw))

    decoded = decode_uplink(raw)
    _logger.debug(f"decoded message: {decoded}")
    
    audio_messages = [
        AudioSensorMessage(
            received_time = received_time,
            sensor_id = dev_eui,
            hz = 4000,
            dbfs = decoded["hz_4000_dbfs"],
        ),
        AudioSensorMessage(
            eceived_time = received_time,
            sensor_id = dev_eui,
            hz = 1000,
            dbfs = decoded["hz_1000_dbfs"],
        ),
        AudioSensorMessage(
            eceived_time = received_time,
            sensor_id = dev_eui,
            hz = 440,
            dbfs = decoded["hz_440_dbfs"],
        ),
        AudioSensorMessage(
            eceived_time = received_time,
            sensor_id = dev_eui,
            hz = 110,
            dbfs = decoded["hz_110_dbfs"],
        )
    ]
    return audio_messages

def write_error(conn: psycopg.Connection | None, 
                payload_for_json, 
                sensor_id: str, 
                data_b64: bytes,
                received_time: datetime,
                created_time: datetime
                ):
    try:
        error_record = AudioSensorError(
                created_time = created_time,
                received_time = received_time,
                sensor_id = sensor_id,
                data_b64 = data_b64,
                object = Jsonb(payload_for_json)
            )
        error_record.insert(conn)
    except Exception as e:
        _logger.error("Error writing to error table: %s", e)
        invalidate_conn(conn)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print(f"Failed to connect: {reason_code}", file=sys.stderr)
        return
    print(f"Connected. Subscribing to '{userdata['topic']}' ...")
    client.subscribe(userdata["topic"], qos=userdata["qos"])

def on_message(client, userdata, msg):
    recieved_time = datetime.now(timezone.utc)
    topic_re = userdata["topic_regex"]

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        _logger.warning("[PARSE ERROR] topic=%s could not decode JSON: %s", msg.topic, e)
        try:
            conn = get_conn()
        except Exception as conn_err:
            _logger.error("Error connecting to database: %s", conn_err)
            return
        dev_eui = extract_dev_eui(msg.topic, topic_re)
        write_error(
            conn,
            {"raw": msg.payload.decode("utf-8", "replace")},
            dev_eui, None, recieved_time, recieved_time,
        )
        return

    try:
        conn = get_conn()
    except Exception as e:
        _logger.error("Error connecting to database: %s", e)
        return
 
    device_info = payload.get("deviceInfo", {})
    sensor_id = device_info.get("devEui", extract_dev_eui(msg.topic, topic_re))
    created_time = parse_chirpstack_time(payload.get("time"))

    try:
        # could update to insert many later
        records = create_record(payload, recieved_time)
        [record.insert(conn) for record in records]
        _logger.info("Inserted reading for %s", records[0].sensor_id)
    except (KeyError, ValueError, TypeError, base64.binascii.Error) as e:
        # This is the same failure mode your errors table is meant to catch -
        # log it here rather than crashing the subscriber.
        _logger.warning("[UPLINK ERROR] topic=%s: %s", msg.topic, e)
        invalidate_conn(conn)
        conn = get_conn()
        write_error(conn, payload, sensor_id, payload.get("data"), recieved_time, created_time)
    except psycopg.Error as e:
        _logger.error("[DB ERROR] insert failed for %s: %s", sensor_id, e)
        invalidate_conn(conn)


def main():
    env = get_env()    

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        userdata={
            "topic": env['topic_filter'], 
            "qos": env['qos'], 
            "topic_regex": env["topic_regex"],
        },
    )

    client.on_connect = on_connect
    client.on_message = on_message
 
    client.connect(env['mqtt_host'], env['mqtt_port'], keepalive=30)
 
    def shutdown(sig, frame):
        print("\nShutting down...")
        client.disconnect()
        if _conn is not None and not _conn.closed:
            _conn.close()
        sys.exit(0)
 
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
 
    client.loop_forever()
 
 
if __name__ == "__main__":
    main()
