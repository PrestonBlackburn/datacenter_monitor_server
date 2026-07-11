# Create a private channel for both nodes
from typing import Optional
import secrets
import meshtastic.serial_interface
from typing import Any, Optional
from pathlib import Path
from meshtastic.protobuf import channel_pb2

PSK_PATH = Path("test_psk.bin")
def setup_test_channel(device_name: str, channel_index: int = 1) -> Optional[bytes]:

    if PSK_PATH.is_file():
        psk = PSK_PATH.read_bytes()
        print(f"Loaded existing PSK from {PSK_PATH}")
    else:
        psk = secrets.token_bytes(32)
        PSK_PATH.write_bytes(psk)
        print(f"Generated new PSK, saved to {PSK_PATH}")

    try:
        with meshtastic.serial_interface.SerialInterface(device_name) as iface:
            # Get the slot directly from the node's channel list
            ch = iface.localNode.getChannelByChannelIndex(channel_index)
            print(ch)
            if ch is None:
                print(f"Channel index {channel_index} not available on {device_name}")
                return None

            # Mutate the protobuf in place
            channel_name = "testPrivate"
            ch.settings.name = channel_name
            ch.settings.psk = psk
            ch.role = channel_pb2.Channel.Role.SECONDARY
            ch.settings.uplink_enabled = True
            ch.settings.downlink_enabled = True
            ch.role = channel_pb2.Channel.Role.SECONDARY

            # duble check pk
            print(f"DEBUG: PSK bytes: {len(psk)} | Hex: {psk.hex()}")
            # Flush to device flash
            iface.localNode.writeChannel(channel_index)

            print(f"{device_name}: test channel written to slot {channel_index}")
            return psk

    except Exception as exc:
        print(f"Error setting up channel on {device_name}: {exc}")
        return None


def get_channel(device_name: str, channel_index: int = 1) -> None:
    with meshtastic.serial_interface.SerialInterface(device_name) as iface:
        # Get the slot directly from the node's channel list
        ch = iface.localNode.getChannelByChannelIndex(channel_index)
        print(ch)
        if ch is None:
            print(f"Channel index {channel_index} not available on {device_name}")
            return None
        

if __name__ == "__main__":
    device_a = "/dev/ttyACM0"
    device_b = "/dev/ttyUSB1"
    INDEX = 1

    setup_test_channel(device_a, channel_index=INDEX)
    setup_test_channel(device_b, channel_index=INDEX)

    get_channel(device_a, channel_index=INDEX)
    get_channel(device_b, channel_index=INDEX)