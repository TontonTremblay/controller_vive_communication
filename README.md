# HTC Vive Controller Tracker

A Python application for tracking and streaming HTC Vive controller data over a network. This project allows you to track the position, rotation, and button states of HTC Vive controllers and send the data to another computer (e.g., from Windows to Linux) in real-time.

## Features

- Real-time tracking of HTC Vive controllers
- Displays position (X, Y, Z) and rotation (roll, pitch, yaw) data
- Shows the status of all controller buttons
- Streams controller data over UDP to another computer
- Low-latency data transmission suitable for real-time applications
- Cross-platform compatibility (sender on Windows, receiver on any platform)
- 3D visualization of controller positions and movements
- Motion trails to track controller movement paths
- Visual feedback when controller triggers are pressed

## Requirements

### Sender (Windows with HTC Vive)
- Python 3.6+
- SteamVR installed and running
- HTC Vive headset and controllers
- OpenVR Python package
- NumPy

### Receiver/Visualizer (Any platform)
- Python 3.6+
- Matplotlib (for 3D visualization)
- NumPy

## Installation

1. Clone this repository:
   ```
   git clone git@github.com:TontonTremblay/controller_vive_communication.git
   cd controller_vive_communication
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Sender (Windows with HTC Vive)

1. Make sure SteamVR is running and your HTC Vive is properly set up
2. Run the sender script with the IP address of the receiver machine:
   ```
   python main.py --ip 192.168.1.X --port 5555
   ```
   Replace `192.168.1.X` with the actual IP address of your receiver machine.

3. To generate a receiver script for the other machine:
   ```
   python main.py --create-receiver
   ```
   This will create `vive_receiver.py` which you can transfer to the receiver machine.

### Receiver (Any platform)

1. Copy the `vive_receiver.py` script to your machine
2. Run the receiver script:
   ```
   python vive_receiver.py
   ```

3. Optional arguments:
   ```
   python vive_receiver.py --port 5555 --mode full
   ```
   - `--port`: UDP port to listen on (default: 5555)
   - `--mode`: Display mode - simple, full, or raw (default: simple)

### Visualizer (Any platform)

1. Run the visualizer script:
   ```
   python vive_matplotlib_visualizer.py
   ```

2. Optional arguments:
   ```
   python vive_matplotlib_visualizer.py --port 5555 --trail-length 100
   ```
   - `--port`: UDP port to listen on (default: 5555)
   - `--trail-length`: Number of points to keep in the motion trail (default: 50)

## Visualization Features

The matplotlib-based visualizer provides:

- 3D view of controller positions in real-time
- Color-coded controllers (blue for left, red for right)
- Controllers turn green when triggers are pressed
- Motion trails showing the path of each controller
- Coordinate frames showing controller orientation
- Ground plane grid for spatial reference

## Display Modes (Text Receiver)

- **simple**: Shows essential information (position and main button states)
- **full**: Shows all available data (position, rotation, all buttons, analog inputs)
- **raw**: Displays the raw JSON data for debugging or custom processing

## Data Format

The controller data is sent as JSON with the following structure:

```json
{
  "left": {
    "tracked": true,
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "rotation": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
    "buttons": {
      "system": false,
      "menu": false,
      "grip": false,
      "trigger": false,
      "trackpad": {"pressed": false, "touched": false},
      ...
    },
    "analog": {
      "trigger": 0.0,
      "trackpad": {"x": 0.0, "y": 0.0}
    }
  },
  "right": {
    ...
  },
  "timestamp": 1234567890.123
}
```

## Handling Controller Sleep

The system automatically handles controller sleep/wake cycles:
- When controllers go to sleep to save battery, they are marked as disconnected
- When they wake up (by pressing any button), they are automatically reconnected
- No need to restart the application when controllers go to sleep

## License

MIT License

## Acknowledgments

- This project uses the OpenVR API to interface with SteamVR
- Thanks to Valve for providing the OpenVR SDK 