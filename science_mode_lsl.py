"""
Example 
"""

import asyncio
import argparse

from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop
from sm4_device import ScienceModeDevice
from p24_device import P24Device
from i24_device import I24Device



async def main() -> None:
    """Main function"""
    parser = argparse.ArgumentParser(description='Example using ScienceMode device with a LSL software')
    parser.add_argument('--sciencemode_device', help='ScienceMode device type (P24/I24)',
                        default="P24")
    parser.add_argument('--sciencemode_device_port', help='ScienceMode device port ("COM*")',
                        default=None)
    parser.add_argument('--lsl_control_stream_name', help='LSL control stream name',
                        default="ScienceMode-Control")
    parser.add_argument('--lsl_measurement_stream_name', help='LSL measurement stream name',
                        default="ScienceMode-Measurement-Data")
    args = parser.parse_args()

    print("Command line parameters:")
    for key, value in vars(args).items():
        print(f"{key}: {value}")

    # Find input LSL control stream
    print(f"Looking for LSL stream '{args.lsl_control_stream_name}' ...")
    while True:
        streams = resolve_byprop("name", args.lsl_control_stream_name, timeout=1)
        if streams:
            break
        await asyncio.sleep(5)

    print("Control stream found.")
    inlet = StreamInlet(streams[0])

    # Create output LSL measurement stream
    info = StreamInfo(
        name=args.lsl_measurement_stream_name,
        type="Current",
        channel_count=1,
        nominal_srate=0,              # irregular: pulses aren't clocked at a fixed rate
        channel_format="float32",
        source_id="ScienceMode-measurement",
    )
    outlet = StreamOutlet(info)

    # create ScienceMode device object
    device: ScienceModeDevice = None
    if args.sciencemode_device == "P24":
        device = P24Device(args.sciencemode_device_port)
    elif args.sciencemode_device == "I24":
        device = I24Device(args.sciencemode_device_port)
    else:
        print(f"ScienceMode device {args.sciencemode_device} not supported")
        return

    print(f"Available device commands: {device.get_available_commands()}")
    await device.connect()

    # loop until an stop command arrives
    while True:
        # read value from LSL control stream
        value = inlet.pull_sample(timeout=0)

        if value[0] is not None:
            command = value[0][0]
            ret = await device.handle_command(command)
            if ret:
                break

        # read measurement data from device and send it via lsl measurement stream
        data = await device.get_measurement_data()
        if data is not None:
            outlet.push_chunk(data)
            await asyncio.sleep(0)
        else:
            await asyncio.sleep(0.01)

    await device.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
