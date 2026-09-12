# LSL_ScienceMode4

A bridge between [Hasomed ScienceMode 4](https://science.hasomed.de/) stimulation/measurement devices and [Lab Streaming Layer (LSL)](https://labstreaminglayer.org/), allowing experiment-control software such as [PsychoPy](https://www.psychopy.org/) to trigger electrical stimulation and receive measurement data over the network in real time.

It wraps the [`science_mode_4`](https://pypi.org/project/science-mode-4/) Python package to talk to a P24 (stimulator) or I24 (Dyscom measurement) device over a serial port, and exposes that device to the outside world purely through two LSL streams. Any LSL-aware application can therefore drive the device and consume its data without needing to know anything about the ScienceMode protocol itself.

## What it does

The core script, [science_mode_lsl.py](science_mode_lsl.py), runs an asyncio event loop that:

1. Connects to a ScienceMode device (P24 or I24) over a serial ("COM") port. If no port is given, it auto-detects the first available ScienceMode device.
2. Resolves an **input** LSL stream (default name `ScienceMode-Control`) used to receive text commands.
3. Creates an **output** LSL stream (default name `ScienceMode-Measurement-Data`) used to publish measurement samples coming from the device.
4. Loops continuously: pulling commands from the control stream and forwarding them to the device, while pushing any measurement data produced by the device onto the measurement stream.

Device-specific behavior lives in small wrapper classes:

- [sm4_device.py](sm4_device.py) — `ScienceModeDevice`, the common base class. Handles the serial connection and the generic `START` / `STOP` commands.
- [p24_device.py](p24_device.py) — `P24Device`, for stimulation. Adds `STIM_1` and `STIM_2` commands that send two example stimulation channel configurations (pulse patterns) to the device, and reports back stimulation measurement samples.
- [i24_device.py](i24_device.py) — `I24Device`, for Dyscom measurement. Starts an EMG measurement on `START` and streams live samples pulled from the device's packet buffer.

Each device class implements `handle_command()` (to react to an incoming LSL control message), `get_measurement_data()` (to produce outgoing samples), and `get_available_commands()` (to advertise which commands it understands).

### Command-line arguments

| Argument | Description | Default |
|---|---|---|
| `--sciencemode_device` | Device type: `P24` or `I24` | `P24` |
| `--sciencemode_device_port` | Serial port of the device (e.g. `COM3`); auto-detected if omitted | `None` |
| `--lsl_control_stream_name` | Name of the LSL stream to read commands from | `ScienceMode-Control` |
| `--lsl_measurement_stream_name` | Name of the LSL stream to publish measurement data to | `ScienceMode-Measurement-Data` |

Example:

```bash
python science_mode_lsl.py --sciencemode_device P24 --sciencemode_device_port COM3
```

## Interfacing with PsychoPy

PsychoPy is not aware of the ScienceMode device or protocol at all — it only ever talks LSL, using the [`pylsl`](https://pypi.org/project/pylsl/) package (bundled with recent PsychoPy versions, or installable separately). The included [psychopy_example.psyexp](psychopy_example.psyexp) experiment shows the pattern:

1. A PsychoPy Code Component creates a `StreamOutlet` once at the start of the experiment:

   ```python
   from pylsl import StreamInfo, StreamOutlet

   info = StreamInfo(
       name='ScienceMode-Control',
       type='Markers',
       channel_count=1,
       nominal_srate=0,          # irregular rate, markers arrive sporadically
       channel_format='string',
       source_id='psychopy_marker_stream_001'
   )
   outlet = StreamOutlet(info)
   ```

   The stream name (`ScienceMode-Control`) must match the `--lsl_control_stream_name` argument passed to `science_mode_lsl.py` so that the script's `resolve_byprop` call finds it.

2. At the appropriate points in the experiment timeline (routine start/end, button presses, etc.), the Code Component pushes single-word string commands onto that outlet, e.g.:

   ```python
   outlet.push_sample(['START'])
   ...
   outlet.push_sample(['STOP'])
   outlet.push_sample(['STIM_1'])   # P24 only
   outlet.push_sample(['STIM_2'])   # P24 only
   ```

   `science_mode_lsl.py` pulls these samples from its `StreamInlet` and forwards them to `device.handle_command()`, which starts/stops the measurement or triggers a stimulation pattern accordingly.

3. Optionally, a PsychoPy component can create a matching `StreamInlet` for `ScienceMode-Measurement-Data` to record incoming stimulation/measurement samples alongside the rest of the experiment data.

Because the coupling is entirely through LSL, PsychoPy and `science_mode_lsl.py` can run as separate processes — even on separate machines on the same network — and any other LSL-capable tool (e.g. LabRecorder, or a custom LSL client) can observe the same streams for synchronized recording.

## Setup

```bash
pip install -r requirements.txt
```

Dependencies: [`pylsl`](https://pypi.org/project/pylsl/) and [`science_mode_4`](https://pypi.org/project/science-mode-4/).


## PsychoPy example
- see file psychopy_example.psyexp
