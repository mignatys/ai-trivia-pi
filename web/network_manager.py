"""
network_manager.py
------------------
Handles WiFi connectivity for the Pi, switching between client mode and
acting as a temporary hotspot for configuration. Uses nmcli for modern
Raspberry Pi OS compatibility.
"""

import subprocess
import time
from logger import log

HOTSPOT_SSID = "MIG_Labs"
HOTSPOT_PASSWORD = "password"

def _run_command(command, check=True):
    """Executes a shell command and returns its output."""
    try:
        log.debug(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=check,
            timeout=120  # Increased timeout for network operations
        )
        log.debug(f"Command successful. Output: {result.stdout.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed: {' '.join(command)}")
        log.error(f"Stderr: {e.stderr.strip()}")
        return None
    except subprocess.TimeoutExpired:
        log.error(f"Command timed out: {' '.join(command)}")
        return None

def is_connected():
    """Checks if the Pi is connected to any WiFi network."""
    log.info("Checking for active WiFi connection...")
    # Use `nmcli g` for a simpler, more reliable status check
    output = _run_command(['nmcli', '-t', '-f', 'STATE', 'g'])
    if output == "connected":
        log.info("WiFi is connected.")
        return True
    log.info("WiFi is not connected.")
    return False

def get_current_ssid():
    """Gets the SSID of the currently connected WiFi network."""
    output = _run_command(['nmcli', '-t', '-f', 'NAME,TYPE', 'c', 'show', '--active'])
    if output:
        for line in output.splitlines():
            if 'wifi' in line:
                return line.split(':')[0].strip()
    return None

def start_hotspot():
    """Starts a temporary WiFi hotspot for configuration."""
    log.info(f"Attempting to start hotspot with SSID: {HOTSPOT_SSID}")
    
    # Disconnect from any existing network
    _run_command(['nmcli', 'd', 'disconnect', 'wlan0'], check=False)
    time.sleep(2)

    # Use the direct hotspot command
    command = [
        'nmcli', 'd', 'wifi', 'hotspot', 'ifname', 'wlan0',
        'ssid', HOTSPOT_SSID, 'password', HOTSPOT_PASSWORD
    ]
    if _run_command(command) is not None:
        log.info("Hotspot started successfully.")
        return True
    
    log.error("Failed to start hotspot.")
    return False

def connect_to_wifi(ssid, password):
    """Attempts to connect to a new WiFi network with verification."""
    log.info(f"Attempting to connect to SSID: {ssid}")
    
    # Disconnect from any current network (including a potential hotspot)
    _run_command(['nmcli', 'd', 'disconnect', 'wlan0'], check=False)
    time.sleep(2)

    # Use the direct connect command
    connect_command = [
        'nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password
    ]
    
    if _run_command(connect_command) is None:
        log.error(f"Failed to connect to '{ssid}'. The network may be out of range or the password may be incorrect.")
        return False

    # Verify connection status for a few seconds
    for _ in range(5):
        time.sleep(2)
        if is_connected():
            log.info(f"Successfully connected to '{ssid}'.")
            return True
            
    log.error(f"Failed to verify connection to '{ssid}' after connecting.")
    return False
