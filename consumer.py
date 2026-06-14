import meshtastic.serial_interface
from pubsub import pub
from datetime import datetime
from typing import Any, Optional
import time
import logging
from dataclasses import dataclass, field
import json
import psycopg
import os

TEST_CHANNEL_INDEX = 1
_TZ_NAME = time.tzname[time.localtime().tm_isdst > 0]
CONSUMER_DEVICE = "/dev/ttyUSB0" #heltec
PRODUCER_DEVICE = '/dev/ttyACM0'

# logging.getLogger("meshtastic").setLevel(logging.CRITICAL)
time.sleep(2)

@dataclass
class AudioMeasurement:
    created_time: datetime = field(default_factory=lambda: None)
    hz_110_dbfs: float = field(default_factory=lambda: None)
    hz_440_dbfs: float = field(default_factory=lambda: None)
    hz_1000_dbfs: float = field(default_factory=lambda: None)
    hz_4000_dbfs: float = field(default_factory=lambda: None)
    recieved_time: datetime = field(default_factory=lambda: datetime.now())
    device_model: str = field(default_factory=lambda: "SPH0645LM4H")

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


def save_measurement(audio_measurement: AudioMeasurement) -> None:
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
    return None

def test_channels(device_name: str):
    with meshtastic.serial_interface.SerialInterface(device_name) as iface:
        channels = iface.localNode.showChannels()
        print(channels)

def on_receive(packet: dict[str, Any], interface: Any) -> None:  # pylint: disable=unused-argument
    """Print a compact line for each received text packet on channel 1."""
    
    # 1. Check if the channel matches (Index 1)
    # The packet 'channel' field represents the channel index
    channel_index = packet.get("channel", 0)
    if channel_index != 1:
        return  # Ignore traffic on all other channels (including Primary 0)

    # 2. Decode the packet
    decoded = packet.get("decoded", {})
    if decoded.get("portnum") != "TEXT_MESSAGE_APP":
        return

    message = decoded.get("text")
    if not message:
        return

    # 3. Print the message
    sender_id = packet.get("fromId", "unknown")
    message_time = datetime.now().strftime(f"%a %b %d %Y %H:%M:%S {_TZ_NAME}")
    print(f"{message_time} : Channel {channel_index} : {sender_id} : {message}")

    try:
        print("processing message")
        message_formatted = json.loads(message)
        records = zip(message_formatted[0], message_formatted[1], message_formatted[2])
        received_date_format = "%Y-%m-%d %H:%M"
        measurement = AudioMeasurement(created_time = datetime.strptime(records[0][0], received_date_format))
        for record in records:
            match record[1]:
                case 110:
                    measurement.hz_110_dbfs = record[2]
                case 440:
                    measurement.hz_440_dbfs = record[2]
                case 1000:
                    measurement.hz_1000_dbfs = record[2]
                case 4000:
                    measurement.hz_4000_dbfs = record[2]
    except Exception as e: 
        print(f"Message formatting error: {e}\n got:\n{message}")

    try:
        save_measurement(measurement)
    except Exception as e: 
        print(f"Error writing to postgres: {e}\ndata: {measurement}")
    return None

def listen_for_messages(device_name:str, channel_index:int = TEST_CHANNEL_INDEX) -> int:
    """Connect over serial and print inbound text messages."""

    pub.subscribe(on_receive, "meshtastic.receive")

    iface: Optional[meshtastic.serial_interface.SerialInterface] = None
    try:
        iface = meshtastic.serial_interface.SerialInterface(device_name)
        print("Connected. Listening for text messages. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(f"Error: Could not monitor serial messages: {exc}")
        return 1
    finally:
        if iface:
            iface.close()
    return 0


if __name__ == "__main__":
    logging.getLogger("meshtastic").setLevel(logging.CRITICAL)

    # startup test -
    with meshtastic.serial_interface.SerialInterface(CONSUMER_DEVICE) as iface:
        for node_id, node in iface.nodes.items():
            if "02e4" in node.get("user", {}).get("longName", "unknown"):
                print(f"SNR: {node.get('snr')}")
                print(f"RSSI: {node.get('lastHeard')}")
                print(f"hopsAway: {node.get('hopsAway')}")
                

    listen_for_messages(CONSUMER_DEVICE)