#!/usr/bin/env python3
"""
Port Checker and Terminal Launcher
Helps find available ports and launch the terminal properly
"""

import socket
import subprocess
import sys
import os

def check_port(host, port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False

def find_available_port(host='localhost', start_port=5000):
    """Find the first available port starting from start_port"""
    test_ports = [start_port, 5001, 8000, 8001, 8080, 8888, 9000, 3000, 4000]
    
    for port in test_ports:
        if check_port(host, port):
            return port
    
    return None

def get_process_using_port(port):
    """Get the process using a specific port (Windows)"""
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    # Get process name
                    try:
                        tasklist = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                                capture_output=True, text=True)
                        for task_line in tasklist.stdout.split('\n'):
                            if pid in task_line:
                                process_name = task_line.split()[0]
                                return f"PID {pid} ({process_name})"
                    except:
                        return f"PID {pid}"
        return "Unknown"
    except:
        return "Unable to determine"

def main():
    print("Python Terminal - Port Checker and Launcher")
    print("=" * 50)
    
    # Check commonly used ports
    common_ports = [5000, 8000, 8080, 8888]
    print("Checking common ports:")
    
    available_ports = []
    for port in common_ports:
        if check_port('localhost', port):
            print(f"✅ Port {port}: Available")
            available_ports.append(port)
        else:
            process = get_process_using_port(port)
            print(f"❌ Port {port}: In use by {process}")
    
    if not available_ports:
        print("\n⚠️  No common ports available. Finding alternative...")
        alt_port = find_available_port()
        if alt_port:
            print(f"✅ Found available port: {alt_port}")
            available_ports.append(alt_port)
    
    print("\n" + "=" * 50)
    print("Launch Options:")
    print("1. CLI Mode (Command Line)")
    print("2. CLI Mode with AI")
    if available_ports:
        print(f"3. Web Interface (port {available_ports[0]})")
        print(f"4. Web Interface with AI (port {available_ports[0]})")
    else:
        print("3. Web Interface (no ports available)")
        print("4. Web Interface with AI (no ports available)")
    print("5. Run tests")
    print("6. Check system requirements")
    print("0. Exit")
    
    while True:
        try:
            choice = input("\nSelect option (0-6): ").strip()
            
            if choice == '0':
                print("Goodbye!")
                break
            elif choice == '1':
                print("Starting CLI Mode...")
                subprocess.run([sys.executable, 'main.py'])
                break
            elif choice == '2':
                print("Starting CLI Mode with AI...")
                subprocess.run([sys.executable, 'main.py', '--ai'])
                break
            elif choice == '3':
                if available_ports:
                    print(f"Starting Web Interface on port {available_ports[0]}...")
                    subprocess.run([sys.executable, 'main.py', '--web', '--port', str(available_ports[0])])
                else:
                    print("No available ports found. Try closing other applications.")
                break
            elif choice == '4':
                if available_ports:
                    print(f"Starting Web Interface with AI on port {available_ports[0]}...")
                    subprocess.run([sys.executable, 'main.py', '--web', '--ai', '--port', str(available_ports[0])])
                else:
                    print("No available ports found. Try closing other applications.")
                break
            elif choice == '5':
                print("Running tests...")
                subprocess.run([sys.executable, 'main.py', '--test'])
                break
            elif choice == '6':
                check_requirements()
                break
            else:
                print("Invalid choice. Please select 0-6.")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")