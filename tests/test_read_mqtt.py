import base64
import json
import signal
import sys
import struct

import paho.mqtt.client as mqtt

# Device Message Info
MSG_VERSION = 1
MSG_TYPE = 1
NUM_BANDS = 4
EXPECTED_LEN = 3 + NUM_BANDS * 2

def format_bytes(raw: bytes) -> str:
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

def handle_uplink(payload:dict):
    device_info = payload.get("deviceInfo", {})
    dev_eui = device_info.get("devEui", "unknown")
    device_name = device_info.get("deviceName", "unknown")
    f_port = payload.get("fPort")
    f_cnt = payload.get("fCnt")
    time = payload.get("time")

    data_b64 = payload.get("data")
    if data_b64 is None:
        raise ValueError("message has no 'data' field")
    
    raw = base64.b64decode(data_b64)

    rx_info = payload.get("rxInfo") or [{}]
    rssi = rx_info[0].get("rssi")
    snr = rx_info[0].get("snr")

    print(f"[{time}] {device_name} ({dev_eui})  fPort={f_port} fCnt={f_cnt}  rssi={rssi} snr={snr}")
    print(format_bytes(raw))
    print("-" * 60)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print(f"Failed to connect: {reason_code}", file=sys.stderr)
        return
    print(f"Connected. Subscribing to '{userdata['topic']}' ...")
    client.subscribe(userdata["topic"], qos=userdata["qos"])

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"[PARSE ERROR] topic={msg.topic} could not decode JSON: {e}", file=sys.stderr)
        print(f"    raw payload: {msg.payload!r}", file=sys.stderr)
        return
    try:
        handle_uplink(payload)
    except (KeyError, ValueError, TypeError, base64.binascii.Error) as e:
        # This is the same failure mode your errors table is meant to catch -
        # log it here rather than crashing the subscriber.
        print(f"[UPLINK ERROR] topic={msg.topic}: {e}", file=sys.stderr)
        print(f"    payload: {json.dumps(payload)}", file=sys.stderr)


def main():
    TOPIC_FILTER = "application/+/device/+/event/up"
    QOS = 0
    MQTT_BROKER_HOST = "localhost"
    PORT = 1883
    

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        userdata={"topic": TOPIC_FILTER, "qos": QOS},
    )
    client.on_connect = on_connect
    client.on_message = on_message
 
    client.connect(MQTT_BROKER_HOST, PORT, keepalive=30)
 
    def shutdown(sig, frame):
        print("\nShutting down...")
        client.disconnect()
        sys.exit(0)
 
    signal.signal(signal.SIGINT, shutdown)
 
    client.loop_forever()
 
 
if __name__ == "__main__":
    main()
