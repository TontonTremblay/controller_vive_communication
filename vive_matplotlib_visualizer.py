#!/usr/bin/env python3
"""
HTC Vive Controller Visualizer using Matplotlib

This script visualizes the position of HTC Vive controllers in real-time using Matplotlib.
It also changes the color of the controller representation when the trigger is pressed.
"""

import socket
import json
import time
import numpy as np
import threading
import argparse
import sys
import os
from collections import deque
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib.patches import FancyArrowPatch
    from mpl_toolkits.mplot3d import proj3d
except ImportError:
    print("Matplotlib is not installed. Please install it with:")
    print("pip install matplotlib")
    sys.exit(1)

# Class for 3D arrows (for coordinate frames)
class Arrow3D(FancyArrowPatch):
    def __init__(self, xs, ys, zs, *args, **kwargs):
        super().__init__((0, 0), (0, 0), *args, **kwargs)
        self._verts3d = xs, ys, zs

    def do_3d_projection(self, renderer=None):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, self.axes.M)
        self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
        return np.min(zs)

class ViveControllerVisualizer:
    def __init__(self, port=5555, max_trail_points=50, axis_limit=2.0, terminal_output=True):
        """Initialize the visualizer with the specified port"""
        self.port = port
        self.socket_lock = threading.Lock()  # Add lock for thread safety
        
        # Initialize data storage
        self.latest_data = None
        self.running = True
        self.left_trigger_pressed = False
        self.right_trigger_pressed = False
        
        # Controller positions
        self.left_position = np.array([0.0, 0.0, 0.0])
        self.right_position = np.array([0.0, 0.0, 0.0])
        
        # Controller rotations (Euler angles in degrees)
        self.left_rotation = np.array([0.0, 0.0, 0.0])
        self.right_rotation = np.array([0.0, 0.0, 0.0])
        
        # Controller button states
        self.left_buttons = {}
        self.right_buttons = {}
        
        # Controller tracking status
        self.left_tracked = False
        self.right_tracked = False
        
        # Last update time
        self.last_update_time = time.time()
        
        # Terminal output flag
        self.terminal_output = terminal_output
        self.terminal_update_interval = 0.2  # seconds
        self.last_terminal_update = 0
        
        # Trail points (history of positions)
        self.max_trail_points = max_trail_points
        self.left_trail_x = deque(maxlen=max_trail_points)
        self.left_trail_y = deque(maxlen=max_trail_points)
        self.left_trail_z = deque(maxlen=max_trail_points)
        self.right_trail_x = deque(maxlen=max_trail_points)
        self.right_trail_y = deque(maxlen=max_trail_points)
        self.right_trail_z = deque(maxlen=max_trail_points)
        
        # Axis limits
        self.axis_limit = axis_limit
        
        # Position history for auto-scaling
        self.min_x, self.max_x = 0, 0
        self.min_y, self.max_y = 0, 0
        self.min_z, self.max_z = 0, 0
        self.auto_scale = True
        
        # Socket error flag
        self.socket_error = False
        
        # Debug mode
        self.debug_mode = True  # Set to True to enable debug output
        
        # Initialize socket
        self.initialize_socket()
        
        # Start the receiver thread
        self.receiver_thread = threading.Thread(target=self.receive_data)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()
        
        # Start terminal output thread if enabled
        if self.terminal_output:
            self.terminal_thread = threading.Thread(target=self.update_terminal)
            self.terminal_thread.daemon = True
            self.terminal_thread.start()
        
        print(f"Listening for controller data on port {port}...")
        print(f"Initial axis limit set to ±{axis_limit} meters")
        print("Press 'a' to toggle auto-scaling of the axes")
        print("Press 'r' to reinitialize the socket")
        print("Press 'd' to toggle debug mode")
        print("Use arrow keys to rotate the view")
    
    def initialize_socket(self):
        """Initialize the UDP socket"""
        with self.socket_lock:
            try:
                if hasattr(self, 'sock') and self.sock:
                    try:
                        self.sock.close()
                    except:
                        pass
                
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Set socket options for reuse
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # Bind to all interfaces
                self.sock.bind(("0.0.0.0", self.port))
                self.sock.settimeout(0.1)  # Set a timeout for non-blocking operation
                self.socket_error = False
                print(f"Socket initialized on port {self.port}")
            except Exception as e:
                print(f"Error initializing socket: {e}")
                self.socket_error = True
    
    def clear_terminal(self):
        """Clear the terminal screen"""
        if sys.platform == 'win32':
            os.system('cls')
        else:
            os.system('clear')
    
    def update_terminal(self):
        """Update the terminal with controller information"""
        while self.running:
            if self.terminal_output and time.time() - self.last_terminal_update > self.terminal_update_interval:
                self.last_terminal_update = time.time()
                
                # Clear the terminal
                self.clear_terminal()
                
                # Print header
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"=== HTC Vive Controller Status - {current_time} ===")
                print(f"Socket Status: {'ERROR' if self.socket_error else 'OK'}")
                print(f"Data Last Updated: {time.time() - self.last_update_time:.1f} seconds ago")
                print("=" * 50)
                
                # Left controller
                print("\nLEFT CONTROLLER:")
                if self.left_tracked:
                    print(f"  Status: TRACKED")
                    print(f"  Position: X={self.left_position[0]:.4f}, Y={self.left_position[1]:.4f}, Z={self.left_position[2]:.4f} m")
                    print(f"  Rotation: Roll={self.left_rotation[0]:.1f}°, Pitch={self.left_rotation[1]:.1f}°, Yaw={self.left_rotation[2]:.1f}°")
                    
                    # Button states
                    print("\n  BUTTON STATES:")
                    trigger_status = "PRESSED" if self.left_trigger_pressed else "RELEASED"
                    print(f"    Trigger: {trigger_status}")
                    
                    for button, state in self.left_buttons.items():
                        if button != "trigger":  # Already displayed trigger
                            if isinstance(state, dict):
                                status = "PRESSED" if state.get("pressed", False) else ("TOUCHED" if state.get("touched", False) else "---")
                            else:
                                status = "PRESSED" if state else "---"
                            print(f"    {button.capitalize()}: {status}")
                else:
                    print("  Status: NOT TRACKED")
                
                # Right controller
                print("\nRIGHT CONTROLLER:")
                if self.right_tracked:
                    print(f"  Status: TRACKED")
                    print(f"  Position: X={self.right_position[0]:.4f}, Y={self.right_position[1]:.4f}, Z={self.right_position[2]:.4f} m")
                    print(f"  Rotation: Roll={self.right_rotation[0]:.1f}°, Pitch={self.right_rotation[1]:.1f}°, Yaw={self.right_rotation[2]:.1f}°")
                    
                    # Button states
                    print("\n  BUTTON STATES:")
                    trigger_status = "PRESSED" if self.right_trigger_pressed else "RELEASED"
                    print(f"    Trigger: {trigger_status}")
                    
                    for button, state in self.right_buttons.items():
                        if button != "trigger":  # Already displayed trigger
                            if isinstance(state, dict):
                                status = "PRESSED" if state.get("pressed", False) else ("TOUCHED" if state.get("touched", False) else "---")
                            else:
                                status = "PRESSED" if state else "---"
                            print(f"    {button.capitalize()}: {status}")
                else:
                    print("  Status: NOT TRACKED")
                
                # Controls reminder
                print("\n" + "=" * 50)
                print("CONTROLS:")
                print("  'a' - Toggle auto-scaling")
                print("  'r' - Reinitialize socket")
                print("  'd' - Toggle debug mode")
                print("  Arrow keys - Rotate view")
                print("  Press Ctrl+C to exit")
            
            # Sleep to avoid high CPU usage
            time.sleep(0.1)
    
    def receive_data(self):
        """Receive data from the UDP socket in a separate thread"""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.running:
            if self.socket_error:
                print("Socket error detected, attempting to reinitialize...")
                self.initialize_socket()
                time.sleep(1)  # Wait before trying again
                continue
                
            try:
                # Try to receive data with the lock
                with self.socket_lock:
                    if not self.sock:
                        raise Exception("Socket is not initialized")
                    data, addr = self.sock.recvfrom(4096)
                
                consecutive_errors = 0  # Reset error counter on success
                
                try:
                    # Parse JSON data
                    json_data = data.decode('utf-8')
                    self.latest_data = json.loads(json_data)
                    
                    if self.debug_mode:
                        print(f"Received data from {addr[0]}:{addr[1]}, size: {len(data)} bytes")
                        
                        # Debug: Print tracked status
                        if "left" in self.latest_data:
                            left_tracked = self.latest_data["left"].get("tracked", False)
                            print(f"Left controller tracked: {left_tracked}")
                        if "right" in self.latest_data:
                            right_tracked = self.latest_data["right"].get("tracked", False)
                            print(f"Right controller tracked: {right_tracked}")
                    
                    # Update controller positions and states
                    self.update_controller_data()
                    
                    # Update last update time
                    self.last_update_time = time.time()
                    
                except json.JSONDecodeError as e:
                    print(f"Received invalid JSON data: {e}")
                    if self.debug_mode:
                        print(f"Raw data: {data[:100]}...")  # Print first 100 chars for debugging
                        
            except socket.timeout:
                # No data available, just continue
                pass
            except Exception as e:
                consecutive_errors += 1
                print(f"Socket error ({consecutive_errors}/{max_consecutive_errors}): {e}")
                if consecutive_errors >= max_consecutive_errors:
                    print(f"Multiple consecutive errors: {e}")
                    print("Attempting to reinitialize socket...")
                    self.socket_error = True
                    consecutive_errors = 0
                time.sleep(0.5)  # Wait a bit before retrying
    
    def update_controller_data(self):
        """Update controller positions and states from the latest data"""
        if not self.latest_data:
            return
        
        if self.debug_mode:
            # Debug: Print the entire data structure
            print(f"Latest data structure: {json.dumps(self.latest_data, indent=2)[:200]}...")
        
        # Update left controller
        if "left" in self.latest_data:
            # Get tracked status directly from the data
            self.left_tracked = self.latest_data["left"].get("tracked", False)
            
            if self.debug_mode:
                print(f"Setting left_tracked to {self.left_tracked}")
            
            # Even if not tracked, update button states if available
            if "buttons" in self.latest_data["left"]:
                self.left_buttons = self.latest_data["left"]["buttons"]
                
                # Trigger state
                if "trigger" in self.left_buttons:
                    if isinstance(self.left_buttons["trigger"], bool):
                        self.left_trigger_pressed = self.left_buttons["trigger"]
                    elif isinstance(self.left_buttons["trigger"], dict):
                        self.left_trigger_pressed = self.left_buttons["trigger"].get("pressed", False)
                
            # Update position and rotation only if tracked
            if self.left_tracked:
                # Position
                if "position" in self.latest_data["left"]:
                    pos = self.latest_data["left"]["position"]
                    if all(k in pos for k in ["x", "y", "z"]):
                        self.left_position = np.array([pos["x"], pos["y"], pos["z"]])
                        
                        if self.debug_mode:
                            print(f"Updated left position: {self.left_position}")
                        
                        # Add to trail
                        self.left_trail_x.append(pos["x"])
                        self.left_trail_y.append(pos["y"])
                        self.left_trail_z.append(pos["z"])
                        
                        # Update min/max for auto-scaling
                        self.min_x = min(self.min_x, pos["x"])
                        self.max_x = max(self.max_x, pos["x"])
                        self.min_y = min(self.min_y, pos["y"])
                        self.max_y = max(self.max_y, pos["y"])
                        self.min_z = min(self.min_z, pos["z"])
                        self.max_z = max(self.max_z, pos["z"])
                
                # Rotation
                if "rotation" in self.latest_data["left"]:
                    rot = self.latest_data["left"]["rotation"]
                    if all(k in rot for k in ["roll", "pitch", "yaw"]):
                        self.left_rotation = np.array([rot["roll"], rot["pitch"], rot["yaw"]])
                
                # Alternative way to check trigger
                if "analog" in self.latest_data["left"] and "trigger" in self.latest_data["left"]["analog"]:
                    self.left_trigger_pressed = self.latest_data["left"]["analog"]["trigger"] > 0.5
        
        # Update right controller
        if "right" in self.latest_data:
            # Get tracked status directly from the data
            self.right_tracked = self.latest_data["right"].get("tracked", False)
            
            if self.debug_mode:
                print(f"Setting right_tracked to {self.right_tracked}")
            
            # Even if not tracked, update button states if available
            if "buttons" in self.latest_data["right"]:
                self.right_buttons = self.latest_data["right"]["buttons"]
                
                # Trigger state
                if "trigger" in self.right_buttons:
                    if isinstance(self.right_buttons["trigger"], bool):
                        self.right_trigger_pressed = self.right_buttons["trigger"]
                    elif isinstance(self.right_buttons["trigger"], dict):
                        self.right_trigger_pressed = self.right_buttons["trigger"].get("pressed", False)
            
            # Update position and rotation only if tracked
            if self.right_tracked:
                # Position
                if "position" in self.latest_data["right"]:
                    pos = self.latest_data["right"]["position"]
                    if all(k in pos for k in ["x", "y", "z"]):
                        self.right_position = np.array([pos["x"], pos["y"], pos["z"]])
                        
                        if self.debug_mode:
                            print(f"Updated right position: {self.right_position}")
                        
                        # Add to trail
                        self.right_trail_x.append(pos["x"])
                        self.right_trail_y.append(pos["y"])
                        self.right_trail_z.append(pos["z"])
                        
                        # Update min/max for auto-scaling
                        self.min_x = min(self.min_x, pos["x"])
                        self.max_x = max(self.max_x, pos["x"])
                        self.min_y = min(self.min_y, pos["y"])
                        self.max_y = max(self.max_y, pos["y"])
                        self.min_z = min(self.min_z, pos["z"])
                        self.max_z = max(self.max_z, pos["z"])
                
                # Rotation
                if "rotation" in self.latest_data["right"]:
                    rot = self.latest_data["right"]["rotation"]
                    if all(k in rot for k in ["roll", "pitch", "yaw"]):
                        self.right_rotation = np.array([rot["roll"], rot["pitch"], rot["yaw"]])
                
                # Alternative way to check trigger
                if "analog" in self.latest_data["right"] and "trigger" in self.latest_data["right"]["analog"]:
                    self.right_trigger_pressed = self.latest_data["right"]["analog"]["trigger"] > 0.5
    
    def euler_to_rotation_matrix(self, euler_angles):
        """Convert Euler angles (in degrees) to rotation matrix"""
        # Convert to radians
        roll, pitch, yaw = np.radians(euler_angles)
        
        # Roll (rotation around X-axis)
        R_x = np.array([
            [1, 0, 0],
            [0, np.cos(roll), -np.sin(roll)],
            [0, np.sin(roll), np.cos(roll)]
        ])
        
        # Pitch (rotation around Y-axis)
        R_y = np.array([
            [np.cos(pitch), 0, np.sin(pitch)],
            [0, 1, 0],
            [-np.sin(pitch), 0, np.cos(pitch)]
        ])
        
        # Yaw (rotation around Z-axis)
        R_z = np.array([
            [np.cos(yaw), -np.sin(yaw), 0],
            [np.sin(yaw), np.cos(yaw), 0],
            [0, 0, 1]
        ])
        
        # Combined rotation matrix
        R = np.dot(R_z, np.dot(R_y, R_x))
        
        return R
    
    def create_coordinate_frame(self, ax, position, rotation, scale=0.1):
        """Create a coordinate frame at the given position with the given rotation"""
        # Get rotation matrix
        R = self.euler_to_rotation_matrix(rotation)
        
        # Create arrows for each axis
        x_axis = np.array([scale, 0, 0])
        y_axis = np.array([0, scale, 0])
        z_axis = np.array([0, 0, scale])
        
        # Apply rotation
        x_axis = np.dot(R, x_axis)
        y_axis = np.dot(R, y_axis)
        z_axis = np.dot(R, z_axis)
        
        # Create arrows
        x_arrow = Arrow3D([position[0], position[0] + x_axis[0]],
                          [position[1], position[1] + x_axis[1]],
                          [position[2], position[2] + x_axis[2]],
                          mutation_scale=10, lw=2, arrowstyle='-|>', color='r')
        
        y_arrow = Arrow3D([position[0], position[0] + y_axis[0]],
                          [position[1], position[1] + y_axis[1]],
                          [position[2], position[2] + y_axis[2]],
                          mutation_scale=10, lw=2, arrowstyle='-|>', color='g')
        
        z_arrow = Arrow3D([position[0], position[0] + z_axis[0]],
                          [position[1], position[1] + z_axis[1]],
                          [position[2], position[2] + z_axis[2]],
                          mutation_scale=10, lw=2, arrowstyle='-|>', color='b')
        
        # Add arrows to the plot
        ax.add_artist(x_arrow)
        ax.add_artist(y_arrow)
        ax.add_artist(z_arrow)
    
    def update_plot(self, frame, ax, left_controller, right_controller, 
                   left_trail, right_trail, title_text, info_text):
        """Update function for the animation"""
        # Clear the axis for redrawing
        ax.clear()
        
        # Set axis labels and limits
        ax.set_xlabel('X (meters)')
        ax.set_ylabel('Z (meters)')  # Swap Y and Z for more intuitive view
        ax.set_zlabel('Y (meters)')
        
        # Set axis limits
        if self.auto_scale and (self.min_x != self.max_x):
            # Add some padding to the limits
            padding = 0.2
            x_range = max(0.5, self.max_x - self.min_x)
            y_range = max(0.5, self.max_y - self.min_y)
            z_range = max(0.5, self.max_z - self.min_z)
            
            # Center the plot on the data
            x_center = (self.min_x + self.max_x) / 2
            y_center = (self.min_y + self.max_y) / 2
            z_center = (self.min_z + self.max_z) / 2
            
            # Set limits with padding
            ax.set_xlim(x_center - x_range/2 - padding, x_center + x_range/2 + padding)
            ax.set_zlim(y_center - y_range/2 - padding, y_center + y_range/2 + padding)
            ax.set_ylim(z_center - z_range/2 - padding, z_center + z_range/2 + padding)
        else:
            # Use fixed limits
            ax.set_xlim(-self.axis_limit, self.axis_limit)
            ax.set_ylim(-self.axis_limit, self.axis_limit)
            ax.set_zlim(0, self.axis_limit * 2)
        
        # Set title with controller status
        left_status = "TRACKED" if self.left_tracked else "NOT TRACKED"
        right_status = "TRACKED" if self.right_tracked else "NOT TRACKED"
        if self.left_tracked and self.left_trigger_pressed:
            left_status += " (TRIGGER PRESSED)"
        if self.right_tracked and self.right_trigger_pressed:
            right_status += " (TRIGGER PRESSED)"
        title_text.set_text(f"HTC Vive Controllers - Left: {left_status}, Right: {right_status}")
        
        # Update info text
        scaling_mode = "AUTO" if self.auto_scale else "FIXED"
        socket_status = "ERROR" if self.socket_error else "OK"
        data_age = time.time() - self.last_update_time
        info_text.set_text(f"Scaling: {scaling_mode} | Socket: {socket_status} | Data Age: {data_age:.1f}s | Debug: {'ON' if self.debug_mode else 'OFF'}")
        
        # Draw ground plane grid
        grid_size = self.axis_limit
        x = np.linspace(-grid_size, grid_size, 11)
        z = np.linspace(-grid_size, grid_size, 11)
        X, Z = np.meshgrid(x, z)
        Y = np.zeros_like(X)
        ax.plot_wireframe(X, Z, Y, color='gray', alpha=0.3)
        
        # Draw left controller
        left_color = 'green' if self.left_trigger_pressed else 'blue'
        if self.left_tracked:
            ax.scatter(self.left_position[0], self.left_position[2], self.left_position[1], 
                      color=left_color, s=100, label='Left Controller')
            
            # Draw trails
            if len(self.left_trail_x) > 1:
                ax.plot(list(self.left_trail_x), list(self.left_trail_z), list(self.left_trail_y), 
                       'b-', alpha=0.5)
            
            # Draw coordinate frames
            self.create_coordinate_frame(ax, self.left_position, self.left_rotation)
        
        # Draw right controller
        right_color = 'green' if self.right_trigger_pressed else 'red'
        if self.right_tracked:
            ax.scatter(self.right_position[0], self.right_position[2], self.right_position[1], 
                      color=right_color, s=100, label='Right Controller')
            
            # Draw trails
            if len(self.right_trail_x) > 1:
                ax.plot(list(self.right_trail_x), list(self.right_trail_z), list(self.right_trail_y), 
                       'r-', alpha=0.5)
            
            # Draw coordinate frames
            self.create_coordinate_frame(ax, self.right_position, self.right_rotation)
        
        # Add legend
        ax.legend()
        
        return ax,
    
    def on_key_press(self, event):
        """Handle key press events"""
        if event.key == 'a':
            # Toggle auto-scaling
            self.auto_scale = not self.auto_scale
            print(f"Auto-scaling: {'ON' if self.auto_scale else 'OFF'}")
        elif event.key == 'r':
            # Reinitialize socket
            print("Manually reinitializing socket...")
            self.socket_error = True
        elif event.key == 't':
            # Toggle terminal output
            self.terminal_output = not self.terminal_output
            print(f"Terminal output: {'ON' if self.terminal_output else 'OFF'}")
        elif event.key == 'd':
            # Toggle debug mode
            self.debug_mode = not self.debug_mode
            print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
    
    def run_visualization(self):
        """Run the matplotlib visualization"""
        # Create figure and 3D axis
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Create title text
        title_text = fig.suptitle("HTC Vive Controllers", fontsize=16)
        
        # Create info text
        info_text = fig.text(0.02, 0.02, "", fontsize=10)
        
        # Connect key press event
        fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # Create empty scatter plots for controllers
        left_controller = ax.scatter([], [], [], color='blue', s=100)
        right_controller = ax.scatter([], [], [], color='red', s=100)
        
        # Create empty line plots for trails
        left_trail, = ax.plot([], [], [], 'b-', alpha=0.5)
        right_trail, = ax.plot([], [], [], 'r-', alpha=0.5)
        
        # Set up the animation
        ani = FuncAnimation(fig, self.update_plot, 
                           fargs=(ax, left_controller, right_controller, 
                                 left_trail, right_trail, title_text, info_text),
                           interval=50, blit=False)
        
        # Show the plot
        plt.show()
        
        # Clean up when the window is closed
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up resources...")
        self.running = False
        time.sleep(0.2)  # Give threads time to notice the running flag
        
        # Close socket with lock
        with self.socket_lock:
            if hasattr(self, 'sock') and self.sock:
                try:
                    self.sock.close()
                    self.sock = None
                except:
                    pass
        
        print("Cleanup complete")

def main():
    parser = argparse.ArgumentParser(description="Visualize HTC Vive controller data using Matplotlib")
    parser.add_argument("--port", type=int, default=5555, help="UDP port to listen on (default: 5555)")
    parser.add_argument("--trail-length", type=int, default=50, help="Length of the motion trail (default: 50)")
    parser.add_argument("--axis-limit", type=float, default=2.0, help="Initial axis limit in meters (default: 2.0)")
    parser.add_argument("--no-terminal", action="store_true", help="Disable terminal output")
    args = parser.parse_args()
    
    try:
        visualizer = ViveControllerVisualizer(
            args.port, 
            args.trail_length, 
            args.axis_limit,
            terminal_output=not args.no_terminal
        )
        visualizer.run_visualization()
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Exiting application")

if __name__ == "__main__":
    main() 