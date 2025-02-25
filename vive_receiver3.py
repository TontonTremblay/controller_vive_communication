#!/usr/bin/env python3
import socket
import open3d as o3d
import numpy as np
import json
import argparse
import time

def receive_controller_data(port=5555, display_mode="simple"):
    
    """Receive and display controller data from the Windows machine"""
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    print(f"Listening for controller data on port {port}...")
    
    try:
        while True:
            # Receive data
            data, addr = sock.recvfrom(4096)
            
            try:
                # Parse JSON data
                controller_data = json.loads(data.decode())
                
                # Clear terminal
                print("\033c", end="")
                
                # Print header
                print(f"=== HTC Vive Controller Data ===")
                print(f"From: {addr[0]}:{addr[1]}")
                print(f"Time: {time.strftime('%H:%M:%S')}")
                print("-------------------------------")
                
                # Display data based on mode
                if display_mode == "simple":
                    display_simple(controller_data)
                elif display_mode == "full":
                    display_full(controller_data)
                elif display_mode == "3d":
                    display_3d(controller_data)
                elif display_mode == "raw":
                    print(json.dumps(controller_data, indent=2))
                
            except json.JSONDecodeError:
                print(f"Received invalid data from {addr}")
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        sock.close()

def display_simple(data):
    """Display simplified controller data"""
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
                print("\n  MAIN BUTTONS:")
                for btn in ["system", "menu", "grip", "trigger"]:
                    if btn in buttons:
                        status = "PRESSED" if buttons[btn] else "---"
                        print(f"    {btn.capitalize()}: {status}")
                
                # Trackpad
                if "trackpad" in buttons:
                    trackpad = buttons["trackpad"]
                    status = "PRESSED" if trackpad.get("pressed", False) else ("TOUCHED" if trackpad.get("touched", False) else "---")
                    print(f"    Trackpad: {status}")
                
                # Analog inputs
                analog = controller.get("analog", {})
                if analog:
                    print("\n  ANALOG INPUTS:")
                    if "trigger" in analog:
                        print(f"    Trigger: {analog['trigger']:.2f}")
                    if "trackpad" in analog:
                        trackpad = analog["trackpad"]
                        print(f"    Trackpad: X={trackpad.get('x', 0):.2f}, Y={trackpad.get('y', 0):.2f}")
            else:
                print(f"\n{hand.upper()} CONTROLLER: Not tracked")

def display_full(data):
    """Display detailed controller data"""
    for hand in ["left", "right"]:
        if hand in data:
            controller = data[hand]
            if controller.get("tracked", False):
                print(f"\n{hand.upper()} CONTROLLER:")
                
                # Position
                pos = controller.get("position", {})
                if pos:
                    print(f"  Position: X={pos.get('x', 0):.4f}, Y={pos.get('y', 0):.4f}, Z={pos.get('z', 0):.4f}")
                
                # Rotation
                rot = controller.get("rotation", {})
                if rot:
                    print(f"  Rotation: Roll={rot.get('roll', 0):.1f}°, Pitch={rot.get('pitch', 0):.1f}°, Yaw={rot.get('yaw', 0):.1f}°")
                
                # All buttons
                buttons = controller.get("buttons", {})
                if buttons:
                    print("\n  ALL BUTTONS:")
                    for btn_name, btn_state in buttons.items():
                        if isinstance(btn_state, dict):
                            status = "PRESSED" if btn_state.get("pressed", False) else ("TOUCHED" if btn_state.get("touched", False) else "---")
                        else:
                            status = "PRESSED" if btn_state else "---"
                        print(f"    {btn_name.replace('_', ' ').capitalize()}: {status}")
                
                # Analog inputs
                analog = controller.get("analog", {})
                if analog:
                    print("\n  ANALOG INPUTS:")
                    for input_name, input_value in analog.items():
                        if isinstance(input_value, dict):
                            print(f"    {input_name.capitalize()}: X={input_value.get('x', 0):.2f}, Y={input_value.get('y', 0):.2f}")
                        else:
                            print(f"    {input_name.capitalize()}: {input_value:.2f}")
            else:
                print(f"\n{hand.upper()} CONTROLLER: Not tracked")

def display_3d(data):
    """Display 3D position and orientation of the controller"""
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    mesh_sphere = o3d.geometry.TriangleMesh.create_sphere(radius=0.05)
    mesh_sphere.paint_uniform_color([0.1, 0.1, 0.7])
    vis.add_geometry(mesh_sphere)

    for hand in ["left", "right"]:
        if hand in data:
            controller = data[hand]
            if controller.get("tracked", False):
                pos = controller.get("position", {})
                rot = controller.get("rotation", {})
                if pos and rot:
                    # Set position
                    mesh_sphere.translate([pos.get('x', 0), pos.get('y', 0), pos.get('z', 0)], relative=False)
                    
                    # Set orientation
                    R = o3d.geometry.get_rotation_matrix_from_xyz(
                        [np.radians(rot.get('roll', 0)), np.radians(rot.get('pitch', 0)), np.radians(rot.get('yaw', 0))]
                    )
                    mesh_sphere.rotate(R, center=mesh_sphere.get_center())
                    
                    vis.update_geometry(mesh_sphere)
                    vis.poll_events()
                    vis.update_renderer()
                    time.sleep(0.1)

    vis.destroy_window()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Receive HTC Vive controller data")
    parser.add_argument("--port", type=int, default=5555, help="UDP port to listen on (default: 5555)")
    parser.add_argument("--mode", choices=["simple", "full", "raw", "3d"], default="simple", 
                        help="Display mode: simple, full, raw JSON, or 3D visualization (default: simple)")
    args = parser.parse_args()
    
    receive_controller_data(args.port, args.mode)
