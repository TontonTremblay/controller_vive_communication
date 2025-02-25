import openvr
import time
import sys
import math
import numpy as np
import socket
import json
import argparse

def get_pose_matrix(pose):
    """Convert OpenVR pose to a 4x4 numpy matrix"""
    return np.array([
        [pose.mDeviceToAbsoluteTracking[0][0], pose.mDeviceToAbsoluteTracking[0][1], pose.mDeviceToAbsoluteTracking[0][2], pose.mDeviceToAbsoluteTracking[0][3]],
        [pose.mDeviceToAbsoluteTracking[1][0], pose.mDeviceToAbsoluteTracking[1][1], pose.mDeviceToAbsoluteTracking[1][2], pose.mDeviceToAbsoluteTracking[1][3]],
        [pose.mDeviceToAbsoluteTracking[2][0], pose.mDeviceToAbsoluteTracking[2][1], pose.mDeviceToAbsoluteTracking[2][2], pose.mDeviceToAbsoluteTracking[2][3]],
        [0.0, 0.0, 0.0, 1.0]
    ])

def extract_rotation_euler(matrix):
    """Extract Euler angles (in degrees) from a rotation matrix"""
    # Convert rotation matrix to Euler angles (roll, pitch, yaw)
    # This is a simplified version and might not handle all edge cases
    pitch = math.atan2(-matrix[2][0], math.sqrt(matrix[0][0]**2 + matrix[1][0]**2))
    yaw = math.atan2(matrix[1][0], matrix[0][0])
    roll = math.atan2(matrix[2][1], matrix[2][2])
    
    # Convert to degrees
    return (
        math.degrees(roll),
        math.degrees(pitch),
        math.degrees(yaw)
    )

def get_button_names():
    """Return a dictionary mapping button IDs to their names"""
    return {
        openvr.k_EButton_System: "System",
        openvr.k_EButton_ApplicationMenu: "Menu",
        openvr.k_EButton_Grip: "Grip",
        openvr.k_EButton_DPad_Left: "Trackpad Left",
        openvr.k_EButton_DPad_Up: "Trackpad Up",
        openvr.k_EButton_DPad_Right: "Trackpad Right",
        openvr.k_EButton_DPad_Down: "Trackpad Down",
        openvr.k_EButton_A: "A Button",
        openvr.k_EButton_SteamVR_Touchpad: "Trackpad Touch",
        openvr.k_EButton_SteamVR_Trigger: "Trigger"
    }

def get_controller_info(target_ip=None, target_port=None):
    """Initialize OpenVR and get information about the HTC Vive controllers."""
    try:
        # Initialize OpenVR
        openvr.init(openvr.VRApplication_Other)
        
        # Set up UDP socket if target IP and port are provided
        udp_socket = None
        if target_ip and target_port:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print(f"\nSending controller data to {target_ip}:{target_port}")
        
        print("\n=== HTC Vive Controller Tracker ===")
        print("Press Ctrl+C to exit.")
        print("-----------------------------------")
        
        # Get the tracking system
        vr_system = openvr.VRSystem()
        
        # Get button names
        button_names = get_button_names()
        
        # Dictionary to store controller indices
        controllers = {"left": None, "right": None}
        
        # First, identify the controllers
        for i in range(openvr.k_unMaxTrackedDeviceCount):
            device_class = vr_system.getTrackedDeviceClass(i)
            if device_class == openvr.TrackedDeviceClass_Controller:
                # Get controller role
                role = vr_system.getControllerRoleForTrackedDeviceIndex(i)
                if role == openvr.TrackedControllerRole_LeftHand:
                    controllers["left"] = i
                elif role == openvr.TrackedControllerRole_RightHand:
                    controllers["right"] = i
        
        print(f"Found controllers: Left: {'Yes' if controllers['left'] is not None else 'No'}, "
              f"Right: {'Yes' if controllers['right'] is not None else 'No'}")
        print("-----------------------------------")
        
        try:
            while True:
                # Clear previous output (Windows)
                if sys.platform == 'win32':
                    _ = system('cls')
                else:
                    _ = system('clear')
                
                print("\n=== HTC Vive Controller Tracker ===")
                print(f"Time: {time.strftime('%H:%M:%S')}")
                if target_ip and target_port:
                    print(f"Sending data to: {target_ip}:{target_port}")
                print("-----------------------------------")
                
                # Dictionary to store all controller data for network transmission
                controller_data = {}
                
                # Get controller data
                for hand, device_idx in controllers.items():
                    if device_idx is not None:
                        # Get the device pose
                        poses = vr_system.getDeviceToAbsoluteTrackingPose(
                            openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount)
                        pose = poses[device_idx]
                        
                        # Initialize data dictionary for this controller
                        controller_data[hand] = {
                            "tracked": False,
                            "position": {},
                            "rotation": {},
                            "buttons": {},
                            "analog": {}
                        }
                        
                        if pose.bPoseIsValid:
                            # Get position
                            pos_x = pose.mDeviceToAbsoluteTracking[0][3]
                            pos_y = pose.mDeviceToAbsoluteTracking[1][3]
                            pos_z = pose.mDeviceToAbsoluteTracking[2][3]
                            
                            # Get rotation
                            matrix = get_pose_matrix(pose)
                            roll, pitch, yaw = extract_rotation_euler(matrix)
                            
                            # Get controller state (buttons, etc.)
                            result, state = vr_system.getControllerState(device_idx)
                            
                            # Store data for network transmission
                            controller_data[hand]["tracked"] = True
                            controller_data[hand]["position"] = {"x": pos_x, "y": pos_y, "z": pos_z}
                            controller_data[hand]["rotation"] = {"roll": roll, "pitch": pitch, "yaw": yaw}
                            
                            # Print controller info
                            print(f"\n{hand.upper()} CONTROLLER:")
                            print(f"  Position: X={pos_x:.4f}, Y={pos_y:.4f}, Z={pos_z:.4f} (meters)")
                            print(f"  Rotation: Roll={roll:.1f}°, Pitch={pitch:.1f}°, Yaw={yaw:.1f}°")
                            
                            # Display button states
                            if result:
                                print("\n  BUTTON STATES:")
                                
                                # Display raw button values for debugging
                                print(f"    Raw Button Pressed: {state.ulButtonPressed}")
                                print(f"    Raw Button Touched: {state.ulButtonTouched}")
                                
                                # Store raw button states for network transmission
                                controller_data[hand]["raw_buttons"] = {
                                    "pressed": state.ulButtonPressed,
                                    "touched": state.ulButtonTouched
                                }
                                
                                # Method 1: Check specific buttons directly
                                print("\n  MAIN BUTTONS:")
                                
                                # System button (typically the power button)
                                system_pressed = (state.ulButtonPressed & (1 << openvr.k_EButton_System)) != 0
                                print(f"    System Button: {'PRESSED' if system_pressed else '---'}")
                                controller_data[hand]["buttons"]["system"] = system_pressed
                                
                                # Menu button
                                menu_pressed = (state.ulButtonPressed & (1 << openvr.k_EButton_ApplicationMenu)) != 0
                                print(f"    Menu Button: {'PRESSED' if menu_pressed else '---'}")
                                controller_data[hand]["buttons"]["menu"] = menu_pressed
                                
                                # Grip button
                                grip_pressed = (state.ulButtonPressed & (1 << openvr.k_EButton_Grip)) != 0
                                print(f"    Grip Button: {'PRESSED' if grip_pressed else '---'}")
                                controller_data[hand]["buttons"]["grip"] = grip_pressed
                                
                                # Trigger button
                                trigger_pressed = (state.ulButtonPressed & (1 << openvr.k_EButton_SteamVR_Trigger)) != 0
                                print(f"    Trigger Button: {'PRESSED' if trigger_pressed else '---'}")
                                controller_data[hand]["buttons"]["trigger"] = trigger_pressed
                                
                                # Trackpad touch
                                trackpad_touched = (state.ulButtonTouched & (1 << openvr.k_EButton_SteamVR_Touchpad)) != 0
                                trackpad_pressed = (state.ulButtonPressed & (1 << openvr.k_EButton_SteamVR_Touchpad)) != 0
                                trackpad_status = "PRESSED" if trackpad_pressed else ("TOUCHED" if trackpad_touched else "---")
                                print(f"    Trackpad: {trackpad_status}")
                                controller_data[hand]["buttons"]["trackpad"] = {
                                    "pressed": trackpad_pressed,
                                    "touched": trackpad_touched
                                }
                                
                                # Method 2: Loop through all buttons (alternative approach)
                                print("\n  ALL BUTTONS:")
                                for button_id, button_name in button_names.items():
                                    try:
                                        # Check if the button is pressed
                                        is_pressed = (state.ulButtonPressed & (1 << button_id)) != 0
                                        # Check if the button is touched
                                        is_touched = (state.ulButtonTouched & (1 << button_id)) != 0
                                        
                                        status = "PRESSED" if is_pressed else ("TOUCHED" if is_touched else "---")
                                        print(f"    {button_name}: {status}")
                                        
                                        # Store button state for network transmission
                                        button_key = button_name.lower().replace(" ", "_")
                                        controller_data[hand]["buttons"][button_key] = {
                                            "pressed": is_pressed,
                                            "touched": is_touched
                                        }
                                    except Exception as e:
                                        print(f"    Error checking {button_name}: {e}")
                                
                                # Display analog inputs
                                print("\n  ANALOG INPUTS:")
                                # Trigger
                                trigger_value = state.rAxis[1].x if len(state.rAxis) > 1 else 0.0
                                print(f"    Trigger: {trigger_value:.2f}")
                                controller_data[hand]["analog"]["trigger"] = trigger_value
                                
                                # Trackpad/Thumbstick
                                if len(state.rAxis) > 0:
                                    trackpad_x = state.rAxis[0].x
                                    trackpad_y = state.rAxis[0].y
                                    print(f"    Trackpad: X={trackpad_x:.2f}, Y={trackpad_y:.2f}")
                                    controller_data[hand]["analog"]["trackpad"] = {
                                        "x": trackpad_x,
                                        "y": trackpad_y
                                    }
                                else:
                                    print("    Trackpad: Not available")
                            
                            # Check if controller is being tracked
                            print(f"\n  Tracking: {'OK' if pose.bDeviceIsConnected else 'Not Connected'}")
                        else:
                            print(f"\n{hand.upper()} CONTROLLER: Not tracked")
                    else:
                        print(f"\n{hand.upper()} CONTROLLER: Not detected")
                
                # Send controller data over UDP if socket is configured
                if udp_socket and target_ip and target_port:
                    try:
                        # Add timestamp to the data
                        controller_data["timestamp"] = time.time()
                        
                        # Convert data to JSON and send
                        json_data = json.dumps(controller_data)
                        udp_socket.sendto(json_data.encode(), (target_ip, target_port))
                        print(f"\nData sent to {target_ip}:{target_port}")
                    except Exception as e:
                        print(f"\nError sending data: {e}")
                
                print("\nPress Ctrl+C to exit.")
                
                # Sleep to avoid flooding the console and network
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nExiting...")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Close socket if it was opened
        if udp_socket:
            udp_socket.close()
        
        # Shutdown OpenVR
        openvr.shutdown()

def create_receiver_script():
    """Create a receiver script for the Linux machine"""
    receiver_code = '''#!/usr/bin/env python3
import socket
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
                print("\\033c", end="")
                
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
                elif display_mode == "raw":
                    print(json.dumps(controller_data, indent=2))
                
            except json.JSONDecodeError:
                print(f"Received invalid data from {addr}")
            
    except KeyboardInterrupt:
        print("\\nExiting...")
    finally:
        sock.close()

def display_simple(data):
    """Display simplified controller data"""
    for hand in ["left", "right"]:
        if hand in data:
            controller = data[hand]
            if controller.get("tracked", False):
                print(f"\\n{hand.upper()} CONTROLLER:")
                
                # Position
                pos = controller.get("position", {})
                if pos:
                    print(f"  Position: X={pos.get('x', 0):.4f}, Y={pos.get('y', 0):.4f}, Z={pos.get('z', 0):.4f}")
                
                # Main buttons
                buttons = controller.get("buttons", {})
                print("\\n  MAIN BUTTONS:")
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
                    print("\\n  ANALOG INPUTS:")
                    if "trigger" in analog:
                        print(f"    Trigger: {analog['trigger']:.2f}")
                    if "trackpad" in analog:
                        trackpad = analog["trackpad"]
                        print(f"    Trackpad: X={trackpad.get('x', 0):.2f}, Y={trackpad.get('y', 0):.2f}")
            else:
                print(f"\\n{hand.upper()} CONTROLLER: Not tracked")

def display_full(data):
    """Display detailed controller data"""
    for hand in ["left", "right"]:
        if hand in data:
            controller = data[hand]
            if controller.get("tracked", False):
                print(f"\\n{hand.upper()} CONTROLLER:")
                
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
                    print("\\n  ALL BUTTONS:")
                    for btn_name, btn_state in buttons.items():
                        if isinstance(btn_state, dict):
                            status = "PRESSED" if btn_state.get("pressed", False) else ("TOUCHED" if btn_state.get("touched", False) else "---")
                        else:
                            status = "PRESSED" if btn_state else "---"
                        print(f"    {btn_name.replace('_', ' ').capitalize()}: {status}")
                
                # Analog inputs
                analog = controller.get("analog", {})
                if analog:
                    print("\\n  ANALOG INPUTS:")
                    for input_name, input_value in analog.items():
                        if isinstance(input_value, dict):
                            print(f"    {input_name.capitalize()}: X={input_value.get('x', 0):.2f}, Y={input_value.get('y', 0):.2f}")
                        else:
                            print(f"    {input_name.capitalize()}: {input_value:.2f}")
            else:
                print(f"\\n{hand.upper()} CONTROLLER: Not tracked")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Receive HTC Vive controller data")
    parser.add_argument("--port", type=int, default=5555, help="UDP port to listen on (default: 5555)")
    parser.add_argument("--mode", choices=["simple", "full", "raw"], default="simple", 
                        help="Display mode: simple, full, or raw JSON (default: simple)")
    args = parser.parse_args()
    
    receive_controller_data(args.port, args.mode)
'''
    
    # Write the receiver script to a file
    with open("vive_receiver.py", "w") as f:
        f.write(receiver_code)
    
    print("\nCreated receiver script: vive_receiver.py")
    print("Copy this file to your Linux machine and run it with: python3 vive_receiver.py")
    print("Optional arguments:")
    print("  --port PORT    UDP port to listen on (default: 5555)")
    print("  --mode MODE    Display mode: simple, full, or raw (default: simple)")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Track and send HTC Vive controller data")
    parser.add_argument("--ip", type=str, help="IP address of the target Linux machine")
    parser.add_argument("--port", type=int, default=5555, help="UDP port on the target machine (default: 5555)")
    parser.add_argument("--create-receiver", action="store_true", help="Create a receiver script for the Linux machine")
    args = parser.parse_args()
    
    if args.create_receiver:
        create_receiver_script()
    else:
        # Import system for clearing the screen
        from os import system
        get_controller_info(args.ip, args.port)