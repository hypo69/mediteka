# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Port and Process Management
# =============================================================================
# Description:
#   Utilities for checking and freeing ports before server startup
#
# Examples:
#   >>> from src.utils.port_manager import kill_port_process
#   >>> kill_port_process(8000)
#
# File: port_manager.py
# Project: Ai Assistant (Docker)
# Version: 0.4.0
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: December 9, 2025
# =============================================================================

import subprocess
import sys
import time
import os

def kill_port_process(port: int) -> bool:
    """Kills the process occupying the specified port"""
    try:
        if sys.platform == "win32":
            # Windows
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True, capture_output=True, text=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5 and f':{port}' in parts[1]:
                        pid = parts[-1]
                        print(f"Killing process PID {pid} on port {port}")
                        subprocess.run(f'taskkill /f /pid {pid}', shell=True)
                        time.sleep(1)
                        return True
        else:
            # Linux/macOS
            result = subprocess.run(
                f'lsof -ti:{port}',
                shell=True, capture_output=True, text=True
            )
            if result.stdout:
                pid = result.stdout.strip()
                print(f"Killing process PID {pid} on port {port}")
                subprocess.run(f'kill -9 {pid}', shell=True)
                time.sleep(1)
                return True
        return False
    except Exception as e:
        print(f"Error freeing port {port}: {e}")
        return False

def is_port_free(port: int) -> bool:
    """Checks if a port is free"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True, capture_output=True, text=True
            )
            return not result.stdout.strip()
        else:
            result = subprocess.run(
                f'lsof -ti:{port}',
                shell=True, capture_output=True, text=True
            )
            return not result.stdout.strip()
    except Exception:
        return True

def ensure_port_free(port: int) -> bool:
    """Ensures the port is free"""
    if is_port_free(port):
        return True
    
    print(f"Port {port} is occupied, freeing...")
    return kill_port_process(port)