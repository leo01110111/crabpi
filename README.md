Personal OpenClaw Assistant on the Raspberry Pi with face recognition and cute eyes.

## Setup

### 1. Create a conda environment

```bash
conda create -n crabpi python=3.11 -y
conda activate crabpi
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

On the Raspberry Pi, install the GPIO library if needed (for eye hardware):

```bash
pip install RPi.GPIO
# or: sudo apt install python3-rpi.gpio
```

## Scripts

### Face position notifier

Prints face position to the terminal (no hardware). Useful for testing the camera and detection.

```bash
python face_position_notifier.py
```

Runs without a GUI by default. Output: `face at left`, `face at center`, `face at right`, or `no face`. **Ctrl+C** to stop.

With camera preview: `python face_position_notifier.py --window` (press **q** to quit).

### Eye control (library)

`eye_control.py` provides the `EyeControl` class for driving two 7-segment “eyes” via shift registers. Instantiate with your GPIO pins (BCM), then call `look_forward()`, `look_left()`, `look_right()`, `look_closed()`, or `look_off()`.

```python
from eye_control import EyeControl

eyes = EyeControl(data_pin=17, latch_pin=27, clock_pin=22)
eyes.look_forward()
eyes.look_left()
eyes.close()
```

### Eye follower

Runs the camera and drives the eyes from face position: eyes look left/right/forward, blink periodically, and turn off after no face for a while.

```bash
python eye_follower.py
```

Uses BCM pins **17** (data), **27** (latch), **22** (clock) by default. Edit the `EyeControl(...)` call in `eye_follower.py` to match your wiring.

No GUI by default; **Ctrl+C** to stop. With preview: `python eye_follower.py --window`. Add `--debug` to print face state to the terminal.
