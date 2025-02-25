#!/usr/bin/env python3
"""
Custom Receiver Example

This example shows how to receive HTC Vive controller data and use it in a custom application.
In this case, we're creating a simple visualization of the controller position.
"""

import socket
import json
import time
import argparse
import math
try:
    # Try to import matplotlib for visualization
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("Matplotlib not available. Running in text-only mode.")
    MATPLOTLIB_AVAILABLE = False

class ViveDataReceiver:
    def __init__(self, port=5555):
        """Initialize the receiver with the specified port"""
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", port))
        self.sock.setblocking(False)
        
        # Initialize data storage
        self.latest_data = None
        self.position_history = {
            "left": {"x": [], "y": [], "z": []},
            "right": {"x": [], "y": [], "z": []}
        }
        self.max_history = 100  # Maximum number of positions to store
        
        print(f"Listening for controller data on port {port}...")
    
    def update(self):
        """Check for new data and update the internal state"""
        try:
            # Try to receive data (non-blocking)
            data, addr = self.sock.recvfrom(4096)
            
            try:
                # Parse JSON data
                self.latest_data = json.loads(data.decode())
                
                # Update position history
                for hand in ["left", "right"]:
                    if hand in self.latest_data and self.latest_data[hand].get("tracked", False):
                        pos = self.latest_data[hand]["position"]
                        
                        # Add new position to history
                        self.position_history[hand]["x"].append(pos["x"])
                        self.position_history[hand]["y"].append(pos["y"])
                        self.position_history[hand]["z"].append(pos["z"])
                        
                        # Trim history if it gets too long
                        if len(self.position_history[hand]["x"]) > self.max_history:
                            self.position_history[hand]["x"] = self.position_history[hand]["x"][-self.max_history:]
                            self.position_history[hand]["y"] = self.position_history[hand]["y"][-self.max_history:]
                            self.position_history[hand]["z"] = self.position_history[hand]["z"][-self.max_history:]
                
                return True
            except json.JSONDecodeError:
                print(f"Received invalid data from {addr}")
        except BlockingIOError:
            # No data available
            pass
        
        return False
    
    def get_latest_data(self):
        """Return the latest controller data"""
        return self.latest_data
    
    def get_position_history(self):
        """Return the position history for both controllers"""
        return self.position_history
    
    def close(self):
        """Close the socket"""
        self.sock.close()

def text_mode(receiver):
    """Run in text-only mode, printing controller data to the console"""
    try:
        while True:
            if receiver.update():
                data = receiver.get_latest_data()
                
                # Clear terminal
                print("\033c", end="")
                
                # Print header
                print(f"=== HTC Vive Controller Data ===")
                print(f"Time: {time.strftime('%H:%M:%S')}")
                print("-------------------------------")
                
                # Display controller data
                for hand in ["left", "right"]:
                    if hand in data:
                        controller = data[hand]
                        if controller.get("tracked", False):
                            print(f"\n{hand.upper()} CONTROLLER:")
                            
                            # Position
                            pos = controller.get("position", {})
                            if pos:
                                print(f"  Position: X={pos.get('x', 0):.4f}, Y={pos.get('y', 0):.4f}, Z={pos.get('z', 0):.4f}")
                            
                            # Main buttons
                            buttons = controller.get("buttons", {})
                            if buttons:
                                print("\n  MAIN BUTTONS:")
                                for btn in ["trigger", "grip", "menu", "system"]:
                                    if btn in buttons:
                                        if isinstance(buttons[btn], dict):
                                            status = "PRESSED" if buttons[btn].get("pressed", False) else "---"
                                        else:
                                            status = "PRESSED" if buttons[btn] else "---"
                                        print(f"    {btn.capitalize()}: {status}")
                        else:
                            print(f"\n{hand.upper()} CONTROLLER: Not tracked")
            
            # Sleep to avoid high CPU usage
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nExiting...")

def plot_mode(receiver):
    """Run in plot mode, visualizing controller positions"""
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib is required for plot mode.")
        return
    
    # Set up the figure and 3D axis
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('X')
    ax.set_ylabel('Z')  # Swap Y and Z for more intuitive top-down view
    ax.set_zlabel('Y')
    ax.set_title('HTC Vive Controller Positions')
    
    # Initialize empty plots
    left_trail, = ax.plot([], [], [], 'b-', alpha=0.5, label='Left Controller')
    right_trail, = ax.plot([], [], [], 'r-', alpha=0.5, label='Right Controller')
    left_point, = ax.plot([], [], [], 'bo', markersize=10)
    right_point, = ax.plot([], [], [], 'ro', markersize=10)
    
    # Set axis limits
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_zlim(0, 2)
    
    # Add a legend
    ax.legend()
    
    def update_plot(frame):
        """Update function for the animation"""
        receiver.update()
        history = receiver.get_position_history()
        
        # Update left controller
        if history["left"]["x"]:
            left_trail.set_data(history["left"]["x"], history["left"]["z"])
            left_trail.set_3d_properties(history["left"]["y"])
            left_point.set_data([history["left"]["x"][-1]], [history["left"]["z"][-1]])
            left_point.set_3d_properties([history["left"]["y"][-1]])
        
        # Update right controller
        if history["right"]["x"]:
            right_trail.set_data(history["right"]["x"], history["right"]["z"])
            right_trail.set_3d_properties(history["right"]["y"])
            right_point.set_data([history["right"]["x"][-1]], [history["right"]["z"][-1]])
            right_point.set_3d_properties([history["right"]["y"][-1]])
        
        return left_trail, right_trail, left_point, right_point
    
    # Create animation
    ani = FuncAnimation(fig, update_plot, frames=None, interval=50, blit=True)
    
    # Show the plot
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Custom receiver for HTC Vive controller data")
    parser.add_argument("--port", type=int, default=5555, help="UDP port to listen on (default: 5555)")
    parser.add_argument("--mode", choices=["text", "plot"], default="text", 
                        help="Display mode: text or plot (default: text)")
    args = parser.parse_args()
    
    # Create receiver
    receiver = ViveDataReceiver(args.port)
    
    try:
        # Run in the selected mode
        if args.mode == "plot" and MATPLOTLIB_AVAILABLE:
            plot_mode(receiver)
        else:
            text_mode(receiver)
    finally:
        receiver.close() 